"""
AI Support Chatbot Service
Handles chat interactions and determines when to create support tickets
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
from dotenv import load_dotenv
import logging

load_dotenv()

class SupportChatbot:
    def __init__(self):
        """Initialize the support chatbot with LLM"""
        self.llm = ChatOpenAI(
            model="deepseek-chat",
            temperature=0.7,
            api_key=os.getenv('DEEPSEEK_API_KEY'),
            base_url="https://api.deepseek.com"
        )
        
        self.system_prompt = """You are a helpful and friendly support assistant for the AI Evaluation System.

**Your Role:**
- Help users with questions about the platform
- Provide clear, concise answers
- Be empathetic and professional
- Guide users through processes

**You can help with:**
1. **Taking Evaluations**
   - How to start an evaluation
   - Choosing roles and skills
   - Understanding the evaluation process
   - Time limits and question formats

2. **Understanding Results**
   - How scoring works
   - Interpreting feedback
   - Viewing evaluation history
   - Downloading reports

3. **Account Management**
   - Profile settings
   - Email updates
   - Password issues
   - Attempt limits

4. **Technical Issues**
   - Login problems
   - Evaluation not loading
   - Results not showing
   - Download issues

5. **General Platform Questions**
   - Available roles
   - Evaluation attempts
   - Feedback system
   - Admin contact

**Important Guidelines:**
- Keep responses concise (2-4 sentences)
- Use bullet points for lists
- Be encouraging and supportive
- If the issue requires admin attention (account issues, score disputes, technical bugs), suggest creating a support ticket
- Don't make promises you can't keep
- Don't provide information about other users

**Tone:** Friendly, professional, helpful, and encouraging.
"""
    
    def get_response(self, user_message: str, username: str, conversation_history: list = None) -> str:
        """
        Get chatbot response to user message
        
        Args:
            user_message: The user's message
            username: Username of the person chatting
            conversation_history: List of previous messages [{'role': 'user'/'assistant', 'content': '...'}]
        
        Returns:
            Chatbot's response
        """
        try:
            # Build conversation context
            messages = [
                ("system", self.system_prompt),
                ("system", f"You are chatting with user: {username}")
            ]
            
            # Add conversation history
            if conversation_history:
                for msg in conversation_history[-6:]:  # Last 6 messages for context
                    if msg['role'] == 'user':
                        messages.append(("human", msg['content']))
                    else:
                        messages.append(("assistant", msg['content']))
            
            # Add current message
            messages.append(("human", user_message))
            
            # Create prompt and get response
            prompt = ChatPromptTemplate.from_messages(messages)
            chain = prompt | self.llm | StrOutputParser()
            
            response = chain.invoke({})
            
            return response
            
        except Exception as e:
            logging.error(f"Error getting chatbot response: {e}")
            return "I apologize, but I'm having trouble responding right now. Please try again or create a support ticket for assistance."
    
    def should_create_ticket(self, conversation_history: list) -> dict:
        """
        Analyze conversation to determine if a support ticket should be created
        
        Args:
            conversation_history: List of messages in the conversation
        
        Returns:
            dict with 'should_create': bool, 'reason': str, 'category': str, 'priority': str
        """
        try:
            # Keywords that suggest ticket creation
            ticket_keywords = {
                'urgent': ['urgent', 'emergency', 'critical', 'immediately', 'asap'],
                'account': ['account', 'login', 'password', 'access', 'locked', 'banned'],
                'technical': ['bug', 'error', 'broken', 'not working', 'crash', 'freeze'],
                'score': ['score', 'wrong', 'incorrect', 'unfair', 'dispute', 'review'],
                'complaint': ['complaint', 'unhappy', 'disappointed', 'frustrated', 'angry']
            }
            
            # Analyze last few messages
            recent_messages = ' '.join([msg['content'].lower() for msg in conversation_history[-4:]])
            
            # Check for ticket keywords
            found_categories = []
            for category, keywords in ticket_keywords.items():
                if any(keyword in recent_messages for keyword in keywords):
                    found_categories.append(category)
            
            # Determine if ticket should be created
            should_create = len(found_categories) > 0
            
            if should_create:
                # Determine priority
                priority = 'high' if 'urgent' in found_categories else 'medium'
                
                # Determine category
                if 'technical' in found_categories:
                    category = 'technical'
                elif 'account' in found_categories:
                    category = 'account'
                elif 'score' in found_categories:
                    category = 'evaluation'
                else:
                    category = 'general'
                
                return {
                    'should_create': True,
                    'reason': f"Issue detected: {', '.join(found_categories)}",
                    'category': category,
                    'priority': priority
                }
            
            return {
                'should_create': False,
                'reason': 'General inquiry, no ticket needed',
                'category': 'general',
                'priority': 'low'
            }
            
        except Exception as e:
            logging.error(f"Error analyzing conversation for ticket: {e}")
            return {
                'should_create': False,
                'reason': 'Error analyzing conversation',
                'category': 'general',
                'priority': 'low'
            }
    
    def generate_ticket_subject(self, conversation_history: list) -> str:
        """
        Generate a concise subject line for a support ticket based on conversation
        
        Args:
            conversation_history: List of messages
        
        Returns:
            Subject line string
        """
        try:
            # Get last user message as basis for subject
            user_messages = [msg['content'] for msg in conversation_history if msg['role'] == 'user']
            
            if user_messages:
                last_message = user_messages[-1]
                
                # Truncate if too long
                if len(last_message) > 60:
                    subject = last_message[:57] + "..."
                else:
                    subject = last_message
                
                return subject
            
            return "Support Request"
            
        except Exception as e:
            logging.error(f"Error generating ticket subject: {e}")
            return "Support Request"


# Global chatbot instance
chatbot = SupportChatbot()
