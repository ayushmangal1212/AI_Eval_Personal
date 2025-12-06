"""
Email Service Module
Mock email service that simulates sending emails without actually sending them
"""

from datetime import datetime
import json
import os

# Email templates
EMAIL_TEMPLATES = {
    'welcome': {
        'subject': '🎉 Welcome to AI Evaluation System!',
        'body': '''
Hello {name},

Welcome to the AI-Powered Evaluation System! 🚀

Your account has been successfully created. You can now:
✅ Take technical assessments
✅ Track your performance
✅ View detailed feedback
✅ Improve your skills

Get started: http://localhost:5000/login

Best regards,
AI Evaluation Team
        '''
    },
    'evaluation_invite': {
        'subject': '📝 You\'re Invited to Take an Evaluation',
        'body': '''
Hello {name},

You have been invited to take a technical evaluation for the position of {role}.

⏰ Time Limit: {duration} minutes
📊 Questions: {question_count}
🎯 Skills: {skills}

Start your evaluation: http://localhost:5000/evaluation/new

Good luck! 🍀

Best regards,
AI Evaluation Team
        '''
    },
    'evaluation_complete': {
        'subject': '✅ Evaluation Completed - Results Available',
        'body': '''
Hello {name},

Congratulations on completing your {role} evaluation! 🎉

📊 Your Results:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Score: {score}/{max_score} ({percentage}%)
Status: {status}
Time Taken: {time_taken}

{recommendation}

View detailed results: http://localhost:5000/dashboard

Best regards,
AI Evaluation Team
        '''
    },
    'admin_notification': {
        'subject': '🔔 New Evaluation Completed',
        'body': '''
Hello Admin,

A new evaluation has been completed:

👤 Candidate: {candidate_name}
💼 Role: {role}
📊 Score: {score}/{max_score} ({percentage}%)
⏰ Completed: {completion_time}

View details: http://localhost:5000/admin/dashboard

Best regards,
AI Evaluation System
        '''
    },
    'reminder': {
        'subject': '⏰ Reminder: Complete Your Evaluation',
        'body': '''
Hello {name},

This is a friendly reminder that you have a pending evaluation for {role}.

Don't miss out on this opportunity! Complete your assessment soon.

Start now: http://localhost:5000/evaluation/new

Best regards,
AI Evaluation Team
        '''
    }
}

class EmailService:
    """Mock email service that logs emails instead of sending them"""
    
    def __init__(self):
        self.email_log_file = 'email_logs.json'
        self.sent_emails = []
        self._load_logs()
    
    def _load_logs(self):
        """Load email logs from file"""
        if os.path.exists(self.email_log_file):
            try:
                with open(self.email_log_file, 'r') as f:
                    self.sent_emails = json.load(f)
            except:
                self.sent_emails = []
    
    def _save_logs(self):
        """Save email logs to file"""
        try:
            with open(self.email_log_file, 'w') as f:
                json.dump(self.sent_emails, f, indent=2)
        except Exception as e:
            print(f"Error saving email logs: {e}")
    
    def send_email(self, to_email, template_name, **kwargs):
        """
        Mock send email - logs the email instead of actually sending
        
        Args:
            to_email: Recipient email address
            template_name: Name of the email template to use
            **kwargs: Template variables
        
        Returns:
            dict: Email send status
        """
        if template_name not in EMAIL_TEMPLATES:
            return {
                'success': False,
                'message': f'Template {template_name} not found'
            }
        
        template = EMAIL_TEMPLATES[template_name]
        
        try:
            # Format the email body with provided variables
            subject = template['subject']
            body = template['body'].format(**kwargs)
            
            # Create email log entry
            email_entry = {
                'id': len(self.sent_emails) + 1,
                'to': to_email,
                'subject': subject,
                'body': body,
                'template': template_name,
                'timestamp': datetime.now().isoformat(),
                'status': 'sent'
            }
            
            # Log the email
            self.sent_emails.append(email_entry)
            self._save_logs()
            
            # Print to console for debugging
            print("\n" + "="*60)
            print("📧 EMAIL SENT (MOCK)")
            print("="*60)
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print(f"Template: {template_name}")
            print(f"Timestamp: {email_entry['timestamp']}")
            print("="*60 + "\n")
            
            return {
                'success': True,
                'message': 'Email sent successfully',
                'email_id': email_entry['id']
            }
            
        except KeyError as e:
            return {
                'success': False,
                'message': f'Missing template variable: {e}'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error sending email: {str(e)}'
            }
    
    def send_welcome_email(self, to_email, name):
        """Send welcome email to new user"""
        return self.send_email(
            to_email=to_email,
            template_name='welcome',
            name=name
        )
    
    def send_evaluation_invite(self, to_email, name, role, duration=50, question_count=5, skills=''):
        """Send evaluation invitation email"""
        return self.send_email(
            to_email=to_email,
            template_name='evaluation_invite',
            name=name,
            role=role,
            duration=duration,
            question_count=question_count,
            skills=skills
        )
    
    def send_evaluation_complete(self, to_email, name, role, score, max_score, percentage, time_taken, status, recommendation):
        """Send evaluation completion email"""
        return self.send_email(
            to_email=to_email,
            template_name='evaluation_complete',
            name=name,
            role=role,
            score=score,
            max_score=max_score,
            percentage=f"{percentage:.1f}",
            time_taken=time_taken,
            status=status,
            recommendation=recommendation
        )
    
    def send_admin_notification(self, admin_email, candidate_name, role, score, max_score, percentage):
        """Send notification to admin about completed evaluation"""
        return self.send_email(
            to_email=admin_email,
            template_name='admin_notification',
            candidate_name=candidate_name,
            role=role,
            score=score,
            max_score=max_score,
            percentage=f"{percentage:.1f}",
            completion_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    
    def send_reminder(self, to_email, name, role):
        """Send reminder email"""
        return self.send_email(
            to_email=to_email,
            template_name='reminder',
            name=name,
            role=role
        )
    
    def get_sent_emails(self, limit=50):
        """Get list of sent emails"""
        return self.sent_emails[-limit:]
    
    def get_email_by_id(self, email_id):
        """Get specific email by ID"""
        for email in self.sent_emails:
            if email['id'] == email_id:
                return email
        return None

# Global email service instance
email_service = EmailService()
