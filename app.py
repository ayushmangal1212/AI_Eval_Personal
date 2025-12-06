from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from functools import wraps
import os
import time
import io
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import json
import re
import hashlib
from datetime import datetime
import db_utils
import logging
import csv
import httpx

# Import enhancement modules
from email_service import email_service
from resume_parser import resume_parser
from code_executor import code_executor
from analytics import AdvancedAnalytics
from proctoring import proctoring_service
import feedback_db
from chatbot_service import chatbot

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# Configuration
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-reasoner")
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Admin@123")

# Initialize LLM
client = httpx.Client(verify=False)
llm = ChatOpenAI(
    base_url=DEEPSEEK_BASE_URL,
    model=DEEPSEEK_MODEL,
    api_key=DEEPSEEK_API_KEY,
    http_client=client,
)

# Load Role skills mapping from roles.json
def get_role_skills():
    """Get role skills from db_utils (loads from roles.json) and extract just the skills for backward compatibility"""
    roles = db_utils.load_roles()
    role_skills = {}
    for role_name, role_info in roles.items():
        if isinstance(role_info, dict):
            role_skills[role_name] = role_info.get('skills', [])
        else:
            role_skills[role_name] = role_info
    return role_skills

ROLE_SKILLS = get_role_skills()

# Helper functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        fullname = data.get('fullname', '')  # Get full name from form
        password = data.get('password')
        email = data.get('email')
        experience = data.get('experience')  # Get experience from form
        resume_data = data.get('resume_data')  # Get parsed resume data
        
        users = db_utils.load_users()
        if username in users:
            return jsonify({'success': False, 'message': 'Username already exists'})
        
        # Prepare user data
        user_data = {
            'password': hash_password(password),
            'email': email,
            'created_at': datetime.now().isoformat(),
            'name': fullname,  # Use fullname from form
            'experience': '',
            'skills': [],
            
            # Evaluation attempts control
            'total_attempts_allowed': 3,  # Total attempts across all roles
            'total_attempts_used': 0,     # How many attempts used so far
            'role_attempts': {}           # Track attempts per role
        }
        
        # Handle experience field - prioritize user input over resume data
        if experience:
            user_data['experience'] = str(experience) + ' years'
        elif resume_data and resume_data.get('experience_years'):
            user_data['experience'] = str(resume_data.get('experience_years', 0)) + ' years'
        
        # If resume data was provided, merge it with user data
        if resume_data:
            # Only override if not provided in form
            if not user_data['name'] and resume_data.get('name'):
                user_data['name'] = resume_data.get('name', '')
            user_data['skills'] = resume_data.get('skills', [])
            # Update email if it was parsed and not provided
            if resume_data.get('email') and not email:
                user_data['email'] = resume_data.get('email')
        
        users[username] = user_data
        db_utils.save_users(users)
        
        return jsonify({'success': True, 'message': 'Registration successful!'})
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        users = db_utils.load_users()
        if username in users and users[username]['password'] == hash_password(password):
            session['username'] = username
            return jsonify({'success': True, 'message': 'Login successful'})
        
        return jsonify({'success': False, 'message': 'Invalid credentials'})
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    username = session.get('username')
    history = db_utils.load_eval_history()
    user_history = history.get(username, [])
    return render_template('dashboard.html', username=username, history=user_history)

@app.route('/evaluation/results/<int:eval_index>')
@login_required
def view_evaluation_results(eval_index):
    """View detailed results of a past evaluation"""
    username = session.get('username')
    history = db_utils.load_eval_history()
    user_history = history.get(username, [])
    
    if eval_index < 0 or eval_index >= len(user_history):
        return redirect(url_for('dashboard'))
    
    evaluation = user_history[eval_index]
    return render_template('evaluation_results.html', 
                         username=username, 
                         evaluation=evaluation,
                         eval_index=eval_index)

@app.route('/evaluation/new')
@login_required
def new_evaluation():
    username = session.get('username')
    users = db_utils.load_users()
    user = users.get(username, {})
    user_skills = user.get('skills', [])
    
    return render_template('evaluation.html', 
                         roles=list(ROLE_SKILLS.keys()),
                         user_skills=user_skills)

@app.route('/api/check-attempts', methods=['POST'])
@login_required
def check_attempts():
    """Check if user has attempts remaining for a role"""
    data = request.get_json()
    role = data.get('role')
    username = session.get('username')
    
    users = db_utils.load_users()
    user = users.get(username, {})
    
    # Get attempt limits
    total_allowed = user.get('total_attempts_allowed', 3)
    total_used = user.get('total_attempts_used', 0)
    role_attempts = user.get('role_attempts', {})
    
    # Check total attempts
    if total_used >= total_allowed:
        return jsonify({
            'success': False,
            'can_attempt': False,
            'message': f'You have used all {total_allowed} attempts. Contact admin for more.',
            'total_remaining': 0
        })
    
    # Check role-specific attempts
    if role in role_attempts:
        role_data = role_attempts[role]
        role_used = role_data.get('used', 0)
        role_allowed = role_data.get('allowed', 1)
        
        if role_used >= role_allowed:
            return jsonify({
                'success': False,
                'can_attempt': False,
                'message': f'You have already attempted {role}. Choose a different role.',
                'total_remaining': total_allowed - total_used
            })
    
    # User can attempt
    return jsonify({
        'success': True,
        'can_attempt': True,
        'message': 'You can take this evaluation',
        'total_remaining': total_allowed - total_used,
        'role_remaining': 1  # Always 1 per role
    })

