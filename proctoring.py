"""
Video Proctoring Module
Monitors candidate behavior during evaluations
"""

from datetime import datetime
import json

class VideoProctoring:
    """
    Video proctoring system to monitor candidates during evaluations
    Tracks violations and suspicious behavior
    """
    
    def __init__(self):
        self.sessions = {}
        self.violations_log = []
    
    def start_session(self, username, evaluation_id):
        """
        Start a proctoring session
        
        Args:
            username: Candidate username
            evaluation_id: Unique evaluation ID
            
        Returns:
            dict: Session information
        """
        session_id = f"{username}_{evaluation_id}_{int(datetime.now().timestamp())}"
        
        self.sessions[session_id] = {
            'session_id': session_id,
            'username': username,
            'evaluation_id': evaluation_id,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'violations': [],
            'tab_switches': 0,
            'window_blur_count': 0,
            'copy_paste_attempts': 0,
            'suspicious_activity_score': 0,
            'webcam_enabled': False,
            'screen_recording': False,
            'status': 'active'
        }
        
        return {
            'success': True,
            'session_id': session_id,
            'message': 'Proctoring session started'
        }
    
    def log_violation(self, session_id, violation_type, details=''):
        """
        Log a proctoring violation
        
        Args:
            session_id: Session ID
            violation_type: Type of violation
            details: Additional details
        """
        if session_id not in self.sessions:
            return {'success': False, 'message': 'Session not found'}
        
        violation = {
            'timestamp': datetime.now().isoformat(),
            'type': violation_type,
            'details': details,
            'severity': self._get_violation_severity(violation_type)
        }
        
        self.sessions[session_id]['violations'].append(violation)
        
        # Update counters
        if violation_type == 'tab_switch':
            self.sessions[session_id]['tab_switches'] += 1
        elif violation_type == 'window_blur':
            self.sessions[session_id]['window_blur_count'] += 1
        elif violation_type == 'copy_paste':
            self.sessions[session_id]['copy_paste_attempts'] += 1
        
        # Update suspicious activity score
        self.sessions[session_id]['suspicious_activity_score'] += violation['severity']
        
        # Log to global violations
        self.violations_log.append({
            'session_id': session_id,
            'username': self.sessions[session_id]['username'],
            **violation
        })
        
        return {
            'success': True,
            'violation_logged': True,
            'total_violations': len(self.sessions[session_id]['violations'])
        }
    
    def _get_violation_severity(self, violation_type):
        """Get severity score for violation type"""
        severity_map = {
            'tab_switch': 5,
            'window_blur': 3,
            'copy_paste': 10,
            'multiple_faces': 15,
            'no_face': 10,
            'phone_detected': 8,
            'unauthorized_device': 12,
            'screen_share': 20
        }
        return severity_map.get(violation_type, 5)
    
    def enable_webcam(self, session_id):
        """Enable webcam monitoring"""
        if session_id in self.sessions:
            self.sessions[session_id]['webcam_enabled'] = True
            return {'success': True, 'message': 'Webcam enabled'}
        return {'success': False, 'message': 'Session not found'}
    
    def enable_screen_recording(self, session_id):
        """Enable screen recording"""
        if session_id in self.sessions:
            self.sessions[session_id]['screen_recording'] = True
            return {'success': True, 'message': 'Screen recording enabled'}
        return {'success': False, 'message': 'Session not found'}
    
    def end_session(self, session_id):
        """
        End a proctoring session
        
        Args:
            session_id: Session ID
            
        Returns:
            dict: Session summary
        """
        if session_id not in self.sessions:
            return {'success': False, 'message': 'Session not found'}
        
        session = self.sessions[session_id]
        session['end_time'] = datetime.now().isoformat()
        session['status'] = 'completed'
        
        # Generate summary
        summary = {
            'session_id': session_id,
            'username': session['username'],
            'duration': self._calculate_duration(session['start_time'], session['end_time']),
            'total_violations': len(session['violations']),
            'tab_switches': session['tab_switches'],
            'window_blur_count': session['window_blur_count'],
            'copy_paste_attempts': session['copy_paste_attempts'],
            'suspicious_activity_score': session['suspicious_activity_score'],
            'risk_level': self._calculate_risk_level(session['suspicious_activity_score']),
            'recommendation': self._get_recommendation(session['suspicious_activity_score'])
        }
        
        return {
            'success': True,
            'summary': summary
        }
    
    def _calculate_duration(self, start_time, end_time):
        """Calculate session duration"""
        try:
            start = datetime.fromisoformat(start_time)
            end = datetime.fromisoformat(end_time)
            duration = (end - start).total_seconds()
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            return f"{minutes}:{seconds:02d}"
        except:
            return "0:00"
    
    def _calculate_risk_level(self, score):
        """Calculate risk level based on suspicious activity score"""
        if score >= 50:
            return 'high'
        elif score >= 20:
            return 'medium'
        elif score > 0:
            return 'low'
        return 'none'
    
    def _get_recommendation(self, score):
        """Get recommendation based on suspicious activity score"""
        if score >= 50:
            return 'High risk of cheating detected. Manual review strongly recommended.'
        elif score >= 20:
            return 'Moderate suspicious activity detected. Consider manual review.'
        elif score > 0:
            return 'Minor violations detected. Evaluation likely valid.'
        return 'No violations detected. Evaluation appears valid.'
    
    def get_session_status(self, session_id):
        """Get current status of a session"""
        if session_id not in self.sessions:
            return {'success': False, 'message': 'Session not found'}
        
        session = self.sessions[session_id]
        return {
            'success': True,
            'session': {
                'session_id': session_id,
                'status': session['status'],
                'violations_count': len(session['violations']),
                'suspicious_activity_score': session['suspicious_activity_score'],
                'risk_level': self._calculate_risk_level(session['suspicious_activity_score'])
            }
        }
    
    def get_all_violations(self, session_id=None):
        """Get all violations, optionally filtered by session"""
        if session_id:
            if session_id in self.sessions:
                return {
                    'success': True,
                    'violations': self.sessions[session_id]['violations']
                }
            return {'success': False, 'message': 'Session not found'}
        
        return {
            'success': True,
            'violations': self.violations_log
        }
    
    def generate_proctoring_report(self, session_id):
        """Generate detailed proctoring report"""
        if session_id not in self.sessions:
            return {'success': False, 'message': 'Session not found'}
        
        session = self.sessions[session_id]
        
        report = {
            'session_info': {
                'session_id': session_id,
                'username': session['username'],
                'start_time': session['start_time'],
                'end_time': session['end_time'],
                'status': session['status']
            },
            'monitoring': {
                'webcam_enabled': session['webcam_enabled'],
                'screen_recording': session['screen_recording']
            },
            'violations': {
                'total': len(session['violations']),
                'by_type': self._group_violations_by_type(session['violations']),
                'timeline': session['violations']
            },
            'metrics': {
                'tab_switches': session['tab_switches'],
                'window_blur_count': session['window_blur_count'],
                'copy_paste_attempts': session['copy_paste_attempts'],
                'suspicious_activity_score': session['suspicious_activity_score']
            },
            'assessment': {
                'risk_level': self._calculate_risk_level(session['suspicious_activity_score']),
                'recommendation': self._get_recommendation(session['suspicious_activity_score']),
                'integrity_score': max(0, 100 - session['suspicious_activity_score'])
            },
            'generated_at': datetime.now().isoformat()
        }
        
        return {
            'success': True,
            'report': report
        }
    
    def _group_violations_by_type(self, violations):
        """Group violations by type"""
        grouped = {}
        for violation in violations:
            v_type = violation['type']
            if v_type not in grouped:
                grouped[v_type] = 0
            grouped[v_type] += 1
        return grouped

# Global proctoring instance
proctoring_service = VideoProctoring()
