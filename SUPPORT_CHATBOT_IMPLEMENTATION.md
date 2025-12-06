# AI Support Chatbot & Ticketing System - Implementation Guide

## Overview
A comprehensive support system with an AI-powered chatbot that helps users, collects issue information, and creates support tickets for admin review.

---

## Features

### User-Facing Features
1. **Floating Chat Button** - Always visible on user screens
2. **AI Chatbot** - Greets user by name, answers questions
3. **Interactive Support** - Collects issue details through conversation
4. **Ticket Creation** - Automatically creates tickets from conversations
5. **App-Specific Help** - LLM answers questions about the evaluation system

### Admin Features
1. **Ticket Dashboard** - View all open/closed tickets
2. **Ticket Details** - See full conversation history
3. **Ticket Actions** - Close, resolve, or respond to tickets
4. **Statistics** - Track support metrics

---

## Database Schema

### Tickets Table
```sql
CREATE TABLE support_tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id TEXT UNIQUE NOT NULL,
    username TEXT NOT NULL,
    subject TEXT NOT NULL,
    status TEXT DEFAULT 'open',  -- open, in_progress, resolved, closed
    priority TEXT DEFAULT 'medium',  -- low, medium, high, urgent
    category TEXT,  -- technical, account, evaluation, feedback, other
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    resolved_at TEXT,
    resolved_by TEXT,
    admin_notes TEXT
);
```

### Ticket Messages Table
```sql
CREATE TABLE ticket_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id TEXT NOT NULL,
    sender TEXT NOT NULL,  -- username, 'bot', or 'admin'
    message TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (ticket_id) REFERENCES support_tickets(ticket_id)
);
```

---

## Implementation Steps

### Step 1: Database Setup (db_utils.py)

Add functions:
- `create_support_tables()` - Initialize tables
- `create_ticket(username, subject, category)` - Create new ticket
- `add_ticket_message(ticket_id, sender, message)` - Add message
- `load_tickets(status=None)` - Load tickets (filtered by status)
- `load_ticket_messages(ticket_id)` - Get conversation
- `update_ticket_status(ticket_id, status, admin_notes)` - Update ticket
- `get_user_tickets(username)` - Get user's tickets

### Step 2: Backend API (app.py)

Add endpoints:
```python
# User endpoints
@app.route('/api/chat/message', methods=['POST'])
@login_required
def chat_message()
    # Process user message
    # Get AI response
    # Return response

@app.route('/api/chat/create-ticket', methods=['POST'])
@login_required
def create_support_ticket()
    # Create ticket from conversation
    # Return ticket ID

@app.route('/api/chat/my-tickets')
@login_required
def get_my_tickets()
    # Return user's tickets

# Admin endpoints
@app.route('/api/admin/tickets')
@admin_required
def get_all_tickets()
    # Return all tickets with filters

@app.route('/api/admin/ticket/<ticket_id>')
@admin_required
def get_ticket_details(ticket_id)
    # Return ticket with full conversation

@app.route('/api/admin/ticket/<ticket_id>/update', methods=['POST'])
@admin_required
def update_ticket(ticket_id)
    # Update ticket status/notes
```

### Step 3: AI Chat Logic

Create `chatbot_service.py`:
```python
class SupportChatbot:
    def __init__(self):
        self.llm = ChatOpenAI(...)
        self.system_prompt = """
        You are a helpful support assistant for the AI Evaluation System.
        
        You can help with:
        - How to take evaluations
        - Understanding scores and feedback
        - Account and profile questions
        - Technical issues
        - General platform questions
        
        Be friendly, concise, and helpful.
        If the issue requires admin attention, suggest creating a support ticket.
        """
    
    def get_response(self, user_message, username, conversation_history):
        # Build context
        # Call LLM
        # Return response
    
    def should_create_ticket(self, conversation):
        # Analyze if ticket needed
        # Return True/False with reason
```

### Step 4: Frontend Chat UI (base.html)

Add floating chat button:
```html
<!-- Floating Chat Button -->
<div id="chatButton" class="chat-button">
    <i class="fas fa-comments"></i>
    <span class="chat-badge" id="chatBadge" style="display: none;">1</span>
</div>

<!-- Chat Window -->
<div id="chatWindow" class="chat-window" style="display: none;">
    <div class="chat-header">
        <h3>💬 Support Chat</h3>
        <button onclick="closeChat()">×</button>
    </div>
    <div class="chat-messages" id="chatMessages"></div>
    <div class="chat-input">
        <input type="text" id="chatInput" placeholder="Type your message...">
        <button onclick="sendMessage()">Send</button>
    </div>
</div>
```

### Step 5: Chat Styles (style.css)

