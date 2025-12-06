"""
SQLite Database utilities for AI Evaluation System
Replaces JSON file storage with database operations
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import logging

# Database file path
DB_FILE = "evaluation_system.db"

def get_connection():
    """Get a connection to the SQLite database"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn

def init_database():
    """Initialize database tables if they don't exist"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT,
                experience TEXT NOT NULL,
                password TEXT NOT NULL,
                created_at TEXT NOT NULL,
                eval_chances TEXT,
                eval_taken_counts TEXT,
                skills TEXT
            )
        """)
        
        # Evaluations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                date TEXT NOT NULL,
                role TEXT NOT NULL,
                score INTEGER NOT NULL,
                max_score INTEGER NOT NULL,
                percentage REAL NOT NULL,
                time_taken REAL NOT NULL,
                qa_history TEXT NOT NULL,
                FOREIGN KEY (username) REFERENCES users(username)
            )
        """)
        
        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_evaluations_username 
            ON evaluations(username)
        """)
        
        # Feedback table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                date TEXT NOT NULL,
                role TEXT,
                skills TEXT,
                message TEXT NOT NULL,
                resolved INTEGER DEFAULT 0,
                admin_comment TEXT,
                FOREIGN KEY (username) REFERENCES users(username)
            )
        """)
        
        # Create index for faster feedback queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_feedback_username 
            ON feedback(username)
        """)
        
        conn.commit()
        logging.info("Database initialized successfully")
    except Exception as e:
        logging.error(f"Error initializing database: {e}")
        conn.rollback()
    finally:
        # Ensure 'skills' column exists in existing DBs
        try:
            conn.execute("ALTER TABLE users ADD COLUMN skills TEXT;")
            conn.commit()
        except Exception:
            # Column already exists or cannot be added; ignore
            pass
        conn.close()

# -------------------------
# User Management Functions
# -------------------------

def load_users() -> Dict:
    """Load all users from database and return as dictionary (compatible with JSON format)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        
        users = {}
        for row in rows:
            username = row['username']
            users[username] = {
                'name': row['name'],
                'email': row['email'] or '',
                'experience': row['experience'],
                'password': row['password'],
                'created_at': row['created_at'],
                'eval_chances': json.loads(row['eval_chances']) if row['eval_chances'] else {},
                'eval_taken_counts': json.loads(row['eval_taken_counts']) if row['eval_taken_counts'] else {},
                'skills': json.loads(row['skills']) if row['skills'] else []
            }
        
        return users
    except Exception as e:
        logging.error(f"Error loading users: {e}")
        return {}
    finally:
        conn.close()

def save_users(users: Dict):
    """Save all users to database (replaces entire users table)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Clear existing users
        cursor.execute("DELETE FROM users")
        
        # Insert all users
        for username, user_data in users.items():
            cursor.execute("""
                INSERT INTO users (username, name, email, experience, password, 
                                 created_at, eval_chances, eval_taken_counts, skills)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                username,
                user_data.get('name', ''),
                user_data.get('email', ''),
                user_data.get('experience', ''),
                user_data.get('password', ''),
                user_data.get('created_at', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                json.dumps(user_data.get('eval_chances', {})),
                json.dumps(user_data.get('eval_taken_counts', {})),
                json.dumps(user_data.get('skills', []))
            ))

        conn.commit()
        logging.info(f"Saved {len(users)} users to database")
    except Exception as e:
        logging.error(f"Error saving users: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_user(username: str) -> Optional[Dict]:
    """Get a single user by username"""
    users = load_users()
    return users.get(username)

def add_user(username: str, user_data: Dict):
    """Add or update a single user"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO users 
            (username, name, email, experience, password, created_at, 
             eval_chances, eval_taken_counts, skills)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            username,
            user_data.get('name', ''),
            user_data.get('email', ''),
            user_data.get('experience', ''),
            user_data.get('password', ''),
            user_data.get('created_at', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            json.dumps(user_data.get('eval_chances', {})),
            json.dumps(user_data.get('eval_taken_counts', {})),
            json.dumps(user_data.get('skills', []))
        ))
        
        conn.commit()
        logging.info(f"Added/updated user: {username}")
    except Exception as e:
        logging.error(f"Error adding user: {e}")
        conn.rollback()
    finally:
        conn.close()