@app.route('/api/generate-questions', methods=['POST'])
@login_required
def generate_questions():
    data = request.get_json()
    role = data.get('role')
    skills = data.get('skills', [])
    language = data.get('language', 'English')
    
    # Get user's experience level from database
    username = session.get('username')
    users = db_utils.load_users()
    user = users.get(username, {})
    experience = user.get('experience', '')
    
    # Determine experience level for question difficulty
    experience_level = "mid-level"  # default
    if experience:
        # Extract years from experience string (e.g., "5 years" -> 5)
        import re
        years_match = re.search(r'(\d+)', experience)
        if years_match:
            years = int(years_match.group(1))
            if years <= 2:
                experience_level = "entry-level"
            elif years <= 5:
                experience_level = "mid-level"
            else:
                experience_level = "senior"
    
    # ============================================
    # TOGGLE BETWEEN DUMMY AND LLM QUESTIONS
    # ============================================
    # For TESTING: Use dummy questions (fast, instant)
    # For PRODUCTION: Use LLM-generated questions (slow, dynamic)
    # 
    # To switch to LLM:
    # 1. Comment out the "DUMMY QUESTIONS" section below
    # 2. Uncomment the "LLM GENERATION" section
    # ============================================
    
    # ============================================
    # DUMMY QUESTIONS (Currently Active)
    # ============================================
    # Generate dummy questions instantly for testing
    
    # Role-specific questions
    role_questions = {
        'Python Developer': [
            {"type": "conceptual", "question": f"Explain the difference between lists and tuples in Python. When would you use each?"},
            {"type": "conceptual", "question": f"What are Python decorators and how do they work? Provide an example."},
            {"type": "coding", "question": f"Write a Python function that takes a list of numbers and returns the sum of all even numbers. Include error handling."},
            {"type": "conceptual", "question": f"Explain the concept of list comprehensions in Python. What are their advantages?"},
            {"type": "coding", "question": f"Implement a function to reverse a string without using built-in reverse methods."}
        ],
        'Java Developer': [
            {"type": "conceptual", "question": f"Explain the difference between abstract classes and interfaces in Java."},
            {"type": "conceptual", "question": f"What is the Java Collections Framework? Explain ArrayList vs LinkedList."},
            {"type": "coding", "question": f"Write a Java program to find the factorial of a number using recursion."},
            {"type": "conceptual", "question": f"Explain exception handling in Java. What is the difference between checked and unchecked exceptions?"},
            {"type": "coding", "question": f"Implement a simple Java class to represent a Bank Account with deposit and withdraw methods."}
        ],
        'Frontend Developer': [
            {"type": "conceptual", "question": f"Explain the difference between var, let, and const in JavaScript."},
            {"type": "conceptual", "question": f"What is the Virtual DOM in React? How does it improve performance?"},
            {"type": "coding", "question": f"Write a JavaScript function to debounce user input. Explain when you would use this."},
            {"type": "conceptual", "question": f"Explain CSS Flexbox and Grid. When would you use each?"},
            {"type": "coding", "question": f"Create a React component that fetches data from an API and displays it with loading and error states."}
        ],
        'DevOps Engineer': [
            {"type": "conceptual", "question": f"Explain the difference between Docker containers and virtual machines."},
            {"type": "conceptual", "question": f"What is CI/CD? Describe a typical CI/CD pipeline."},
            {"type": "coding", "question": f"Write a Dockerfile for a simple Node.js application. Explain each instruction."},
            {"type": "conceptual", "question": f"Explain Infrastructure as Code (IaC). What are the benefits of using tools like Terraform?"},
            {"type": "coding", "question": f"Write a bash script to monitor disk usage and send an alert if it exceeds 80%."}
        ],
        'Data Engineer': [
            {"type": "conceptual", "question": f"Explain the difference between OLTP and OLAP systems."},
            {"type": "conceptual", "question": f"What is data partitioning? Why is it important in big data systems?"},
            {"type": "coding", "question": f"Write a SQL query to find the top 5 customers by total purchase amount from orders table."},
            {"type": "conceptual", "question": f"Explain the concept of data lakes vs data warehouses."},
            {"type": "coding", "question": f"Write a Python script using pandas to clean a dataset: remove duplicates, handle missing values, and normalize data."}
        ],
        'Database Administrator': [
            {"type": "conceptual", "question": f"Explain database normalization. What are the different normal forms?"},
            {"type": "conceptual", "question": f"What is database indexing? How does it improve query performance?"},
            {"type": "coding", "question": f"Write SQL queries to create a table with proper constraints (primary key, foreign key, unique, not null)."},
            {"type": "conceptual", "question": f"Explain ACID properties in database transactions."},
            {"type": "coding", "question": f"Write a SQL query to find duplicate records in a table and remove them keeping only one copy."}
        ]
    }
    
    # Get questions for the selected role, or use default
    questions = role_questions.get(role, [
        {"type": "conceptual", "question": f"Explain the key concepts and best practices in {role}."},
        {"type": "conceptual", "question": f"What are the most important skills for a {role}? Explain why."},
        {"type": "coding", "question": f"Write a solution to a common problem in {role} using {skills[0] if skills else 'appropriate technology'}."},
        {"type": "conceptual", "question": f"How would you approach performance optimization in {role} projects?"},
        {"type": "coding", "question": f"Implement a feature commonly required in {role} applications."}
    ])
    
    return jsonify({'success': True, 'questions': questions})
    # ============================================
    # END DUMMY QUESTIONS
    # ============================================
    
    
    # ============================================
    # LLM GENERATION (Currently Commented Out)
    # ============================================
    # Uncomment this section to use AI-generated questions
    # Note: This will be slower (5-10 seconds) but questions will be dynamic
    
    # # Generate questions using LLM
    # prompt = f"""Generate 5 technical interview questions for a {role} position.
    # Candidate Experience Level: {experience_level} ({experience if experience else 'not specified'})
    # Skills to focus on: {', '.join(skills)}
    # Language: {language}
    # 
    # IMPORTANT: Adjust question difficulty based on experience level:
    # - Entry-level (0-2 years): Focus on fundamentals, basic concepts, simple coding tasks
    # - Mid-level (3-5 years): Intermediate concepts, practical applications, moderate complexity
    # - Senior (6+ years): Advanced topics, system design, optimization, best practices
    # 
    # Mix of questions:
    # - Questions 1-2: Conceptual/Theoretical (appropriate for {experience_level})
    # - Question 3: Coding Challenge (difficulty: {experience_level})
    # - Question 4: Conceptual/Theoretical (appropriate for {experience_level})
    # - Question 5: Coding Challenge (difficulty: {experience_level})
    # 
    # Return as JSON array with format: [{{"type": "conceptual/coding", "question": "..."}}]
    # """
    # 
    # try:
    #     response = llm.invoke(prompt)
    #     response_text = response.content.strip()
    #     
    #     # Try to extract JSON from response
    #     try:
    #         questions = json.loads(response_text)
    #     except json.JSONDecodeError:
    #         # Try to find JSON array in the response
    #         import re
    #         json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
    #         if json_match:
    #             questions = json.loads(json_match.group(0))
    #         else:
    #             # Fallback to dummy questions
    #             print(f"Warning: Could not parse LLM response. Using fallback questions.")
    #             questions = [
    #                 {"type": "conceptual", "question": f"Explain the key concepts of {skills[0] if skills else role}"},
    #                 {"type": "conceptual", "question": f"What are the best practices for {skills[1] if len(skills) > 1 else role}?"},
    #                 {"type": "coding", "question": f"Write a function to solve a common {role} problem using {skills[0] if skills else 'your preferred language'}"},
    #                 {"type": "conceptual", "question": f"How would you optimize performance in a {role} application?"},
    #                 {"type": "coding", "question": f"Implement a solution for data processing using {skills[2] if len(skills) > 2 else 'appropriate tools'}"}
    #             ]
    #     
    #     return jsonify({'success': True, 'questions': questions})
    # except Exception as e:
    #     print(f"Error in LLM generation: {str(e)}")
    #     return jsonify({'success': False, 'message': str(e)})
    # ============================================
    # END LLM GENERATION
    # ============================================