```css
.chat-button {
    position: fixed;
    bottom: 2rem;
    right: 2rem;
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    z-index: 1000;
    transition: transform 0.3s ease;
}

.chat-button:hover {
    transform: scale(1.1);
}

.chat-window {
    position: fixed;
    bottom: 6rem;
    right: 2rem;
    width: 380px;
    height: 500px;
    background: var(--bg-card);
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    display: flex;
    flex-direction: column;
    z-index: 999;
}

.chat-header {
    padding: 1rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 12px 12px 0 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
}

.chat-message {
    margin-bottom: 1rem;
    padding: 0.75rem;
    border-radius: 8px;
    max-width: 80%;
}

.chat-message.user {
    background: #667eea;
    color: white;
    margin-left: auto;
}

.chat-message.bot {
    background: var(--bg-secondary);
    color: var(--text-primary);
}

.chat-input {
    display: flex;
    padding: 1rem;
    border-top: 1px solid var(--glass-border);
}

.chat-input input {
    flex: 1;
    padding: 0.75rem;
    border: 1px solid var(--glass-border);
    border-radius: 8px;
    background: var(--bg-secondary);
    color: var(--text-primary);
}

.chat-input button {
    margin-left: 0.5rem;
    padding: 0.75rem 1.5rem;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
}
```

### Step 6: Admin Ticket Dashboard (admin_dashboard.html)

Add new section:
```html
<!-- Support Tickets -->
<div class="card">
    <div class="card-header">
        <h2 class="card-title">🎫 Support Tickets</h2>
        <p class="card-subtitle">Manage user support requests</p>
    </div>
    
    <!-- Ticket filters -->
    <div class="ticket-filters">
        <button onclick="filterTickets('all')">All</button>
        <button onclick="filterTickets('open')">Open</button>
        <button onclick="filterTickets('in_progress')">In Progress</button>
        <button onclick="filterTickets('resolved')">Resolved</button>
    </div>
    
    <!-- Tickets table -->
    <table>
        <thead>
            <tr>
                <th>Ticket ID</th>
                <th>User</th>
                <th>Subject</th>
                <th>Category</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Created</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody id="ticketsTableBody">
            <!-- Populated by JavaScript -->
        </tbody>
    </table>
</div>
```

---

## Chat Flow

### Initial Greeting
```
Bot: Hi [Username]! 👋 I'm your AI support assistant.
     How can I help you today?
     
     I can assist with:
     • Taking evaluations
     • Understanding your scores
     • Account questions
     • Technical issues
     
     Just ask me anything!
```

### Example Conversation
```
User: How do I start an evaluation?

Bot: To start an evaluation:
     1. Go to your Dashboard
     2. Click "New Evaluation"
     3. Select a role
     4. Choose your skills
     5. Click "Start Evaluation"
     
     Would you like me to explain any of these steps in detail?

User: My evaluation score seems wrong

Bot: I understand your concern about the evaluation score.
     
     To help you better, could you tell me:
     1. Which role was the evaluation for?
     2. What score did you receive?
     3. What do you think went wrong?
     
     This will help me create a support ticket for admin review.

User: Python Developer, got 60% but I think I deserved more

Bot: Thank you for the details. I've collected the following:
     - Role: Python Developer
     - Score: 60%
     - Issue: Score seems incorrect
     
     Would you like me to create a support ticket for admin review?
     [Create Ticket] [Continue Chat]
```

### Ticket Creation
```
Bot: ✅ Support ticket #TKT-20250106-001 has been created!
     
     An admin will review your case and respond soon.
     You can track your ticket status in your dashboard.
     
     Is there anything else I can help you with?
```

---

## Ticket Lifecycle

1. **Created** - User creates ticket via chat
2. **Open** - Ticket awaits admin review
3. **In Progress** - Admin is working on it
4. **Resolved** - Admin has resolved the issue
5. **Closed** - Ticket is closed (by admin or auto-close)

---

## AI Knowledge Base

The chatbot should know about:
- How to register and login
- How to take evaluations
- How scoring works
- How to view results
- How to download reports
- Account management
- Technical troubleshooting
- Platform features

---

## Admin Actions

Admins can:
- View all tickets
- Filter by status/priority
- View full conversation
- Add admin notes
- Change ticket status
- Respond to user
- Close tickets
- View statistics

---

## Next Steps for Implementation

1. **Create database tables** in db_utils.py
2. **Add chatbot service** with LLM integration
3. **Create API endpoints** for chat and tickets
4. **Build chat UI** component
5. **Add admin ticket section** to dashboard
6. **Test end-to-end** flow

---

## Estimated Implementation Time

- Database & Backend: 2-3 hours
- Chat UI: 1-2 hours
- Admin Dashboard: 1-2 hours
- Testing & Polish: 1 hour
- **Total: 5-8 hours**

---

This comprehensive support system will significantly improve user experience and help admins manage support efficiently!