def update_user_profile(username: str, profile_data: Dict):
    """Update user profile with resume data (name, skills, etc.)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Get current user data
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        
        if not row:
            logging.error(f"User {username} not found")
            return False
        
        # Update fields that are provided
        update_fields = []
        update_values = []
        
        if 'name' in profile_data:
            update_fields.append("name = ?")
            update_values.append(profile_data['name'])
        
        if 'email' in profile_data:
            update_fields.append("email = ?")
            update_values.append(profile_data['email'])
        
        if 'experience' in profile_data:
            update_fields.append("experience = ?")
            update_values.append(str(profile_data['experience']))
        
        if 'skills' in profile_data:
            update_fields.append("skills = ?")
            update_values.append(json.dumps(profile_data['skills']))
        
        if not update_fields:
            return True  # Nothing to update
        
        # Add username to values for WHERE clause
        update_values.append(username)
        
        # Build and execute UPDATE query
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE username = ?"
        cursor.execute(query, tuple(update_values))
        
        conn.commit()
        logging.info(f"Updated profile for user: {username}")
        return True
        
    except Exception as e:
        logging.error(f"Error updating user profile: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


# -------------------------
# Evaluation History Functions
# -------------------------

def load_eval_history() -> Dict:
    """Load evaluation history from database and return as dictionary (compatible with JSON format)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM evaluations ORDER BY date")
        rows = cursor.fetchall()
        
        history = {}
        for row in rows:
            username = row['username']
            if username not in history:
                history[username] = []
            
            history[username].append({
                'date': row['date'],
                'role': row['role'],
                'score': row['score'],
                'max_score': row['max_score'],
                'percentage': row['percentage'],
                'time_taken': row['time_taken'],
                'qa_history': json.loads(row['qa_history'])
            })
        
        return history
    except Exception as e:
        logging.error(f"Error loading evaluation history: {e}")
        return {}
    finally:
        conn.close()

def save_eval_history(history: Dict):
    """Save all evaluation history to database (replaces entire evaluations table)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Clear existing evaluations
        cursor.execute("DELETE FROM evaluations")
        
        # Insert all evaluations
        for username, evaluations in history.items():
            for eval_data in evaluations:
                cursor.execute("""
                    INSERT INTO evaluations 
                    (username, date, role, score, max_score, percentage, time_taken, qa_history)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    username,
                    eval_data.get('date', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                    eval_data.get('role', ''),
                    eval_data.get('score', 0),
                    eval_data.get('max_score', 0),
                    eval_data.get('percentage', 0.0),
                    eval_data.get('time_taken', 0.0),
                    json.dumps(eval_data.get('qa_history', []))
                ))
        
        conn.commit()
        total_evals = sum(len(evals) for evals in history.values())
        logging.info(f"Saved {total_evals} evaluations to database")
    except Exception as e:
        logging.error(f"Error saving evaluation history: {e}")
        conn.rollback()
    finally:
        conn.close()

def save_evaluation_result(username: str, eval_data: Dict):
    """Save a single evaluation result to database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO evaluations 
            (username, date, role, score, max_score, percentage, time_taken, qa_history)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            username,
            eval_data.get('date', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            eval_data.get('role', ''),
            eval_data.get('score', 0),
            eval_data.get('max_score', 0),
            eval_data.get('percentage', 0.0),
            eval_data.get('time_taken', 0.0),
            json.dumps(eval_data.get('qa_history', []))
        ))
        
        conn.commit()
        logging.info(f"Saved evaluation for user: {username}")
    except Exception as e:
        logging.error(f"Error saving evaluation result: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_user_evaluations(username: str) -> List[Dict]:
    """Get all evaluations for a specific user"""
    history = load_eval_history()
    return history.get(username, [])

# -------------------------
# Feedback Functions
# -------------------------

def load_feedback() -> Dict:
    """Load all feedback from database and return as dictionary (compatible with JSON format)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM feedback ORDER BY date")
        rows = cursor.fetchall()
        
        feedback = {}
        for row in rows:
            username = row['username']
            if username not in feedback:
                feedback[username] = []
            
            feedback[username].append({
                'date': row['date'],
                'role': row['role'],
                'skills': json.loads(row['skills']) if row['skills'] else [],
                'message': row['message'],
                'resolved': bool(row['resolved']),
                'admin_comment': row['admin_comment']
            })
        
        return feedback
    except Exception as e:
        logging.error(f"Error loading feedback: {e}")
        return {}
    finally:
        conn.close()

