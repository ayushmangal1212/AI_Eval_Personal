# 🎯 Evaluation Attempts Control System - Implementation Guide

## Overview
This document describes the implementation of the evaluation attempts control system with the following rules:
- Each user can take **1 attempt per role**
- Total of **3 attempts** across all roles per user
- Admin can **increase/decrease** attempts for individual users

---

## Database Structure

### User Data Structure
```python
user_data = {
    'username': 'john_doe',
    'password': 'hashed_password',
    'email': 'john@example.com',
    'name': 'John Doe',
    'experience': '5 years',
    'skills': ['Python', 'Flask'],
    'created_at': '2025-01-01T00:00:00',
    
    # Evaluation Attempts Control
    'total_attempts_allowed': 3,  # Total attempts across all roles
    'total_attempts_used': 0,     # How many attempts used so far
    'role_attempts': {            # Attempts per role
        'Python Developer': {
            'allowed': 1,
            'used': 0,
            'last_attempt': None
        },
        'Java Developer': {
            'allowed': 1,
            'used': 0,
            'last_attempt': None
        }
    }
}
```

---

## Implementation Steps

### 1. Update User Registration (app.py)

Add default attempts when user registers:

```python
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # ... existing code ...
        
        # Prepare user data
        user_data = {
            'password': hash_password(password),
            'email': email,
            'created_at': datetime.now().isoformat(),
            'name': fullname,
            'experience': '',
            'skills': [],
            
            # NEW: Evaluation attempts control
            'total_attempts_allowed': 3,
            'total_attempts_used': 0,
            'role_attempts': {}
        }
        
        # ... rest of code ...
```

### 2. Check Attempts Before Evaluation (app.py)

Add route to check if user can take evaluation:

```python
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
```

### 3. Update Attempts After Evaluation (app.py)

Modify save_evaluation to update attempt counts:

```python
@app.route('/api/save-evaluation', methods=['POST'])
@login_required
def save_evaluation():
    data = request.get_json()
    username = session.get('username')
    role = data.get('role')
    
    # Save evaluation data
    eval_data = {
        'date': datetime.now().isoformat(),
        'role': role,
        'score': data.get('score'),
        'max_score': data.get('max_score'),
        'percentage': data.get('percentage'),
        'time_taken': data.get('time_taken'),
        'qa_history': data.get('qa_history', [])
    }
    
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
    
    return jsonify({'success': True})
```

### 4. Admin: View User Attempts (app.py)

Add route for admin to view user attempts:

```python
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
```

### 5. Admin: Update User Attempts (app.py)

Add route for admin to modify attempts:

```python
@app.route('/api/admin/update-attempts', methods=['POST'])
@admin_required
def update_user_attempts():
    """Admin can increase/decrease user attempts"""
    data = request.get_json()
    username = data.get('username')
    action = data.get('action')  # 'increase_total', 'decrease_total', 'reset_role'
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
```

---

## Frontend Implementation

### 1. Check Attempts Before Starting Evaluation (evaluation.html)

Add JavaScript to check attempts when user selects a role:

```javascript
// Check if user can take evaluation for selected role
async function checkEvaluationAttempts(role) {
    try {
        const response = await fetch('/api/check-attempts', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({role: role})
        });
        
        const data = await response.json();
        
        if (!data.can_attempt) {
            // Show error message
            alert(data.message);
            return false;
        }
        
        // Show remaining attempts
        if (data.total_remaining <= 1) {
            const warning = `⚠️ Warning: This is your last attempt! (${data.total_remaining} remaining)`;
            document.getElementById('attemptWarning').textContent = warning;
            document.getElementById('attemptWarning').style.display = 'block';
        }
        
        return true;
    } catch (error) {
        console.error('Error checking attempts:', error);
        return false;
    }
}

// Call this when form is submitted
document.getElementById('setupForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const role = document.getElementById('role').value;
    
    // Check attempts first
    const canAttempt = await checkEvaluationAttempts(role);
    
    if (!canAttempt) {
        return; // Don't proceed
    }
    
    // Proceed with evaluation...
});
```

### 2. Admin Dashboard: Manage User Attempts (admin_dashboard.html)

Add UI for admin to manage attempts:

