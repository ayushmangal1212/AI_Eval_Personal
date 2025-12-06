# 🐛 Debugging: Start Evaluation Button Issue

## Problem
The "Start Evaluation" button shows an alert and closes immediately.

## Possible Causes

### 1. **API Endpoint Error**
The `/api/generate-questions` endpoint might be failing.

**Check Flask Console**:
Look at the terminal where Flask is running for error messages.

### 2. **DeepSeek API Issue**
The LLM API might not be responding.

**Check**:
- Is `DEEPSEEK_API_KEY` set in `.env`?
- Is the API key valid?
- Is there internet connectivity?

### 3. **JavaScript Error**
The form submission might be failing before reaching the server.

---

## 🧪 Quick Test

### **Test 1: Check Browser Console**
1. Open page: `http://localhost:5000/evaluation/new`
2. Press `F12` to open Developer Console
3. Go to "Console" tab
4. Fill form and click "Start Evaluation"
5. Look for error messages in red

### **Test 2: Check Network Tab**
1. Open Developer Console (`F12`)
2. Go to "Network" tab
3. Click "Start Evaluation"
4. Look for `/api/generate-questions` request
5. Click on it to see:
   - Status code (should be 200)
   - Response data
   - Any error messages

### **Test 3: Check Flask Server Logs**
Look at the terminal where you ran `python app.py` or `start_flask.bat`.
You should see:
```
POST /api/generate-questions HTTP/1.1" 200
```

If you see `500` or `404`, there's a server error.

---

## 🔍 Common Issues & Solutions

### **Issue 1: "Failed to generate questions"**
**Cause**: Server returned `success: false`

**Solution**:
Check Flask logs for the actual error. Likely causes:
- DeepSeek API key missing or invalid
- LLM API timeout
- Network issue

**Fix**:
```bash
# Check .env file
DEEPSEEK_API_KEY=your-actual-api-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-reasoner
```

### **Issue 2: "An error occurred"**
**Cause**: JavaScript exception or network error

**Solution**:
1. Check browser console for JavaScript errors
2. Check if Flask server is running
3. Verify the endpoint exists in `app.py`

### **Issue 3: CORS Error**
**Cause**: Cross-origin request blocked

**Solution**:
Make sure you're accessing via `http://localhost:5000`, not `file://`

---

## 📝 What to Check

### **1. Environment Variables** (`.env` file):
```env
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-reasoner
SECRET_KEY=your-secret-key
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

### **2. Flask Server Running**:
```bash
# Should see:
* Running on http://127.0.0.1:5000
* Debugger is active!
```

### **3. API Endpoint Exists** (`app.py`):
```python
@app.route('/api/generate-questions', methods=['POST'])
@login_required
def generate_questions():
    # Should exist
```

---

## 🚀 Quick Fix Steps

### **Step 1: Restart Flask Server**
```bash
# Stop current server (Ctrl+C)
# Start again
python app.py
```

### **Step 2: Check API Key**
```bash
# In Python console
python
>>> import os
>>> from dotenv import load_dotenv
>>> load_dotenv()
>>> print(os.getenv('DEEPSEEK_API_KEY'))
# Should print your API key
```

### **Step 3: Test API Endpoint Manually**
Open a new terminal and run:
```bash
curl -X POST http://localhost:5000/api/generate-questions \
  -H "Content-Type: application/json" \
  -d '{"role":"Python Developer","skills":["Python","Django"],"language":"English"}'
```

Should return JSON with questions.

---

## 📊 Expected vs Actual

### **Expected Behavior**:
1. Click "Start Evaluation"
2. Spinner shows
3. Questions generate (5-10 seconds)
4. Evaluation screen appears

### **Actual Behavior**:
1. Click "Start Evaluation"
2. Alert appears
3. Page closes/resets

---

## 🎯 Next Steps

1. **Check Browser Console** - Look for JavaScript errors
2. **Check Network Tab** - See the API response
3. **Check Flask Logs** - See server-side errors
4. **Verify API Key** - Make sure DeepSeek API is configured

---

## 💡 Most Likely Issue

**DeepSeek API Key Not Set or Invalid**

The most common cause is that the `DEEPSEEK_API_KEY` in your `.env` file is either:
- Missing
- Invalid
- Expired

**Solution**:
1. Get a valid API key from DeepSeek
2. Update `.env` file
3. Restart Flask server
4. Try again

---

**Please check the browser console (F12) and Flask server logs, then share what error you see!**