def save_feedback(feedback: Dict):
    """Save all feedback to database (replaces entire feedback table)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Clear existing feedback
        cursor.execute("DELETE FROM feedback")
        
        # Insert all feedback entries
        for username, entries in feedback.items():
            for entry in entries:
                cursor.execute("""
                    INSERT INTO feedback 
                    (username, date, role, skills, message, resolved, admin_comment)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    username,
                    entry.get('date', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                    entry.get('role'),
                    json.dumps(entry.get('skills', [])),
                    entry.get('message', ''),
                    1 if entry.get('resolved', False) else 0,
                    entry.get('admin_comment')
                ))
        
        conn.commit()
        total_feedback = sum(len(entries) for entries in feedback.values())
        logging.info(f"Saved {total_feedback} feedback entries to database")
    except Exception as e:
        logging.error(f"Error saving feedback: {e}")
        conn.rollback()
    finally:
        conn.close()

def add_feedback_entry(username: str, message: str, role: str = None, 
                      skills: List[str] = None):
    """Add a single feedback entry for a user"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO feedback 
            (username, date, role, skills, message, resolved, admin_comment)
            VALUES (?, ?, ?, ?, ?, 0, NULL)
        """, (
            username,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            role,
            json.dumps(skills or []),
            message
        ))
        
        conn.commit()
        logging.info(f"Added feedback for user: {username}")
    except Exception as e:
        logging.error(f"Error adding feedback: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_user_feedback(username: str) -> List[Dict]:
    """Get all feedback for a specific user"""
    feedback = load_feedback()
    return feedback.get(username, [])

# -------------------------
# Migration Functions
# -------------------------

def migrate_from_json():
    """
    Migrate existing JSON data to SQLite database
    Reads users.json, evaluation_history.json, and feedback.json
    """
    import os
    
    migrated_items = {'users': 0, 'evaluations': 0, 'feedback': 0}
    
    # Migrate users
    if os.path.exists('users.json'):
        try:
            with open('users.json', 'r') as f:
                users_data = json.load(f)
            save_users(users_data)
            migrated_items['users'] = len(users_data)
            logging.info(f"Migrated {len(users_data)} users from users.json")
        except Exception as e:
            logging.error(f"Error migrating users: {e}")
    
    # Migrate evaluation history
    if os.path.exists('evaluation_history.json'):
        try:
            with open('evaluation_history.json', 'r') as f:
                history_data = json.load(f)
            save_eval_history(history_data)
            total_evals = sum(len(evals) for evals in history_data.values())
            migrated_items['evaluations'] = total_evals
            logging.info(f"Migrated {total_evals} evaluations from evaluation_history.json")
        except Exception as e:
            logging.error(f"Error migrating evaluation history: {e}")
    
    # Migrate feedback
    if os.path.exists('feedback.json'):
        try:
            with open('feedback.json', 'r') as f:
                feedback_data = json.load(f)
            save_feedback(feedback_data)
            total_feedback = sum(len(entries) for entries in feedback_data.values())
            migrated_items['feedback'] = total_feedback
            logging.info(f"Migrated {total_feedback} feedback entries from feedback.json")
        except Exception as e:
            logging.error(f"Error migrating feedback: {e}")
    
    return migrated_items

def backup_json_files():
    """Create backup copies of JSON files before migration"""
    import shutil
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"json_backup_{timestamp}"
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    files_to_backup = ['users.json', 'evaluation_history.json', 'feedback.json']
    backed_up = []
    
    for filename in files_to_backup:
        if os.path.exists(filename):
            try:
                shutil.copy2(filename, os.path.join(backup_dir, filename))
                backed_up.append(filename)
                logging.info(f"Backed up {filename} to {backup_dir}")
            except Exception as e:
                logging.error(f"Error backing up {filename}: {e}")
    
    return backup_dir, backed_up


# ============================================
# ADMIN CONTROL FUNCTIONS
# ============================================

def admin_get_user_profile(username):
    """Get complete user profile with all details"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT username, name, email, experience, created_at, 
                   eval_chances, eval_taken_counts, skills
            FROM users
            WHERE username = ?
        """, (username,))
        
        row = cursor.fetchone()
        if row:
            return {
                'username': row[0],
                'name': row[1],
                'email': row[2],
                'experience': row[3],
                'created_at': row[4],
                'eval_chances': row[5],
                'eval_taken_counts': row[6],
                'skills': row[7].split(',') if row[7] else []
            }
        return None
    finally:
        conn.close()

def admin_reset_user_attempts(username):
    """Reset user's evaluation attempts"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE users
            SET eval_taken_counts = '0'
            WHERE username = ?
        """, (username,))
        
        conn.commit()
        return {'success': True, 'message': f'Reset attempts for {username}'}
    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        conn.close()

