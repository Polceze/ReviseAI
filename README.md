# ReviseAI - AI Study Assistant 🎓

[![SDG 4 - Quality Education](https://img.shields.io/badge/SDG-4_Quality_Education-0A96D6?style=for-the-badge&logo=un&logoColor=white)](https://sdgs.un.org/goals/goal4)
[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0%2B-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0%2B-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://mysql.com)
[![Claude 3 Haiku API](https://img.shields.io/badge/Claude%203%20Haiku-API-6B4EFF?style=for-the-badge&logo=anthropic&logoColor=white)](https://www.anthropic.com/claude)
[![PythonAnywhere](https://img.shields.io/badge/Hosted%20on-PythonAnywhere-306998?style=for-the-badge&logo=python&logoColor=white)](https://www.pythonanywhere.com/)


> An intelligent study companion that generates interactive flashcards from your notes, making learning more accessible and effective for everyone.

## Supporting Sustainable Development Goal 4

ReviseAI directly contributes to **SDG 4: Quality Education** by:
- Making study materials creation accessible to all learners
- Providing personalized, interactive learning experiences
- Supporting both free and affordable premium education access
- Using AI to enhance educational content quality
- Promoting lifelong learning opportunities

## Live Demo

**Live Application:** [ReviseAI on Render](https://reviseai.onrender.com)

## 🛠️ Tech Stack

### Backend
- **Python 3.8+** - Core programming language
- **Flask 2.0+** - Web framework with Jinja2 templating
- **MySQL 8.0+** - Relational database with connection pooling
- **Anthropic Claude API** - AI-powered question generation (claude-3-haiku model)
- **Flask-Mail** - Email functionality for contact forms
- **python-dotenv** - Environment variable management

### Frontend
- **Vanilla JavaScript (ES6+)** - Client-side interactivity
- **CSS3 with Custom Properties** - Modern styling with dark theme
- **Chart.js** - Data visualization and analytics
- **Responsive Design** - Mobile-first approach with tablet and desktop optimizations

### Infrastructure & Deployment
- **Railway** - Cloud deployment platform
- **Aiven MySQL** - Managed database with SSL
- **Connection Pooling** - Optimized database performance
- **TTL Caching** - Session management with cachetools

### Key Libraries & Dependencies
- `mysql-connector-python` - Database connectivity
- `anthropic` - Claude AI API integration
- `cachetools` - In-memory caching
- `requests` - HTTP client for API calls

## Features

### 🎯 Core Functionality
- **AI-Powered Flashcard Generation**: Convert study notes into interactive quizzes using Anthropic Claude AI
- **Multiple Question Types**: Support for Multiple Choice (MCQ) and True/False questions
- **Adaptive Difficulty**: Normal and Difficult question levels
- **Smart Session Management**: Save, review, and manage study sessions with detailed analytics
- **Progress Tracking**: Visual analytics with score trends and performance metrics

### 📊 Advanced Analytics
- **Performance Charts**: Score progression and time metrics using Chart.js
- **Question Type Analysis**: Breakdown of MCQ vs True/False performance
- **Difficulty Insights**: Accuracy comparison between normal and difficult questions
- **Session Duration Tracking**: Study time analytics and efficiency metrics

### 🔐 User Management
- **Email-based Authentication**: Simple login with session management
- **Daily Session Limits**: 10 sessions per day for free tier users
- **Tier System**: Ready for premium feature expansion
- **Secure Sessions**: Flask session management with secret key

### 📱 Responsive Design
- **Mobile-First Approach**: Optimized for mobile devices
- **Tablet & Desktop Layouts**: Adaptive sidebar navigation
- **Touch & Click Support**: Universal interaction patterns
- **Landscape Optimization**: Special CSS for mobile landscape mode

## Architecture Overview
```text
AI-study-buddy/
├─ static/
│  ├─ css/
│  │  ├─ components/
│  │  │  ├─ buttons.css
│  │  │  ├─ cards.css
│  │  │  ├─ charts.css
│  │  │  ├─ forms.css
│  │  │  ├─ modals.css
│  │  │  └─ navigation.css
│  │  ├─ pages/
│  │  │  ├─ analytics.css
│  │  │  ├─ contact.css
│  │  │  ├─ donate.css
│  │  │  ├─ home.css
│  │  │  └─ sessions.css
│  │  ├─ base.css
│  │  ├─ desktop.css
│  │  ├─ layout.css
│  │  ├─ rotation.css
│  │  └─ tablet.css
│  ├─ images/
│  └─ js/
│     └─ script.js
├─ templates/
│  ├─ analytics.html
│  ├─ base.html
│  ├─ contact.html
│  ├─ donate.html
│  ├─ index.html
│  └─ sessions.html
├─ .env
├─ .gitignore
├─ app.py
├─ config.py
├─ models.py
├─ README.md
└─ requirements.txt
```

### Architecture Decisions
- **Modular CSS:** Scalable styling system with design tokens
- **RESTful API:** Clean separation between frontend and backend
- **Progressive Enhancement:** Core functionality works without JavaScript
- **Security:** Implemented proper session management and input validation

### Scalability Features
- **Database Pooling:** Handles concurrent users efficiently
- **Caching Layer:** Reduces database load for frequent queries
- **Modular Architecture:** Easy to extend with new question types or AI providers
- **Environment Configuration:** Ready for different deployment scenarios

## Quick Start

### Prerequisites
- Python 3.8+
- MySQL 8.0+
- Anthropic Claude API key
- Render account (for deployment)

### Installation
#### 1. Clone the repository
```bash
git clone https://github.com/Polceze/AI-Study-Assistant-Project.git
cd ReviseAI
```

#### 2. Set up Python environment

```bash 
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 3. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your settings:
# ANTHROPIC_API_KEY=your_claude_api_key
# DB_HOST=your_mysql_host
# DB_USER=your_mysql_user
# DB_PASSWORD=your_mysql_password
# DB_NAME=reviseai
# SECRET_KEY=your_flask_secret_key
```

#### 4.Initialize database
```bash
# The application will automatically create tables on first run
python app.py
```

#### 5. Run the application
```bash
python app.py
# Access at http://localhost:5000
```

## Deployment

### Backend Deployment on Render

1. **Connect your repository** to Render
2. **Create a Web Service** with the following settings:
   - **Build Command:** pip install -r requirements.txt
   - **Start Command:** python app.py
   - **Environment:** Python 3.8+
3. Set environment variables in Render dashboard:

```text
ANTHROPIC_API_KEY=your_claude_api_key
SECRET_KEY=your_flask_secret_key
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
```

### Database Setup with Aiven
**1. Create Aiven account** at aiven.io
**2. Create MySQL service:**
   - **Select MySQL 8.0** as service type
   - Choose your preferred cloud provider and region
   - Select appropriate plan based on your needs
**3. Get connection details** from Aiven console:
   - Host, Port, Database name, Username, Password
**4. Set database environment variables** in Render:
```text
DB_HOST=your-aiven-mysql-host.aivencloud.com
DB_PORT=your-mysql-port
DB_NAME=defaultdb
DB_USER=avnadmin
DB_PASSWORD=your-aiven-password
```

### Automatic Deployment
- **Continuous Deployment:** Render automatically deploys on git push to main branch
- **Build Logs:** Monitor build process in Render dashboard
- **Health Checks:** Render provides automatic health monitoring
- **Custom Domains:** Add your custom domain in Render settings

### Environment Configuration
Create a `.env` file for local development or set these in Render environment variables:

```env
# AI Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Database Configuration (Aiven MySQL)
DB_HOST=your-aiven-host.aivencloud.com
DB_PORT=2768
DB_NAME=defaultdb
DB_USER=avnadmin
DB_PASSWORD=your_aiven_password

# Flask Configuration
SECRET_KEY=your_secret_key_here
DEBUG=False

# Email Configuration (Optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
```

## 🔧 Key Features Implementation

### AI-Powered Question Generation
```python
def generate_questions_with_claude(notes, num_questions=6, question_type="mcq", difficulty="normal"):
    # Uses Anthropic Claude API with optimized prompts
    # Includes answer balancing and validation
```

### Database Connection Pooling
```python
class Database:
    def __init__(self):
        self.pool = MySQLConnectionPool(
            pool_name="reviseAI_pool",
            pool_size=5,
            pool_reset_session=True,
            **self.config
        )
```

### Real-time Analytics
```javascript
function initAllCharts() {
    progressChart = initProgressChart();
    trendsChart = initTrendsChart();
    // Multiple Chart.js instances for comprehensive analytics
}
```
### Future Enhancements
- **Spaced Repetition:** Algorithm-based review scheduling
- **Collaborative Features:** Study groups and shared sessions
- **Export Capabilities:** PDF and Anki deck exports
- **Multi-modal AI:** Image and document processing
- **Advanced Analytics:** Machine learning insights on study patterns

## 📄 License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details. 
Feel free to use this project for learning and development purposes.

## 🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

---
---


Built with ❤️ for accessible education and technical excellence




