# 🔧 Fix app.py - Step by Step Guide

## ⚠️ Problem
app.py has duplicate code (1011 lines instead of ~730 lines)

## ✅ Backup Created
`app_backup.py` - Your original file is safe!

---

## 📋 Step-by-Step Fix

### **Step 1: Find the Duplicate Section**

1. Open `app.py` in your editor
2. Press `Ctrl+F` (Find)
3. Search for: `@app.route('/api/analytics/role-distribution')`
4. You'll find **TWO** instances of this route

### **Step 2: Identify the Duplicate Block**

The duplicate starts around **line 720** and goes to around **line 1000**.

Look for this pattern:
```python
# Line ~720
@app.route('/api/analytics/role-distribution')
@admin_required
def analytics_role_distribution():
    ...

# Then you'll see ALL the routes repeated:
# - analytics routes
# - proctoring routes  
# - registration routes
# - feedback routes
# - AGAIN!
```

### **Step 3: Delete the Duplicate Section**

**Delete from line ~720 to line ~1000** (approximately)

**What to DELETE**:
- Everything from the SECOND occurrence of `@app.route('/api/analytics/role-distribution')`
- Up to (but NOT including) the FIRST occurrence of:
  ```python
  # ============================================
  # ADMIN CONTROL ENDPOINTS
  # ============================================
  ```

**What to KEEP**:
- Keep the FIRST set of routes (lines 1-719)
- Keep the ADMIN CONTROL ENDPOINTS section
- Keep the final `if __name__ == '__main__':`

---

## 🎯 Visual Guide

### **BEFORE** (Wrong - 1011 lines):
```
Line 1-500: Correct routes
Line 501-719: Correct routes (feedback, etc.)
Line 720-1000: DUPLICATE ROUTES ❌ DELETE THIS
Line 1001-1011: if __name__ == '__main__'
```

### **AFTER** (Correct - ~820 lines):
```
Line 1-500: Correct routes
Line 501-719: Correct routes (feedback, etc.)
Line 720-810: ADMIN CONTROL ENDPOINTS ✅ KEEP THIS
Line 811-820: if __name__ == '__main__'
```

---

## 🔍 Detailed Instructions

### **1. Find Line 720**
- Scroll to line 720 (or search for second `analytics_role_distribution`)
- You should see:
  ```python
  @app.route('/api/analytics/role-distribution')
  @admin_required
  def analytics_role_distribution():
  ```

### **2. Select Everything to Delete**
- From line 720
- Down to the line BEFORE:
  ```python
  # ============================================
  # ADMIN CONTROL ENDPOINTS
  # ============================================
  ```

### **3. Delete**
- Select all those lines
- Press `Delete` or `Backspace`

### **4. Verify**
After deletion, you should see:
```python
# ... feedback routes ...

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
    ...
```

---

## ✅ Verification Checklist

After fixing, check:

- [ ] File has ~820 lines (not 1011)
- [ ] Each route appears only ONCE
- [ ] ADMIN CONTROL ENDPOINTS section exists
- [ ] `if __name__ == '__main__':` is at the end
- [ ] No duplicate function names

---

## 🧪 Test the Fix

After fixing, run:
```bash
python app.py
```

**Expected output**:
```
Feedback database initialized successfully
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

**If you see errors**:
- Check for any remaining duplicates
- Make sure you didn't delete too much
- Restore from `app_backup.py` and try again

---

## 🆘 If You Get Stuck

### **Option A: Restore and Try Again**
```bash
copy app_backup.py app.py
```

### **Option B: Tell Me**
Let me know which line numbers you're seeing and I'll help!

---

## 📝 Quick Reference

**Search for**: `@app.route('/api/analytics/role-distribution')`  
**Should find**: 1 occurrence (currently finds 2)  
**Delete**: Lines ~720-1000  
**Keep**: Lines 1-719 + Admin endpoints + if __name__  
**Final size**: ~820 lines  

---

**Good luck! The fix should take 2-3 minutes.** 🚀