def admin_update_user_skills(username, skills):
    """Update user's skills"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        skills_str = ','.join(skills) if isinstance(skills, list) else skills
        cursor.execute("""
            UPDATE users
            SET skills = ?
            WHERE username = ?
        """, (skills_str, username))
        
        conn.commit()
        return {'success': True, 'message': f'Updated skills for {username}'}
    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        conn.close()

def admin_get_user_evaluations(username):
    """Get all evaluations for a specific user"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, date, role, score, max_score, percentage, 
                   time_taken, qa_history
            FROM evaluations
            WHERE username = ?
            ORDER BY date DESC
        """, (username,))
        
        rows = cursor.fetchall()
        evaluations = []
        
        for row in rows:
            evaluations.append({
                'id': row[0],
                'date': row[1],
                'role': row[2],
                'score': row[3],
                'max_score': row[4],
                'percentage': row[5],
                'time_taken': row[6],
                'qa_history': json.loads(row[7]) if row[7] else []
            })
        
        return evaluations
    finally:
        conn.close()

def admin_update_evaluation_score(eval_id, new_score, new_max_score=None):
    """Update evaluation score (e.g., after reviewing feedback)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Get current evaluation
        cursor.execute("""
            SELECT score, max_score FROM evaluations WHERE id = ?
        """, (eval_id,))
        
        row = cursor.fetchone()
        if not row:
            return {'success': False, 'error': 'Evaluation not found'}
        
        current_max = row[1]
        max_score = new_max_score if new_max_score else current_max
        percentage = (new_score / max_score) * 100
        
        cursor.execute("""
            UPDATE evaluations
            SET score = ?, max_score = ?, percentage = ?
            WHERE id = ?
        """, (new_score, max_score, percentage, eval_id))
        
        conn.commit()
        return {
            'success': True, 
            'message': f'Updated evaluation {eval_id}',
            'new_score': new_score,
            'new_percentage': percentage
        }
    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        conn.close()

def admin_update_question_score(eval_id, question_index, new_score):
    """Update individual question score within an evaluation"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Get evaluation
        cursor.execute("""
            SELECT qa_history, score, max_score FROM evaluations WHERE id = ?
        """, (eval_id,))
        
        row = cursor.fetchone()
        if not row:
            return {'success': False, 'error': 'Evaluation not found'}
        
        qa_history = json.loads(row[0]) if row[0] else []
        current_total = row[1]
        max_score = row[2]
        
        if question_index < 0 or question_index >= len(qa_history):
            return {'success': False, 'error': 'Invalid question index'}
        
        # Update question score
        old_score = qa_history[question_index].get('score', 0)
        qa_history[question_index]['score'] = new_score
        qa_history[question_index]['admin_adjusted'] = True
        
        # Recalculate total score
        new_total = current_total - old_score + new_score
        new_percentage = (new_total / max_score) * 100
        
        # Update database
        cursor.execute("""
            UPDATE evaluations
            SET qa_history = ?, score = ?, percentage = ?
            WHERE id = ?
        """, (json.dumps(qa_history), new_total, new_percentage, eval_id))
        
        conn.commit()
        return {
            'success': True,
            'message': f'Updated question {question_index + 1} score',
            'old_score': old_score,
            'new_score': new_score,
            'new_total': new_total,
            'new_percentage': new_percentage
        }
    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        conn.close()

def admin_delete_evaluation(eval_id):
    """Delete an evaluation"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM evaluations WHERE id = ?", (eval_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            return {'success': True, 'message': f'Deleted evaluation {eval_id}'}
        else:
            return {'success': False, 'error': 'Evaluation not found'}
    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        conn.close()

def admin_get_all_users_summary():
    """Get summary of all users"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT u.username, u.name, u.email, u.created_at, u.skills,
                   COUNT(e.id) as eval_count,
                   AVG(e.percentage) as avg_percentage
            FROM users u
            LEFT JOIN evaluations e ON u.username = e.username
            GROUP BY u.username
            ORDER BY u.created_at DESC
        """)
        
        rows = cursor.fetchall()
        users = []
        
        for row in rows:
            users.append({
                'username': row[0],
                'name': row[1],
                'email': row[2],
                'created_at': row[3],
                'skills': row[4].split(',') if row[4] else [],
                'eval_count': row[5] or 0,
                'avg_percentage': round(row[6], 1) if row[6] else 0
            })
        
        return users
    finally:
        conn.close()


# Initialize database on module import
init_database()
