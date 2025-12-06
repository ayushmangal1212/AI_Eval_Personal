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

# Role skills mapping
ROLE_SKILLS = {
    "Java Developer": ["Core Java", "Spring / Spring Boot", "Concurrency / Multithreading", "Maven / Gradle", "REST / Web APIs", "JPA / SQL", "Testing (JUnit)"],
    "Database Administrator": ["PostgreSQL / MySQL", "Backup & Recovery", "Replication / HA", "Performance Tuning", "Security", "Monitoring"],
    "Frontend Developer": ["HTML / CSS / JS", "React / Angular / Vue", "State Management", "Accessibility", "Responsive Design", "Testing (Jest)"],
    "DevOps Engineer": ["Docker", "Kubernetes", "CI/CD", "Terraform / IaC", "Monitoring / Logging", "Linux / Scripting"],
    "Data Engineer": ["Python / Scala", "ETL / Data Pipelines", "Spark", "Airflow", "Data Modeling", "SQL"],
    "Python Developer": ["Core Python", "Flask / Django", "Async IO", "Testing (pytest)", "APIs", "Data Structures"],
}

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
            'eval_chances': {},
            'eval_taken_counts': {}
        }
        
        # If resume data was provided, merge it with user data
        if resume_data:
            # Only override if not provided in form
            if not user_data['name'] and resume_data.get('name'):
                user_data['name'] = resume_data.get('name', '')
            user_data['experience'] = str(resume_data.get('experience_years', 0)) + ' years'
            user_data['skills'] = resume_data.get('skills', [])
            # Update email if it was parsed and not provided
            if resume_data.get('email') and not email:
                user_data['email'] = resume_data.get('email')
        
        users[username] = user_data
        db_utils.save_users(users)
        
        # Send welcome email
        if user_data['email']:
            email_service.send_welcome_email(user_data['email'], username)
        
        return jsonify({'success': True, 'message': 'Registration successful'})
    
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

@app.route('/api/generate-questions', methods=['POST'])
@login_required
def generate_questions():
    data = request.get_json()
    role = data.get('role')
    skills = data.get('skills', [])
    language = data.get('language', 'English')
    
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
    # Skills to focus on: {', '.join(skills)}
    # Language: {language}
    # 
    # Mix of questions:
    # - Questions 1-2: Conceptual/Theoretical
    # - Question 3: Coding Challenge
    # - Question 4: Conceptual/Theoretical
    # - Question 5: Coding Challenge
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
    return jsonify({'success': True})

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

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    users = db_utils.load_users()
    history = db_utils.load_eval_history()
    feedback = db_utils.load_feedback()
    
    return render_template('admin_dashboard.html', 
                         users=users, 
                         history=history, 
                         feedback=feedback)

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


if __name__ == '__main__':
    app.run(debug=True, port=5000)
