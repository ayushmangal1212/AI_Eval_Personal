# 🤖 AI-Powered Evaluation System

An intelligent, automated candidate evaluation platform powered by AI that streamlines technical assessments with real-time feedback, resume parsing, voice input, and comprehensive analytics.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## ✨ Features

### 🎯 **Core Features**
- **AI-Powered Question Generation** - Dynamic questions tailored to role and skills
- **Real-time Evaluation** - Instant AI feedback on answers
- **Multiple Question Types** - Conceptual and coding challenges
- **Role-Based Assessments** - Python, Java, Frontend, DevOps, Data Engineer, DBA
- **Comprehensive Dashboard** - Track progress and view detailed results

### 🚀 **Advanced Features**
- **📄 Resume Parsing** - Automatic skill extraction and role suggestion
- **🎤 Voice Input** - Speech-to-text for answering questions
- **📊 Analytics Dashboard** - Performance insights and trends
- **💬 Feedback System** - Challenge AI evaluations
- **📧 Email Notifications** - Automated evaluation reports
- **🔒 Admin Panel** - User management and oversight

---

## 🖼️ Screenshots

### Dashboard
![Dashboard](https://via.placeholder.com/800x400?text=Dashboard+Screenshot)

### Evaluation Interface
![Evaluation](https://via.placeholder.com/800x400?text=Evaluation+Interface)

### Results & Feedback
![Results](https://via.placeholder.com/800x400?text=Results+Page)

---

## 🛠️ Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **AI**: DeepSeek AI (via LangChain)
- **Frontend**: HTML, CSS, JavaScript
- **Speech Recognition**: Web Speech API
- **Document Parsing**: PyPDF2, python-docx

---

## 📋 Prerequisites

- Python 3.8 or higher
- DeepSeek API key ([Get one here](https://platform.deepseek.com/))
- Modern web browser (Chrome, Edge, Safari)

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ai-evaluation-system.git
cd ai-evaluation-system
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/Mac
```

### 3. Install Dependencies

```bash
pip install -r requirements_flask.txt
```

### 4. Configure Environment

Create a `.env` file in the root directory:

```env
DEEPSEEK_API_KEY=your-api-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-reasoner
SECRET_KEY=your-secret-key-here
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

### 5. Run the Application

**Windows**:
```bash
start_flask.bat
```

**Linux/Mac**:
```bash
python app.py
```

### 6. Access the Application

Open your browser and navigate to:
```
http://localhost:5000
```

---

## 📚 Documentation

### User Guides
- [Setup Guide](docs/README_FLASK.md)
- [Resume Parsing Guide](docs/RESUME_INTEGRATION_COMPLETE.md)
- [Voice Input Guide](docs/VOICE_INPUT_FEATURE.md)
- [Feedback System Guide](docs/FEEDBACK_SYSTEM_GUIDE.md)

### Admin Guides
- [Admin Dashboard](docs/ENHANCEMENTS_DOCUMENTATION.md)
- [Analytics Overview](docs/ENHANCEMENTS_DOCUMENTATION.md#analytics)

---

## 🎯 Usage

### For Candidates

1. **Register** - Create an account (optional: upload resume)
2. **Start Evaluation** - Select role and skills
3. **Answer Questions** - Type or use voice input
4. **Get Results** - Instant AI feedback and scoring
5. **Submit Feedback** - Challenge evaluations if needed

### For Admins

1. **Login** - Access admin panel at `/admin/login`
2. **View Analytics** - Monitor performance trends
3. **Manage Users** - View and manage candidates
4. **Review Feedback** - Address user concerns

---

## 🔧 Configuration

### Switching Between Dummy and AI Questions

For testing (instant questions):
- Questions are pre-defined in `app.py`
- No API calls, instant loading

For production (AI-generated):
- Edit `app.py` line ~182
- Uncomment LLM generation section
- Comment out dummy questions section

### Supported Roles

- Python Developer
- Java Developer
- Frontend Developer
- DevOps Engineer
- Data Engineer
- Database Administrator

---

## 📊 Database Schema

### Users Table
- `username`, `password_hash`, `email`, `full_name`
- `skills` (comma-separated), `created_at`

### Evaluations Table
- `username`, `role`, `score`, `percentage`
- `time_taken`, `qa_history` (JSON), `date`

### Feedback Table
- `user_id`, `question_text`, `user_answer`
- `ai_score`, `user_feedback`, `status`

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 🐛 Known Issues

- Voice input not supported in Firefox
- Resume parsing works best with PDF and DOCX formats
- LLM responses may vary in format (fallback questions available)

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Your Name**
- GitHub: [@yourusername](https://github.com/yourusername)
- Email: your.email@example.com

---

## 🙏 Acknowledgments

- [DeepSeek AI](https://www.deepseek.com/) for AI capabilities
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [LangChain](https://www.langchain.com/) for LLM integration

---

## 📞 Support

For support, email your.email@example.com or open an issue on GitHub.

---

## 🗺️ Roadmap

- [ ] Multi-language support
- [ ] Video proctoring integration
- [ ] Advanced code execution sandbox
- [ ] Real-time collaboration features
- [ ] Mobile app version
- [ ] Integration with ATS systems

---

**⭐ If you find this project useful, please consider giving it a star!**
