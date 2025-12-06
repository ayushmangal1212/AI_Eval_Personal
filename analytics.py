"""
Advanced Analytics Module
Provides comprehensive analytics and insights for evaluations
"""

from datetime import datetime, timedelta
from collections import defaultdict
import json

class AdvancedAnalytics:
    """Advanced analytics engine for evaluation data"""
    
    def __init__(self, history_data, users_data):
        """
        Initialize analytics with evaluation history and user data
        
        Args:
            history_data: Dictionary of user evaluations
            users_data: Dictionary of user information
        """
        self.history = history_data
        self.users = users_data
    
    def get_overview_stats(self):
        """Get high-level overview statistics"""
        total_evaluations = sum(len(evals) for evals in self.history.values())
        total_users = len(self.users)
        active_users = len([u for u in self.history.keys() if len(self.history[u]) > 0])
        
        # Calculate average score
        all_scores = []
        for user_evals in self.history.values():
            for eval in user_evals:
                if 'percentage' in eval:
                    all_scores.append(eval['percentage'])
        
        avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
        
        # Pass rate (>= 60%)
        passed = len([s for s in all_scores if s >= 60])
        pass_rate = (passed / len(all_scores) * 100) if all_scores else 0
        
        return {
            'total_evaluations': total_evaluations,
            'total_users': total_users,
            'active_users': active_users,
            'average_score': round(avg_score, 2),
            'pass_rate': round(pass_rate, 2),
            'total_passed': passed,
            'total_failed': len(all_scores) - passed
        }
    
    def get_role_distribution(self):
        """Get distribution of evaluations by role"""
        role_counts = defaultdict(int)
        role_scores = defaultdict(list)
        
        for user_evals in self.history.values():
            for eval in user_evals:
                role = eval.get('role', 'Unknown')
                role_counts[role] += 1
                if 'percentage' in eval:
                    role_scores[role].append(eval['percentage'])
        
        role_stats = []
        for role, count in role_counts.items():
            avg_score = sum(role_scores[role]) / len(role_scores[role]) if role_scores[role] else 0
            role_stats.append({
                'role': role,
                'count': count,
                'average_score': round(avg_score, 2),
                'pass_rate': round(len([s for s in role_scores[role] if s >= 60]) / len(role_scores[role]) * 100, 2) if role_scores[role] else 0
            })
        
        return sorted(role_stats, key=lambda x: x['count'], reverse=True)
    
    def get_performance_trends(self, days=30):
        """Get performance trends over time"""
        trends = []
        today = datetime.now()
        
        for i in range(days):
            date = (today - timedelta(days=days-i-1)).strftime('%Y-%m-%d')
            day_evals = []
            
            for user_evals in self.history.values():
                for eval in user_evals:
                    eval_date = eval.get('date', '')
                    if eval_date.startswith(date):
                        if 'percentage' in eval:
                            day_evals.append(eval['percentage'])
            
            if day_evals:
                trends.append({
                    'date': date,
                    'count': len(day_evals),
                    'average_score': round(sum(day_evals) / len(day_evals), 2),
                    'pass_rate': round(len([s for s in day_evals if s >= 60]) / len(day_evals) * 100, 2)
                })
        
        return trends
    
    def get_top_performers(self, limit=10):
        """Get top performing candidates"""
        user_performances = []
        
        for username, user_evals in self.history.items():
            if not user_evals:
                continue
            
            scores = [eval.get('percentage', 0) for eval in user_evals]
            avg_score = sum(scores) / len(scores)
            best_score = max(scores)
            
            user_performances.append({
                'username': username,
                'email': self.users.get(username, {}).get('email', ''),
                'total_evaluations': len(user_evals),
                'average_score': round(avg_score, 2),
                'best_score': round(best_score, 2),
                'latest_role': user_evals[-1].get('role', 'Unknown')
            })
        
        return sorted(user_performances, key=lambda x: x['average_score'], reverse=True)[:limit]
    
    def get_skill_analysis(self):
        """Analyze performance by skills (if available)"""
        # This would require storing skills with each evaluation
        # For now, return role-based analysis
        return self.get_role_distribution()
    
    def get_time_analysis(self):
        """Analyze time taken for evaluations"""
        time_data = []
        
        for user_evals in self.history.values():
            for eval in user_evals:
                time_taken = eval.get('time_taken', '')
                if time_taken:
                    # Parse time (format: "MM:SS" or similar)
                    try:
                        if ':' in time_taken:
                            parts = time_taken.split(':')
                            minutes = int(parts[0])
                            seconds = int(parts[1]) if len(parts) > 1 else 0
                            total_seconds = minutes * 60 + seconds
                            
                            time_data.append({
                                'role': eval.get('role', 'Unknown'),
                                'time_seconds': total_seconds,
                                'score': eval.get('percentage', 0)
                            })
                    except:
                        pass
        
        if not time_data:
            return {'average_time': 0, 'min_time': 0, 'max_time': 0}
        
        times = [d['time_seconds'] for d in time_data]
        
        return {
            'average_time': round(sum(times) / len(times), 2),
            'min_time': min(times),
            'max_time': max(times),
            'time_vs_score_correlation': self._calculate_correlation(
                [d['time_seconds'] for d in time_data],
                [d['score'] for d in time_data]
            )
        }
    
    def get_score_distribution(self):
        """Get distribution of scores in ranges"""
        all_scores = []
        for user_evals in self.history.values():
            for eval in user_evals:
                if 'percentage' in eval:
                    all_scores.append(eval['percentage'])
        
        if not all_scores:
            return []
        
        ranges = [
            {'range': '0-20%', 'min': 0, 'max': 20},
            {'range': '20-40%', 'min': 20, 'max': 40},
            {'range': '40-60%', 'min': 40, 'max': 60},
            {'range': '60-80%', 'min': 60, 'max': 80},
            {'range': '80-100%', 'min': 80, 'max': 100},
        ]
        
        distribution = []
        for r in ranges:
            count = len([s for s in all_scores if r['min'] <= s < r['max'] or (r['max'] == 100 and s == 100)])
            percentage = (count / len(all_scores) * 100) if all_scores else 0
            distribution.append({
                'range': r['range'],
                'count': count,
                'percentage': round(percentage, 2)
            })
        
        return distribution
    
    def get_user_insights(self, username):
        """Get detailed insights for a specific user"""
        if username not in self.history:
            return None
        
        user_evals = self.history[username]
        if not user_evals:
            return None
        
        scores = [eval.get('percentage', 0) for eval in user_evals]
        roles = [eval.get('role', 'Unknown') for eval in user_evals]
        
        # Calculate improvement trend
        if len(scores) > 1:
            improvement = scores[-1] - scores[0]
            trend = 'improving' if improvement > 5 else ('declining' if improvement < -5 else 'stable')
        else:
            improvement = 0
            trend = 'new'
        
        return {
            'username': username,
            'total_evaluations': len(user_evals),
            'average_score': round(sum(scores) / len(scores), 2),
            'best_score': round(max(scores), 2),
            'worst_score': round(min(scores), 2),
            'latest_score': round(scores[-1], 2),
            'improvement': round(improvement, 2),
            'trend': trend,
            'roles_attempted': list(set(roles)),
            'most_common_role': max(set(roles), key=roles.count)
        }
    
    def get_recommendations(self):
        """Get AI-powered recommendations based on data"""
        recommendations = []
        
        overview = self.get_overview_stats()
        
        # Low pass rate
        if overview['pass_rate'] < 50:
            recommendations.append({
                'type': 'warning',
                'title': 'Low Pass Rate',
                'message': f"Only {overview['pass_rate']}% of evaluations are passing. Consider reviewing question difficulty.",
                'action': 'Review question difficulty levels'
            })
        
        # High average score
        if overview['average_score'] > 85:
            recommendations.append({
                'type': 'info',
                'title': 'High Performance',
                'message': f"Average score is {overview['average_score']}%. Questions might be too easy.",
                'action': 'Consider adding more challenging questions'
            })
        
        # Low user engagement
        if overview['total_users'] > 0:
            engagement_rate = (overview['active_users'] / overview['total_users']) * 100
            if engagement_rate < 30:
                recommendations.append({
                    'type': 'warning',
                    'title': 'Low User Engagement',
                    'message': f"Only {engagement_rate:.1f}% of users have taken evaluations.",
                    'action': 'Send reminder emails to inactive users'
                })
        
        return recommendations
    
    def _calculate_correlation(self, x, y):
        """Calculate correlation coefficient between two lists"""
        if len(x) != len(y) or len(x) == 0:
            return 0
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi ** 2 for xi in x)
        sum_y2 = sum(yi ** 2 for yi in y)
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = ((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2)) ** 0.5
        
        if denominator == 0:
            return 0
        
        return round(numerator / denominator, 3)
    
    def generate_report(self):
        """Generate comprehensive analytics report"""
        return {
            'overview': self.get_overview_stats(),
            'role_distribution': self.get_role_distribution(),
            'score_distribution': self.get_score_distribution(),
            'top_performers': self.get_top_performers(5),
            'time_analysis': self.get_time_analysis(),
            'recommendations': self.get_recommendations(),
            'generated_at': datetime.now().isoformat()
        }