@app.route('/api/evaluate-answer', methods=['POST'])
@login_required
def evaluate_answer():
    data = request.get_json()
    question = data.get('question')
    answer = data.get('answer')
    question_type = data.get('type')
    
    # Evaluate answer using LLM
    prompt = f"""Evaluate this answer for a {question_type} question.
    
    Question: {question}
    Answer: {answer}
    
    Provide:
    1. Score (0-20)
    2. Detailed feedback
    
    Return as JSON: {{"score": X, "feedback": "..."}}
    """
    
    try:
        response = llm.invoke(prompt)
        result = json.loads(response.content)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/save-evaluation', methods=['POST'])
@login_required
def save_evaluation():
    data = request.get_json()
    username = session.get('username')
    role = data.get('role')
    
    eval_data = {
        'date': datetime.now().isoformat(),
        'role': role,
        'score': data.get('score'),
        'max_score': data.get('max_score'),
        'percentage': data.get('percentage'),
        'time_taken': data.get('time_taken'),
        'qa_history': data.get('qa_history', [])
    }
    
    # Save evaluation result
    db_utils.save_evaluation_result(username, eval_data)
    
    # UPDATE: Increment attempt counts
    users = db_utils.load_users()
    user = users.get(username, {})
    
    # Increment total attempts
    user['total_attempts_used'] = user.get('total_attempts_used', 0) + 1
    
    # Increment role-specific attempts
    if 'role_attempts' not in user:
        user['role_attempts'] = {}
    
    if role not in user['role_attempts']:
        user['role_attempts'][role] = {
            'allowed': 1,
            'used': 0,
            'last_attempt': None
        }
    
    user['role_attempts'][role]['used'] += 1
    user['role_attempts'][role]['last_attempt'] = datetime.now().isoformat()
    
    # Save updated user data
    users[username] = user
    db_utils.save_users(users)
    
    # Send detailed evaluation report email
    email_sent = False
    if user.get('email'):
        try:
            # Determine status based on percentage
            percentage = eval_data['percentage']
            if percentage >= 80:
                status = "Excellent ✅"
                recommendation = "Outstanding performance! You've demonstrated strong expertise in this area. Consider taking on more advanced challenges."
            elif percentage >= 60:
                status = "Good 👍"
                recommendation = "Good job! You have a solid understanding. Review the feedback to further strengthen your skills."
            else:
                status = "Needs Improvement ⚠️"
                recommendation = "Keep practicing! Review the detailed feedback and focus on areas that need improvement. You can do it!"
            
            # Format time taken
            time_minutes = int(eval_data['time_taken'] // 60)
            time_seconds = int(eval_data['time_taken'] % 60)
            time_taken_str = f"{time_minutes}m {time_seconds}s"
            
            # Send email
            email_result = email_service.send_evaluation_complete(
                to_email=user['email'],
                name=user.get('name', username),
                role=role,
                score=eval_data['score'],
                max_score=eval_data['max_score'],
                percentage=percentage,
                time_taken=time_taken_str,
                status=status,
                recommendation=recommendation
            )
            
            email_sent = email_result.get('success', False)
            
        except Exception as e:
            logging.error(f"Failed to send evaluation report email: {e}")
    
    return jsonify({
        'success': True, 
        'email_sent': email_sent,
        'user_email': user.get('email') if email_sent else None
    })

@app.route('/api/download-report/<eval_date>')
@login_required
def download_report(eval_date):
    """Generate and download evaluation report"""
    username = session.get('username')
    
    # Load user's evaluation history
    history = db_utils.load_evaluation_history()
    user_history = history.get(username, [])
    
    # Find the specific evaluation
    evaluation = None
    for eval_item in user_history:
        if eval_item.get('date') == eval_date:
            evaluation = eval_item
            break
    
    if not evaluation:
        return jsonify({'error': 'Evaluation not found'}), 404
    
    # Load user data
    users = db_utils.load_users()
    user = users.get(username, {})
    
    # Generate HTML report
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Evaluation Report - {username}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
            background: #f5f5f5;
            color: #333;
        }}
        .report-container {{
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #667eea;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #667eea;
            margin: 0 0 10px 0;
            font-size: 2.5em;
        }}
        .header .subtitle {{
            color: #666;
            font-size: 1.1em;
        }}
        .info-section {{
            background: #f9f9f9;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .info-row {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #e0e0e0;
        }}
        .info-row:last-child {{
            border-bottom: none;
        }}
        .info-label {{
            font-weight: 600;
            color: #555;
        }}
        .info-value {{
            color: #333;
        }}
        .score-section {{
            text-align: center;
            padding: 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 8px;
            margin: 30px 0;
        }}
        .score-value {{
            font-size: 4em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .score-label {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        .qa-section {{
            margin: 30px 0;
        }}
        .qa-item {{
            background: #f9f9f9;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #667eea;
        }}
        .question {{
            font-weight: 600;
            color: #333;
            margin-bottom: 10px;
            font-size: 1.1em;
        }}
        .answer {{
            background: white;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
            line-height: 1.6;
        }}
        .feedback {{
            background: #e8f4fd;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
            border-left: 3px solid #4facfe;
        }}
        .score-badge {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: 600;
            margin: 10px 0;
        }}
        .score-excellent {{
            background: #10b981;
            color: white;
        }}
        .score-good {{
            background: #f59e0b;
            color: white;
        }}
        .score-needs-improvement {{
            background: #ef4444;
            color: white;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #e0e0e0;
            color: #666;
        }}
        @media print {{
            body {{
                background: white;
            }}
            .report-container {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="report-container">
        <div class="header">
            <h1>🤖 AI Evaluation Report</h1>
            <p class="subtitle">Detailed Performance Analysis</p>
        </div>
        
        <div class="info-section">
            <h2 style="margin-top: 0; color: #667eea;">Candidate Information</h2>
            <div class="info-row">
                <span class="info-label">Name:</span>
                <span class="info-value">{user.get('name', username)}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Username:</span>
                <span class="info-value">{username}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Email:</span>
                <span class="info-value">{user.get('email', 'N/A')}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Role:</span>
                <span class="info-value">{evaluation.get('role', 'N/A')}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Date:</span>
                <span class="info-value">{evaluation.get('date', '').split('T')[0]}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Time Taken:</span>
                <span class="info-value">{evaluation.get('time_taken', 'N/A')}</span>
            </div>
        </div>
        
        <div class="score-section">
            <div class="score-label">Overall Score</div>
            <div class="score-value">{evaluation.get('percentage', 0):.1f}%</div>
            <div class="score-label">{evaluation.get('score', 0)} / {evaluation.get('max_score', 0)} points</div>
            <div style="margin-top: 15px;">
                {'<span class="score-badge score-excellent">Excellent Performance</span>' if evaluation.get('percentage', 0) >= 80 else '<span class="score-badge score-good">Good Performance</span>' if evaluation.get('percentage', 0) >= 60 else '<span class="score-badge score-needs-improvement">Needs Improvement</span>'}
            </div>
        </div>
        
        <div class="qa-section">
            <h2 style="color: #667eea;">Question & Answer Details</h2>
            {''.join([f'''
            <div class="qa-item">
                <div class="question">Q{i+1}: {qa.get('question', 'N/A')}</div>
                <div class="answer">
                    <strong>Your Answer:</strong><br>
                    {qa.get('answer', 'No answer provided')}
                </div>
                <div class="feedback">
                    <strong>AI Feedback:</strong><br>
                    {qa.get('feedback', 'No feedback available')}
                </div>
                <div style="margin-top: 10px;">
                    <strong>Score:</strong> {qa.get('score', 0)}/10
                </div>
            </div>
            ''' for i, qa in enumerate(evaluation.get('qa_history', []))])}
        </div>
        
        <div class="footer">
            <p><strong>AI-Powered Evaluation System</strong></p>
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p style="font-size: 0.9em; color: #999;">This is an automated evaluation report. For questions, contact your administrator.</p>
        </div>
    </div>
</body>
</html>
    """
    
    # Create a BytesIO object to store the HTML
    buffer = io.BytesIO()
    buffer.write(html_content.encode('utf-8'))
    buffer.seek(0)
    
    # Generate filename
    filename = f"evaluation_report_{username}_{eval_date.split('T')[0]}.html"
    
    return send_file(
        buffer,
        mimetype='text/html',
        as_attachment=True,
        download_name=filename
    )

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            return jsonify({'success': True})
        
        return jsonify({'success': False, 'message': 'Invalid credentials'})
    
    return render_template('admin_login.html')

@app.route('/api/admin/download-users-data')
@admin_required
def download_users_data():
    """Download all users data as CSV/Excel file"""
    users = db_utils.load_users()
    all_history = db_utils.load_evaluation_history()
    
    # Create CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Username',
        'Full Name',
        'Email',
        'Created At',
        'Experience (Years)',
        'Total Evaluations',
        'Total Attempts Used',
        'Total Attempts Allowed',
        'Average Score (%)',
        'Highest Score (%)',
        'Roles Evaluated',
        'Last Evaluation Date'
    ])
    
    # Write user data
    for username, user_data in users.items():
        # Skip admin user
        if username == ADMIN_USERNAME:
            continue
            
        # Get user's evaluation history
        user_evals = all_history.get(username, [])
        
        # Calculate statistics
        total_evals = len(user_evals)
        avg_score = sum(e.get('percentage', 0) for e in user_evals) / total_evals if total_evals > 0 else 0
        highest_score = max((e.get('percentage', 0) for e in user_evals), default=0)
        roles = ', '.join(set(e.get('role', 'N/A') for e in user_evals)) if user_evals else 'None'
        last_eval_date = max((e.get('date', '') for e in user_evals), default='Never')
        
        writer.writerow([
            username,
            user_data.get('name', 'N/A'),
            user_data.get('email', 'N/A'),
            user_data.get('created_at', 'N/A'),
            user_data.get('experience', 'N/A'),
            total_evals,
            user_data.get('total_attempts_used', 0),
            user_data.get('total_attempts_allowed', 3),
            f"{avg_score:.1f}",
            f"{highest_score:.1f}",
            roles,
            last_eval_date.split('T')[0] if 'T' in last_eval_date else last_eval_date
        ])
    
    # Create BytesIO object
    output.seek(0)
    buffer = io.BytesIO()
    buffer.write(output.getvalue().encode('utf-8-sig'))  # UTF-8 with BOM for Excel
    buffer.seek(0)
    
    # Generate filename with timestamp
    filename = f"users_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return send_file(
        buffer,
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename,
        attachment_filename=filename  # For older Flask versions
    )

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    users = db_utils.load_users()
    all_history = db_utils.load_eval_history()
    all_feedback = db_utils.load_feedback()
    
    # Get only the 10 most recent attempts across all users
    recent_attempts = []
    for username, evaluations in all_history.items():
        for eval_data in evaluations:
            eval_data['username'] = username  # Add username to each evaluation
            recent_attempts.append(eval_data)
    
    # Sort by date (most recent first) and take only 10
    recent_attempts.sort(key=lambda x: x.get('date', ''), reverse=True)
    recent_history = recent_attempts[:10]
    
    # Get pending (unresolved) feedback
    pending_feedback = []
    for username, feedback_list in all_feedback.items():
        for feedback_item in feedback_list:
            if not feedback_item.get('resolved', False):
                feedback_item['username'] = username
                pending_feedback.append(feedback_item)
    
    # Sort pending feedback by date (most recent first)
    pending_feedback.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    return render_template('admin_dashboard.html', 
                         users=users, 
                         history=all_history,  # Full history for user stats
                         recent_history=recent_history,  # Only 10 most recent
                         feedback=all_feedback,  # All feedback
                         pending_feedback=pending_feedback,  # Only unresolved feedback
                         admin_view=True,
                         roles=db_utils.load_roles())

# ============================================
# ROLE MANAGEMENT ROUTES
# ============================================

@app.route('/api/admin/roles', methods=['GET'])
@admin_required
def get_roles():
    """Get all available roles"""
    roles = db_utils.load_roles()
    return jsonify({'success': True, 'roles': roles})

@app.route('/api/admin/roles/add', methods=['POST'])
@admin_required
def add_role():
    """Add a new role"""
    data = request.get_json()
    role_name = data.get('role_name', '').strip()
    skills = data.get('skills', [])
    default_attempts = data.get('default_attempts', 3)
    
    if not role_name:
        return jsonify({'success': False, 'error': 'Role name is required'})
    
    if not skills or not isinstance(skills, list):
        return jsonify({'success': False, 'error': 'Skills list is required'})
    
    result = db_utils.add_role(role_name, skills, default_attempts)
    
    # Reload ROLE_SKILLS globally
    global ROLE_SKILLS
    ROLE_SKILLS = get_role_skills()
    
    return jsonify(result)

@app.route('/api/admin/roles/<role_name>', methods=['DELETE'])
@admin_required
def delete_role(role_name):
    """Remove a role"""
    result = db_utils.remove_role(role_name)
    
    # Reload ROLE_SKILLS globally
    global ROLE_SKILLS
    ROLE_SKILLS = get_role_skills()
    
    return jsonify(result)

@app.route('/api/admin/roles/<role_name>', methods=['PUT'])
@admin_required
def update_role_skills(role_name):
    """Update skills and/or default attempts for a role"""
    data = request.get_json()
    skills = data.get('skills', None)
    default_attempts = data.get('default_attempts', None)
    
    if skills is not None and (not skills or not isinstance(skills, list)):
        return jsonify({'success': False, 'error': 'Skills list is required'})
    
    result = db_utils.update_role(role_name, skills=skills, default_attempts=default_attempts)
    
    # Reload ROLE_SKILLS globally
    global ROLE_SKILLS
    ROLE_SKILLS = get_role_skills()
    
    return jsonify(result)

# ============================================
# USER ROLE ATTEMPTS MANAGEMENT
# ============================================

@app.route('/api/admin/user/<username>/role-attempts', methods=['GET'])
@admin_required
def get_user_role_attempts(username):
    """Get role attempt limits for a specific user"""
    users = db_utils.load_users()
    if username not in users:
        return jsonify({'success': False, 'error': 'User not found'})
    
    user = users[username]
    eval_chances = user.get('eval_chances', {})
    
    # Get all roles and their default/user attempts
    roles = db_utils.load_roles()
    attempts_info = {}
    
    for role_name, role_info in roles.items():
        default_attempts = role_info.get('default_attempts', 3) if isinstance(role_info, dict) else 3
        user_attempts = eval_chances.get(role_name, default_attempts)
        attempts_info[role_name] = {
            'default_attempts': default_attempts,
            'user_attempts': user_attempts,
            'is_custom': role_name in eval_chances
        }
    
    return jsonify({'success': True, 'username': username, 'attempts': attempts_info})

@app.route('/api/admin/user/<username>/role-attempts/<role_name>', methods=['PUT'])
@admin_required
def set_user_role_attempts(username, role_name):
    """Set role attempt limit for a specific user"""
    data = request.get_json()
    attempts = data.get('attempts')
    
    if attempts is None or not isinstance(attempts, int):
        return jsonify({'success': False, 'error': 'Attempts must be an integer'})
    
    result = db_utils.set_user_role_attempts(username, role_name, attempts)
    return jsonify(result)

@app.route('/api/admin/user/<username>/role-attempts/<role_name>', methods=['DELETE'])
@admin_required
def reset_user_role_attempts(username, role_name):
    """Reset user role attempt limit to default"""
    try:
        users = db_utils.load_users()
        if username not in users:
            return jsonify({'success': False, 'error': 'User not found'})
        
        user = users[username]
        eval_chances = user.get('eval_chances', {})
        
        if role_name in eval_chances:
            del eval_chances[role_name]
            user['eval_chances'] = eval_chances
            users[username] = user
            db_utils.save_users(users)
            return jsonify({'success': True, 'message': f'Reset {role_name} attempts for {username} to default'})
        
        return jsonify({'success': True, 'message': 'Already using default attempts'})
    except Exception as e:
        logging.error(f"Error resetting role attempts: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/roles/<role_name>/default-attempts', methods=['PUT'])
@admin_required
def update_role_default_attempts(role_name):
    """Update default attempts for a role (applies to all new users)"""
    data = request.get_json()
    default_attempts = data.get('default_attempts')
    
    if default_attempts is None or not isinstance(default_attempts, int):
        return jsonify({'success': False, 'error': 'Default attempts must be an integer'})
    
    if default_attempts < 0:
        return jsonify({'success': False, 'error': 'Default attempts must be >= 0'})
    
    result = db_utils.update_role(role_name, default_attempts=default_attempts)
    
    # Reload ROLE_SKILLS globally
    global ROLE_SKILLS
    ROLE_SKILLS = get_role_skills()
    
    return jsonify(result)

# ============================================
# ENHANCEMENT ROUTES
# ============================================

# Email Service Routes
@app.route('/api/send-email', methods=['POST'])
@login_required
def send_email():
    """Send email notification"""
    data = request.get_json()
    email_type = data.get('type', 'welcome')
    to_email = data.get('to_email')
    
    if email_type == 'welcome':
        result = email_service.send_welcome_email(to_email, data.get('name', 'User'))
    elif email_type == 'evaluation_complete':
        result = email_service.send_evaluation_complete(
            to_email=to_email,
            name=data.get('name'),
            role=data.get('role'),
            score=data.get('score'),
            max_score=data.get('max_score'),
            percentage=data.get('percentage'),
            time_taken=data.get('time_taken'),
            status=data.get('status'),
            recommendation=data.get('recommendation')
        )
    else:
        result = {'success': False, 'message': 'Unknown email type'}
    
    return jsonify(result)

@app.route('/api/email-logs')
@admin_required
def get_email_logs():
    """Get email logs (admin only)"""
    logs = email_service.get_sent_emails(limit=50)
    return jsonify({'success': True, 'emails': logs})

# Resume Parsing Routes
@app.route('/api/parse-resume', methods=['POST'])
def parse_resume():
    """Parse uploaded resume - No login required for registration"""
    if 'resume' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'})
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
    
    try:
        file_bytes = file.read()
        parsed_data = resume_parser.parse_file(file_bytes, file.filename)
        
        return jsonify({
            'success': True,
            'data': parsed_data
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Code Execution Routes
@app.route('/api/execute-code', methods=['POST'])
@login_required
def execute_code():
    """Execute code with test cases"""
    data = request.get_json()
    code = data.get('code', '')
    test_cases = data.get('test_cases', [])
    
    try:
        result = code_executor.execute_with_tests(code, test_cases)
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/validate-code', methods=['POST'])
@login_required
def validate_code():
    """Validate code syntax"""
    data = request.get_json()
    code = data.get('code', '')
    language = data.get('language', 'python')
    
    try:
        validation = code_executor.validate_syntax(code, language)
        return jsonify({
            'success': True,
            'validation': validation
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Analytics Routes
@app.route('/api/analytics/overview')
@admin_required
def analytics_overview():
    """Get analytics overview"""
    users = db_utils.load_users()
    history = db_utils.load_eval_history()
    
    analytics = AdvancedAnalytics(history, users)
    overview = analytics.get_overview_stats()
    
    return jsonify({'success': True, 'data': overview})

@app.route('/api/analytics/report')
@admin_required
def analytics_report():
    """Get comprehensive analytics report"""
    users = db_utils.load_users()
    history = db_utils.load_eval_history()
    
    analytics = AdvancedAnalytics(history, users)
    report = analytics.generate_report()
    
    return jsonify({'success': True, 'report': report})

@app.route('/api/analytics/role-distribution')
@admin_required
def analytics_role_distribution():
    """Get role distribution analytics"""
    users = db_utils.load_users()
    history = db_utils.load_eval_history()
    
    analytics = AdvancedAnalytics(history, users)
    distribution = analytics.get_role_distribution()
    
    return jsonify({'success': True, 'data': distribution})

@app.route('/api/analytics/top-performers')
@admin_required
def analytics_top_performers():
    """Get top performers"""
    users = db_utils.load_users()
    history = db_utils.load_eval_history()
    
    analytics = AdvancedAnalytics(history, users)
    top_performers = analytics.get_top_performers(10)
    
    return jsonify({'success': True, 'data': top_performers})

# Proctoring Routes
@app.route('/api/proctoring/start', methods=['POST'])
@login_required
def start_proctoring():
    """Start proctoring session"""
    data = request.get_json()
    username = session.get('username')
    evaluation_id = data.get('evaluation_id', 'eval_' + str(int(time.time())))
    
    result = proctoring_service.start_session(username, evaluation_id)
    return jsonify(result)

@app.route('/api/proctoring/log-violation', methods=['POST'])
@login_required
def log_violation():
    """Log a proctoring violation"""
    data = request.get_json()
    session_id = data.get('session_id')
    violation_type = data.get('type')
    details = data.get('details', '')
    
    result = proctoring_service.log_violation(session_id, violation_type, details)
    return jsonify(result)

@app.route('/api/proctoring/end', methods=['POST'])
@login_required
def end_proctoring():
    """End proctoring session"""
    data = request.get_json()
    session_id = data.get('session_id')
    
    result = proctoring_service.end_session(session_id)
    return jsonify(result)

@app.route('/api/proctoring/status/<session_id>')
@login_required
def proctoring_status(session_id):
    """Get proctoring session status"""
    result = proctoring_service.get_session_status(session_id)
    return jsonify(result)

@app.route('/api/proctoring/report/<session_id>')
@admin_required
def proctoring_report(session_id):
    """Get proctoring report (admin only)"""
    result = proctoring_service.generate_proctoring_report(session_id)
    return jsonify(result)

# Enhanced Registration with Email
@app.route('/register-enhanced', methods=['POST'])
def register_enhanced():
    """Enhanced registration with email notification"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    
    users = db_utils.load_users()
    if username in users:
        return jsonify({'success': False, 'message': 'Username already exists'})
    
    users[username] = {
        'password': hash_password(password),
        'email': email,
        'created_at': datetime.now().isoformat()
    }
    db_utils.save_users(users)
    
    # Send welcome email
    email_service.send_welcome_email(email, username)
    
    return jsonify({'success': True, 'message': 'Registration successful! Welcome email sent.'})

# Enhanced Save Evaluation with Email
@app.route('/api/save-evaluation-enhanced', methods=['POST'])
@login_required
def save_evaluation_enhanced():
    """Save evaluation with email notification"""
    data = request.get_json()
    username = session.get('username')
    
    eval_data = {
        'date': datetime.now().isoformat(),
        'role': data.get('role'),
        'score': data.get('score'),
        'max_score': data.get('max_score'),
        'percentage': data.get('percentage'),
        'time_taken': data.get('time_taken'),
        'qa_history': data.get('qa_history', [])
    }
    
    db_utils.save_evaluation_result(username, eval_data)
    
    # Send completion email
    users = db_utils.load_users()
    user_email = users.get(username, {}).get('email', '')
    
    if user_email:
        percentage = eval_data['percentage']
        status = 'Excellent' if percentage >= 80 else ('Good' if percentage >= 60 else 'Needs Improvement')
        recommendation = 'Great job!' if percentage >= 80 else 'Keep practicing!'
        
        email_service.send_evaluation_complete(
            to_email=user_email,
            name=username,
            role=eval_data['role'],
            score=eval_data['score'],
            max_score=eval_data['max_score'],
            percentage=percentage,
            time_taken=eval_data['time_taken'],
            status=status,
            recommendation=recommendation
        )
    
    return jsonify({'success': True, 'email_sent': bool(user_email)})


# ============================================
# FEEDBACK ROUTES
# ============================================

@app.route('/api/submit-feedback', methods=['POST'])
@login_required
def submit_feedback():
    """Submit feedback on AI evaluation"""
    data = request.get_json()
    username = session.get('username')
    
    feedback_data = {
        'user_id': session.get('user_id', username),
        'username': username,
        'question_id': data.get('question_id'),
        'question_text': data.get('question_text'),
        'user_answer': data.get('user_answer'),
        'ai_score': data.get('ai_score'),
        'ai_feedback': data.get('ai_feedback'),
        'user_feedback': data.get('user_feedback'),
        'user_expected_score': data.get('user_expected_score')
    }
    
    result = feedback_db.save_feedback(feedback_data)
    return jsonify(result)

@app.route('/api/get-feedback')
@login_required
def get_user_feedback_api():
    """Get feedback submitted by current user"""
    username = session.get('username')
    result = feedback_db.get_user_feedback(username)
    return jsonify(result)

@app.route('/api/admin/feedback')
@admin_required
def get_all_feedback_api():
    """Get all feedback (admin only)"""
    limit = request.args.get('limit', 100, type=int)
    result = feedback_db.get_all_feedback(limit)
    return jsonify(result)

@app.route('/api/admin/feedback/stats')
@admin_required
def get_feedback_stats_api():
    """Get feedback statistics (admin only)"""
    result = feedback_db.get_feedback_stats()
    return jsonify(result)

@app.route('/api/admin/feedback/<int:feedback_id>/status', methods=['PUT'])
@admin_required
def update_feedback_status_api(feedback_id):
    """Update feedback status (admin only)"""
    data = request.get_json()
    status = data.get('status', 'reviewed')
    result = feedback_db.update_feedback_status(feedback_id, status)
    return jsonify(result)



# ============================================
# ADMIN CONTROL ENDPOINTS
# ============================================

@app.route('/api/admin/user/<username>/profile')
@admin_required
def get_user_profile_api(username):
    """Get user profile"""
    profile = db_utils.admin_get_user_profile(username)
    if profile:
        return jsonify({'success': True, 'profile': profile})
    return jsonify({'success': False, 'error': 'User not found'})

@app.route('/api/admin/user/<username>/reset-attempts', methods=['POST'])
@admin_required
def reset_user_attempts_api(username):
    """Reset user's evaluation attempts"""
    result = db_utils.admin_reset_user_attempts(username)
    return jsonify(result)

@app.route('/api/admin/user/<username>/update-skills', methods=['POST'])
@admin_required
def update_user_skills_api(username):
    """Update user skills"""
    data = request.get_json()
    skills = data.get('skills', [])
    result = db_utils.admin_update_user_skills(username, skills)
    return jsonify(result)

@app.route('/api/admin/user/<username>/evaluations')
@admin_required
def get_user_evaluations_api(username):
    """Get all evaluations for a user"""
    evaluations = db_utils.admin_get_user_evaluations(username)
    return jsonify({'success': True, 'evaluations': evaluations})

@app.route('/api/admin/evaluation/<int:eval_id>/update-score', methods=['POST'])
@admin_required
def update_evaluation_score_api(eval_id):
    """Update evaluation score"""
    data = request.get_json()
    new_score = data.get('new_score')
    new_max_score = data.get('new_max_score')
    result = db_utils.admin_update_evaluation_score(eval_id, new_score, new_max_score)
    return jsonify(result)

@app.route('/api/admin/evaluation/<int:eval_id>/update-question', methods=['POST'])
@admin_required
def update_question_score_api(eval_id):
    """Update individual question score"""
    data = request.get_json()
    question_index = data.get('question_index')
    new_score = data.get('new_score')
    result = db_utils.admin_update_question_score(eval_id, question_index, new_score)
    return jsonify(result)

@app.route('/api/admin/evaluation/<int:eval_id>/delete', methods=['DELETE'])
@admin_required
def delete_evaluation_api(eval_id):
    """Delete evaluation"""
    result = db_utils.admin_delete_evaluation(eval_id)
    return jsonify(result)

@app.route('/api/admin/users/summary')
@admin_required
def get_users_summary_api():
    """Get summary of all users"""
    users = db_utils.admin_get_all_users_summary()
    return jsonify({'success': True, 'users': users})

@app.route('/api/admin/feedback/<int:feedback_id>/adjust-score', methods=['POST'])
@admin_required
def adjust_score_from_feedback_api(feedback_id):
    """Adjust score based on feedback review"""
    data = request.get_json()
    eval_id = data.get('eval_id')
    question_index = data.get('question_index')
    new_score = data.get('new_score')
    
    # Update question score
    result = db_utils.admin_update_question_score(eval_id, question_index, new_score)
    
    if result['success']:
        # Mark feedback as reviewed
        feedback_db.update_feedback_status(feedback_id, 'resolved')
    
    return jsonify(result)

# ============================================
# ADMIN: Manage User Evaluation Attempts
# ============================================

@app.route('/api/admin/user-attempts/<username>', methods=['GET'])
@admin_required
def get_user_attempts(username):
    """Get attempt details for a specific user"""
    users = db_utils.load_users()
    user = users.get(username)
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})
    
    return jsonify({
        'success': True,
        'username': username,
        'total_attempts_allowed': user.get('total_attempts_allowed', 3),
        'total_attempts_used': user.get('total_attempts_used', 0),
        'role_attempts': user.get('role_attempts', {})
    })

@app.route('/api/admin/update-attempts', methods=['POST'])
@admin_required
def update_user_attempts():
    """Admin can increase/decrease user attempts"""
    data = request.get_json()
    username = data.get('username')
    action = data.get('action')  # 'increase_total', 'decrease_total', 'reset_role', 'reset_all'
    role = data.get('role', None)
    amount = data.get('amount', 1)
    
    users = db_utils.load_users()
    user = users.get(username)
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})
    
    if action == 'increase_total':
        user['total_attempts_allowed'] = user.get('total_attempts_allowed', 3) + amount
        message = f'Increased total attempts by {amount}'
        
    elif action == 'decrease_total':
        current = user.get('total_attempts_allowed', 3)
        new_total = max(0, current - amount)
        user['total_attempts_allowed'] = new_total
        message = f'Decreased total attempts by {amount}'
        
    elif action == 'reset_role' and role:
        if 'role_attempts' not in user:
            user['role_attempts'] = {}
        
        if role in user['role_attempts']:
            # Reset role attempts
            old_used = user['role_attempts'][role].get('used', 0)
            user['role_attempts'][role]['used'] = 0
            user['role_attempts'][role]['last_attempt'] = None
            
            # Decrease total used count
            user['total_attempts_used'] = max(0, user.get('total_attempts_used', 0) - old_used)
            
            message = f'Reset attempts for {role}'
        else:
            message = f'No attempts found for {role}'
            
    elif action == 'reset_all':
        user['total_attempts_used'] = 0
        user['role_attempts'] = {}
        message = 'Reset all attempts'
        
    else:
        return jsonify({'success': False, 'message': 'Invalid action'})
    
    # Save updated user
    users[username] = user
    db_utils.save_users(users)
    
    return jsonify({
        'success': True,
        'message': message,
        'total_attempts_allowed': user.get('total_attempts_allowed', 3),
        'total_attempts_used': user.get('total_attempts_used', 0)
    })

# ============================================
# ADMIN: Manage Feedback
# ============================================

@app.route('/api/admin/feedback/resolve', methods=['POST'])
@admin_required
def resolve_feedback():
    """Admin resolves feedback with a comment"""
    data = request.get_json()
    username = data.get('username')
    feedback_date = data.get('date')
    admin_comment = data.get('admin_comment', '')
    
    all_feedback = db_utils.load_feedback()
    
    if username not in all_feedback:
        return jsonify({'success': False, 'message': 'User feedback not found'})
    
    # Find and update the specific feedback
    updated = False
    for feedback_item in all_feedback[username]:
        if feedback_item.get('date') == feedback_date:
            feedback_item['resolved'] = True
            feedback_item['admin_comment'] = admin_comment
            updated = True
            break
    
    if updated:
        db_utils.save_feedback(all_feedback)
        return jsonify({
            'success': True,
            'message': 'Feedback resolved successfully'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Feedback not found'
        })

@app.route('/api/admin/feedback/close', methods=['POST'])
@admin_required
def close_feedback():
    """Admin closes/dismisses feedback without action"""
    data = request.get_json()
    username = data.get('username')
    feedback_date = data.get('date')
    
    all_feedback = db_utils.load_feedback()
    
    if username not in all_feedback:
        return jsonify({'success': False, 'message': 'User feedback not found'})
    
    # Find and mark as resolved (closed)
    updated = False
    for feedback_item in all_feedback[username]:
        if feedback_item.get('date') == feedback_date:
            feedback_item['resolved'] = True
            feedback_item['admin_comment'] = 'Closed without action'
            updated = True
            break
    
    if updated:
        db_utils.save_feedback(all_feedback)
        return jsonify({
            'success': True,
            'message': 'Feedback closed successfully'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Feedback not found'
        })


# ========================================
# SUPPORT CHAT & TICKETING SYSTEM
# ========================================

@app.route('/api/chat/message', methods=['POST'])
@login_required
def chat_message():
    """Handle chat message and get AI response"""
    try:
        data = request.get_json()
        user_message = data.get('message')
        conversation_history = data.get('history', [])
        username = session.get('username')
        
        if not user_message:
            return jsonify({'success': False, 'error': 'Message is required'})
        
        # Get AI response
        response = chatbot.get_response(user_message, username, conversation_history)
        
        return jsonify({
            'success': True,
            'response': response
        })
        
    except Exception as e:
        logging.error(f"Error in chat message: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/chat/create-ticket', methods=['POST'])
@login_required
def create_support_ticket():
    """Create a support ticket from chat conversation"""
    try:
        data = request.get_json()
        conversation_history = data.get('history', [])
        category = data.get('category', 'general')
        priority = data.get('priority', 'medium')
        username = session.get('username')
        
        # Generate subject from conversation
        subject = chatbot.generate_ticket_subject(conversation_history)
        
        # Create ticket
        result = db_utils.create_ticket(username, subject, category, priority)
        
        if result['success']:
            ticket_id = result['ticket_id']
            
            # Add conversation messages to ticket
            for msg in conversation_history:
                sender = username if msg['role'] == 'user' else 'bot'
                db_utils.add_ticket_message(ticket_id, sender, msg['content'])
            
            return jsonify({
                'success': True,
                'ticket_id': ticket_id,
                'message': f'Support ticket {ticket_id} created successfully!'
            })
        else:
            return jsonify({'success': False, 'error': result.get('error', 'Failed to create ticket')})
            
    except Exception as e:
        logging.error(f"Error creating support ticket: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/chat/my-tickets')
@login_required
def get_my_tickets():
    """Get current user's support tickets"""
    try:
        username = session.get('username')
        tickets = db_utils.get_user_tickets(username)
        
        return jsonify({
            'success': True,
            'tickets': tickets
        })
        
    except Exception as e:
        logging.error(f"Error getting user tickets: {e}")
        return jsonify({'success': False, 'error': str(e)})

# Admin ticket endpoints
@app.route('/api/admin/tickets')
@admin_required
def get_all_tickets():
    """Get all support tickets (admin only)"""
    try:
        status = request.args.get('status')
        tickets = db_utils.load_tickets(status=status)
        stats = db_utils.get_ticket_stats()
        
        return jsonify({
            'success': True,
            'tickets': tickets,
            'stats': stats
        })
        
    except Exception as e:
        logging.error(f"Error getting all tickets: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/ticket/<ticket_id>')
@admin_required
def get_ticket_details(ticket_id):
    """Get ticket details with full conversation (admin only)"""
    try:
        ticket = db_utils.get_ticket_by_id(ticket_id)
        
        if not ticket:
            return jsonify({'success': False, 'error': 'Ticket not found'}), 404
        
        messages = db_utils.load_ticket_messages(ticket_id)
        
        return jsonify({
            'success': True,
            'ticket': ticket,
            'messages': messages
        })
        
    except Exception as e:
        logging.error(f"Error getting ticket details: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/ticket/<ticket_id>/update', methods=['POST'])
@admin_required
def update_ticket(ticket_id):
    """Update ticket status and add admin notes (admin only)"""
    try:
        data = request.get_json()
        status = data.get('status')
        admin_notes = data.get('admin_notes')
        admin_username = session.get('admin_username', 'admin')
        
        if not status:
            return jsonify({'success': False, 'error': 'Status is required'})
        
        # Update ticket
        success = db_utils.update_ticket_status(ticket_id, status, admin_notes, admin_username)
        
        if success:
            # If admin added a note, add it as a message
            if admin_notes:
                db_utils.add_ticket_message(ticket_id, 'admin', f"Admin note: {admin_notes}")
            
            return jsonify({
                'success': True,
                'message': f'Ticket updated to {status}'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to update ticket'})
            
    except Exception as e:
        logging.error(f"Error updating ticket: {e}")
        return jsonify({'success': False, 'error': str(e)})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