```html
<!-- User Attempts Management Section -->
<div class="card">
    <div class="card-header">
        <h2 class="card-title">👥 Manage User Attempts</h2>
    </div>
    
    <table class="admin-table">
        <thead>
            <tr>
                <th>Username</th>
                <th>Total Allowed</th>
                <th>Total Used</th>
                <th>Remaining</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for username, user in users.items() %}
            <tr>
                <td>{{ username }}</td>
                <td>{{ user.get('total_attempts_allowed', 3) }}</td>
                <td>{{ user.get('total_attempts_used', 0) }}</td>
                <td>{{ user.get('total_attempts_allowed', 3) - user.get('total_attempts_used', 0) }}</td>
                <td>
                    <button onclick="increaseAttempts('{{ username }}', 1)" class="btn btn-sm btn-success">
                        +1
                    </button>
                    <button onclick="decreaseAttempts('{{ username }}', 1)" class="btn btn-sm btn-warning">
                        -1
                    </button>
                    <button onclick="resetAllAttempts('{{ username }}')" class="btn btn-sm btn-danger">
                        Reset All
                    </button>
                    <button onclick="viewRoleAttempts('{{ username }}')" class="btn btn-sm btn-outline">
                        View Details
                    </button>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>

<script>
async function increaseAttempts(username, amount) {
    const response = await fetch('/api/admin/update-attempts', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            username: username,
            action: 'increase_total',
            amount: amount
        })
    });
    
    const data = await response.json();
    if (data.success) {
        alert(data.message);
        location.reload();
    }
}

async function decreaseAttempts(username, amount) {
    const response = await fetch('/api/admin/update-attempts', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            username: username,
            action: 'decrease_total',
            amount: amount
        })
    });
    
    const data = await response.json();
    if (data.success) {
        alert(data.message);
        location.reload();
    }
}

async function resetAllAttempts(username) {
    if (!confirm(`Reset all attempts for ${username}?`)) return;
    
    const response = await fetch('/api/admin/update-attempts', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            username: username,
            action: 'reset_all'
        })
    });
    
    const data = await response.json();
    if (data.success) {
        alert(data.message);
        location.reload();
    }
}
</script>
```

---

## Testing Scenarios

### Test 1: New User Registration
```
1. Register new user
2. Check user data has:
   - total_attempts_allowed: 3
   - total_attempts_used: 0
   - role_attempts: {}
```

### Test 2: First Evaluation
```
1. User takes Python Developer evaluation
2. After completion:
   - total_attempts_used: 1
   - role_attempts['Python Developer'].used: 1
   - Remaining: 2
```

### Test 3: Same Role Again
```
1. User tries Python Developer again
2. System blocks with message:
   "You have already attempted Python Developer"
```

### Test 4: Different Role
```
1. User takes Java Developer evaluation
2. After completion:
   - total_attempts_used: 2
   - role_attempts['Java Developer'].used: 1
   - Remaining: 1
```

### Test 5: Third Attempt
```
1. User takes Frontend Developer evaluation
2. After completion:
   - total_attempts_used: 3
   - Remaining: 0
```

### Test 6: No More Attempts
```
1. User tries any role
2. System blocks with message:
   "You have used all 3 attempts"
```

### Test 7: Admin Increases Attempts
```
1. Admin adds +2 attempts
2. User now has:
   - total_attempts_allowed: 5
   - Can take 2 more evaluations
```

### Test 8: Admin Resets Role
```
1. Admin resets Python Developer
2. User can retake Python Developer
3. total_attempts_used decreases by 1
```

---

## Dashboard Display

### User Dashboard
Show attempts remaining:

```html
<div class="stat-card">
    <div class="stat-icon">🎯</div>
    <div class="stat-value">{{ 3 - user.get('total_attempts_used', 0) }}</div>
    <div class="stat-label">Attempts Remaining</div>
</div>

<div class="card">
    <h3>Role-wise Attempts</h3>
    <ul>
        {% for role, data in user.get('role_attempts', {}).items() %}
        <li>
            {{ role }}: 
            {% if data.used >= data.allowed %}
                ❌ Completed
            {% else %}
                ✅ Available
            {% endif %}
        </li>
        {% endfor %}
    </ul>
</div>
```

---

## Summary

This implementation provides:
✅ 1 attempt per role per user
✅ 3 total attempts across all roles
✅ Admin can increase/decrease attempts
✅ Admin can reset specific role attempts
✅ Clear user feedback on remaining attempts
✅ Prevents users from exceeding limits
✅ Tracks attempt history per role

Ready to implement! 🚀
