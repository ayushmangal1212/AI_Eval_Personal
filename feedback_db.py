"""
Feedback Database Utilities
Manages user feedback on AI evaluations
"""

import sqlite3
import json
from datetime import datetime

DB_PATH = 'evaluation_feedback.db'

def init_feedback_db():
    """Initialize the feedback database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create feedback table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            username TEXT NOT NULL,
            question_id TEXT NOT NULL,
            question_text TEXT NOT NULL,
            user_answer TEXT NOT NULL,
            ai_score INTEGER NOT NULL,
            ai_feedback TEXT NOT NULL,
            user_feedback TEXT NOT NULL,
            user_expected_score INTEGER,
            submitted_at TEXT NOT NULL,
            status TEXT DEFAULT 'pending'
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Feedback database initialized successfully")

def save_feedback(feedback_data):
    """
    Save user feedback to database
    
    Args:
        feedback_data (dict): Feedback information
            - user_id: User identifier
            - username: Username
            - question_id: Question identifier
            - question_text: The question that was asked
            - user_answer: User's answer
            - ai_score: Score given by AI
            - ai_feedback: Feedback given by AI
            - user_feedback: User's feedback/complaint
            - user_expected_score: Score user thinks they deserved
    
    Returns:
        dict: Success status and feedback ID
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO feedback (
                user_id, username, question_id, question_text, 
                user_answer, ai_score, ai_feedback, user_feedback,
                user_expected_score, submitted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            feedback_data.get('user_id'),
            feedback_data.get('username'),
            feedback_data.get('question_id'),
            feedback_data.get('question_text'),
            feedback_data.get('user_answer'),
            feedback_data.get('ai_score'),
            feedback_data.get('ai_feedback'),
            feedback_data.get('user_feedback'),
            feedback_data.get('user_expected_score'),
            datetime.now().isoformat()
        ))
        
        feedback_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {'success': True, 'feedback_id': feedback_id}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_user_feedback(username):
    """Get all feedback submitted by a user"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM feedback 
            WHERE username = ? 
            ORDER BY submitted_at DESC
        ''', (username,))
        
        rows = cursor.fetchall()
        conn.close()
        
        feedback_list = []
        for row in rows:
            feedback_list.append({
                'id': row[0],
                'user_id': row[1],
                'username': row[2],
                'question_id': row[3],
                'question_text': row[4],
                'user_answer': row[5],
                'ai_score': row[6],
                'ai_feedback': row[7],
                'user_feedback': row[8],
                'user_expected_score': row[9],
                'submitted_at': row[10],
                'status': row[11]
            })
        
        return {'success': True, 'feedback': feedback_list}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_all_feedback(limit=100):
    """Get all feedback (for admin review)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM feedback 
            ORDER BY submitted_at DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        feedback_list = []
        for row in rows:
            feedback_list.append({
                'id': row[0],
                'user_id': row[1],
                'username': row[2],
                'question_id': row[3],
                'question_text': row[4],
                'user_answer': row[5],
                'ai_score': row[6],
                'ai_feedback': row[7],
                'user_feedback': row[8],
                'user_expected_score': row[9],
                'submitted_at': row[10],
                'status': row[11]
            })
        
        return {'success': True, 'feedback': feedback_list, 'count': len(feedback_list)}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def update_feedback_status(feedback_id, status):
    """Update feedback status (pending, reviewed, resolved)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE feedback 
            SET status = ? 
            WHERE id = ?
        ''', (status, feedback_id))
        
        conn.commit()
        conn.close()
        
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_feedback_stats():
    """Get feedback statistics"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Total feedback count
        cursor.execute('SELECT COUNT(*) FROM feedback')
        total = cursor.fetchone()[0]
        
        # Pending feedback
        cursor.execute('SELECT COUNT(*) FROM feedback WHERE status = "pending"')
        pending = cursor.fetchone()[0]
        
        # Reviewed feedback
        cursor.execute('SELECT COUNT(*) FROM feedback WHERE status = "reviewed"')
        reviewed = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'success': True,
            'stats': {
                'total': total,
                'pending': pending,
                'reviewed': reviewed
            }
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

# Initialize database when module is imported
init_feedback_db()
