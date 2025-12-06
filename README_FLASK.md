# 🤖 AI-Powered Candidate Evaluation System - Flask Edition

A beautiful, modern Flask web application for AI-driven technical interviews with real-time assessment and intelligent feedback.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)
![LangChain](https://img.shields.io/badge/LangChain-0.1.0-purple.svg)
![DeepSeek](https://img.shields.io/badge/DeepSeek-AI-orange.svg)

## ✨ What's New in Flask Version

### 🎨 Premium Design
- **Modern Glassmorphism UI** - Stunning frosted glass effects with backdrop blur
- **Vibrant Gradients** - Eye-catching color schemes throughout the interface
- **Smooth Animations** - Micro-interactions and transitions for enhanced UX
- **Floating Particles** - Dynamic background animations
- **Responsive Design** - Perfect on all devices and screen sizes

### 🚀 Enhanced Features
- **Beautiful Landing Page** - Impressive hero section with feature showcase
- **Interactive Dashboard** - Animated stats and progress tracking
- **Real-time Timers** - Countdown timers with visual feedback
- **Modern Forms** - Sleek input fields with validation feedback
- **Admin Panel** - Comprehensive user and evaluation management

### 💎 Design Highlights
- Custom color palette with HSL-based gradients
- Google Fonts (Inter & Poppins) for premium typography
- Font Awesome icons for visual clarity
- Smooth scroll animations and entrance effects
- Progress bars with shimmer animations
- Badge system for status indicators

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- DeepSeek API key ([Get one here](https://platform.deepseek.com/))

### Installation

1. **Navigate to the project directory**
```bash
cd AI_Eval-main
```

2. **Install dependencies**
```bash
pip install -r requirements_flask.txt
```

3. **Set up environment variables**
Create a `.env` file in the root directory:
```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
SECRET_KEY=your-secret-key-for-flask-sessions
ADMIN_USERNAME=admin
ADMIN_PASSWORD=Admin@123
```

4. **Run the Flask application**
```bash
python app.py
```

5. **Open in browser**
Navigate to `http://localhost:5000`

## 📋 Usage Guide

### For Candidates

1. **Register/Login**
   - Create a new account with username, email, and password
   - Or login with existing credentials
   - Beautiful animated forms with real-time validation

2. **Dashboard**
   - View your evaluation statistics
   - Track average scores and performance
   - Review complete evaluation history
   - Animated stats cards and progress bars

3. **Start Evaluation**
   - Select your role from 6 available options
   - Enter technical skills (comma-separated)
   - Choose preferred language
   - Get AI-generated questions tailored to your profile

4. **Complete Assessment**
   - Answer 5 questions (3 conceptual + 2 coding)
   - Real-time countdown timers
   - Text-to-speech for questions
   - Submit or skip questions
   - Instant AI evaluation

5. **View Results**
   - Detailed score breakdown
   - Performance percentage
   - Time taken
   - AI-generated recommendations
   - Export or share results

### For Administrators

1. **Admin Login**
   - Access at `/admin/login`
   - Use admin credentials from `.env`

2. **Admin Dashboard**
   - View all registered users
   - Monitor evaluation statistics
   - Track system performance
   - Review feedback entries

## 🎯 Supported Roles

- ☕ **Java Developer** - Spring Boot, Concurrency, REST APIs
- 🗄️ **Database Administrator** - PostgreSQL, MySQL, Performance Tuning
- 🎨 **Frontend Developer** - React, Vue, Angular, Responsive Design
- 🚀 **DevOps Engineer** - Docker, Kubernetes, CI/CD, Terraform
- 📊 **Data Engineer** - Spark, Airflow, ETL, Data Pipelines
- 🐍 **Python Developer** - Flask, Django, APIs, Data Structures

## 🛠️ Technology Stack

### Backend
- **Flask 3.0.0** - Modern Python web framework
- **LangChain** - LLM orchestration
- **DeepSeek AI** - Advanced reasoning model
- **SQLite** - Database (via db_utils)

### Frontend
- **HTML5** - Semantic markup
- **CSS3** - Custom design system with variables
- **Vanilla JavaScript** - No framework dependencies
- **Font Awesome** - Icon library
- **Google Fonts** - Inter & Poppins

### Design Features
- CSS Variables for theming
- Glassmorphism effects
- CSS Grid & Flexbox layouts
- CSS Animations & Transitions
- Responsive breakpoints

## 📁 Project Structure

```
AI_Eval-main/
├── app.py                      # Flask application
├── db_utils.py                 # Database utilities
├── requirements_flask.txt      # Python dependencies
├── .env                        # Environment variables
├── templates/                  # HTML templates
│   ├── base.html              # Base template
│   ├── index.html             # Landing page
│   ├── login.html             # User login
│   ├── register.html          # User registration
│   ├── dashboard.html         # User dashboard
│   ├── evaluation.html        # Evaluation interface
│   ├── admin_login.html       # Admin login
│   └── admin_dashboard.html   # Admin panel
├── static/                     # Static assets
│   ├── css/
│   │   └── style.css          # Main stylesheet
│   └── js/
│       └── (future JS files)
└── README_FLASK.md            # This file
```

## 🎨 Design System

### Color Palette
- **Primary**: `#667eea` → `#764ba2` (Purple gradient)
- **Secondary**: `#f093fb` → `#f5576c` (Pink gradient)
- **Success**: `#4facfe` → `#00f2fe` (Blue gradient)
- **Warning**: `#fa709a` → `#fee140` (Orange gradient)

### Typography
- **Headings**: Poppins (700-800 weight)
- **Body**: Inter (400-600 weight)
- **Code**: Courier New (monospace)

### Spacing Scale
- XS: 0.5rem (8px)
- SM: 1rem (16px)
- MD: 1.5rem (24px)
- LG: 2rem (32px)
- XL: 3rem (48px)

## 🔧 Configuration

### Environment Variables
```env
DEEPSEEK_API_KEY=sk-...           # Required: Your DeepSeek API key
SECRET_KEY=random-secret-key       # Required: Flask session secret
DEEPSEEK_BASE_URL=https://...     # Optional: Custom API endpoint
DEEPSEEK_MODEL=deepseek-reasoner   # Optional: Model name
ADMIN_USERNAME=admin               # Optional: Admin username
ADMIN_PASSWORD=Admin@123           # Optional: Admin password
```

### Customization
Edit `static/css/style.css` to customize:
- Color schemes (CSS variables)
- Typography and fonts
- Spacing and sizing
- Animation timings
- Responsive breakpoints

## 🌟 Key Features

### User Experience
- ✨ Stunning visual design with modern aesthetics
- 🎭 Smooth animations and micro-interactions
- 📱 Fully responsive across all devices
- ⚡ Fast loading with optimized assets
- 🎨 Consistent design language

### Technical Capabilities
- 🤖 AI-powered question generation
- 📊 Real-time answer evaluation
- ⏱️ Countdown timers with auto-submit
- 🔊 Text-to-speech for questions
- 💾 Persistent data storage
- 🔐 Secure authentication
- 👨‍💼 Admin management panel

## 🐛 Troubleshooting

### Common Issues

**Port already in use**
```bash
# Change port in app.py
app.run(debug=True, port=5001)
```

**API Key errors**
- Verify `.env` file exists in root directory
- Check API key is valid and has credits
- Ensure no extra spaces in `.env` file

**Database errors**
- Ensure `db_utils.py` is in the same directory
- Check file permissions for database files
- Run `python migrate_to_db.py` if needed

**CSS not loading**
- Clear browser cache (Ctrl+Shift+R)
- Check Flask static folder configuration
- Verify file paths in templates

## 🚀 Deployment

### Production Checklist
- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Update `ADMIN_PASSWORD` to a secure password
- [ ] Set `debug=False` in `app.py`
- [ ] Use production WSGI server (Gunicorn, uWSGI)
- [ ] Configure HTTPS/SSL
- [ ] Set up proper database (PostgreSQL)
- [ ] Enable CORS if needed
- [ ] Configure logging
- [ ] Set up monitoring

### Example with Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- DeepSeek for the powerful AI API
- Flask for the excellent web framework
- LangChain for LLM orchestration
- Font Awesome for beautiful icons
- Google Fonts for premium typography

## 📧 Support

For questions or issues, please open an issue on GitHub.

---

Made with ❤️ using DeepSeek AI and Flask | Converted from Streamlit with enhanced design
