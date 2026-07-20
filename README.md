# ReviseAI - AI Study Assistant

[![SDG 4 - Quality Education](https://img.shields.io/badge/SDG-4_Quality_Education-0A96D6?style=for-the-badge&logo=un&logoColor=white)](https://sdgs.un.org/goals/goal4)
[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0%2B-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0%2B-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://mysql.com)
[![Groq API](https://img.shields.io/badge/Groq%20Llama%203.3-API-F55036?style=for-the-badge&logo=groq&logoColor=white)](https://groq.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

> An intelligent study companion that generates interactive flashcards from your notes, making learning more accessible and effective for everyone.

## Table of Contents
- [Supporting SDG 4](#supporting-sustainable-development-goal-4)
- [Live Site](#live-site)
- [Tech Stack](#tech-stack)
- [Features](#features)
- [Quick Start with Docker (Recommended)](#quick-start-with-docker-recommended)
- [Manual Setup (Without Docker)](#manual-setup-without-docker)
- [Environment Variables](#environment-variables)
- [Architecture Overview](#architecture-overview)
- [API Reference](#api-reference)
- [Common Docker Commands](#common-docker-commands)
- [Troubleshooting](#troubleshooting)
- [Future Enhancements](#future-enhancements)
- [License](#license)
- [Contributing](#contributing)

## Supporting Sustainable Development Goal 4

ReviseAI directly contributes to **SDG 4: Quality Education** by:
- Making study materials creation accessible to all learners
- Providing personalized, interactive learning experiences
- Supporting both free and affordable premium education access
- Using AI to enhance educational content quality
- Promoting lifelong learning opportunities

## Live Site

[ReviseAI on PythonAnywhere](https://reviseai.pythonanywhere.com/)

## Tech Stack

### Backend
- **Python 3.11** - Core programming language
- **Flask 2.3** - Web framework with Jinja2 templating and a blueprint-based structure
- **MySQL 8.0** - Relational database with connection pooling
- **Groq API** - AI-powered question generation (`llama-3.3-70b-versatile` by default)
- **Flask-Mail** - Email functionality for contact forms
- **python-dotenv** - Environment variable management
- **Gunicorn** - Included for production-style WSGI serving

### Frontend
- **Vanilla JavaScript (ES6+)** - Client-side interactivity
- **CSS3 with Custom Properties** - Modern styling with a dark theme
- **Chart.js** - Data visualization and analytics
- **Responsive Design** - Mobile-first approach with tablet and desktop optimizations

### Infrastructure & Deployment
- **Docker & Docker Compose** - One-command local setup (app + MySQL, this repo)
- **Railway** - Cloud deployment platform (production)
- **Aiven MySQL** - Managed database with SSL (production)
- **Connection Pooling** - Optimized database performance
- **TTL Caching** - Session management with `cachetools`

### Key Libraries & Dependencies
- `mysql-connector-python` - Database connectivity
- `groq` - Groq LLM API integration
- `cachetools` - In-memory caching
- `requests` - HTTP client for API calls

## Features

### Core Functionality
- **AI-Powered Flashcard Generation**: Convert study notes into interactive quizzes using the Groq API
- **Multiple Question Types**: Support for Multiple Choice (MCQ) and True/False questions
- **Adaptive Difficulty**: Normal and Difficult question levels
- **Smart Session Management**: Save, review, and manage study sessions with detailed analytics
- **Progress Tracking**: Visual analytics with score trends and performance metrics

### Advanced Analytics
- **Performance Charts**: Score progression and time metrics using Chart.js
- **Question Type Analysis**: Breakdown of MCQ vs True/False performance
- **Difficulty Insights**: Accuracy comparison between normal and difficult questions
- **Session Duration Tracking**: Study time analytics and efficiency metrics

### User Management
- **Email-based Authentication**: Simple, password-less login with session cookies
- **Daily Session Limits**: 10 sessions per day for free tier users
- **Tier System**: Ready for premium feature expansion
- **Secure Sessions**: Flask session management with a configurable secret key

### Responsive Design
- **Mobile-First Approach**: Optimized for mobile devices
- **Tablet & Desktop Layouts**: Adaptive sidebar navigation
- **Touch & Click Support**: Universal interaction patterns
- **Landscape Optimization**: Special CSS for mobile landscape mode

---

## Quick Start with Docker (Recommended)

This is the fastest way to get ReviseAI running — a single command spins up the Flask app **and** a MySQL database, and the app automatically creates its own tables on first boot.

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) and Docker Compose (bundled with Docker Desktop, or `docker-compose-plugin` on Linux)
- A [Groq API key](https://console.groq.com) (needed for flashcard generation to work; the app will still start without one)

**1. Clone the repository**
```bash
git clone https://github.com/Polceze/ReviseAI.git
cd ReviseAI
```

**2. Configure environment variables**
```bash
cp .env.example .env
```
Open `.env` and set at least the required variables. See [Environment Variables](#environment-variables) for the full list.

**3. Build and start everything**
```bash
docker compose up --build -d
```
(On older installs the command is `docker-compose up --build`.)

That single command will:
- Build the Flask app image
- Start a MySQL 8.0 container with a persistent volume
- Wait for MySQL to become healthy before starting the app
- Create all required tables automatically on first boot
- Serve the app at **http://localhost:5000**

To view live logs in a nother terminal tab:
```bash
docker compose logs -f
```

**4. Stop the stack**
```bash
docker compose down
```
Add `-v` to also delete the MySQL data volume (a full reset): `docker compose down -v`

---

## Manual Setup (Without Docker)

If you'd rather run it directly on your machine:

### Prerequisites
- Python 3.8+
- MySQL 8.0+
- [Groq API key](https://console.groq.com) (from console.groq.com)

**1. Clone the repository**
```bash
git clone https://github.com/Polceze/ReviseAI.git
cd ReviseAI
```

**2. Set up a Python environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**3. Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your settings — in particular:
# DB_HOST=localhost (or your MySQL host)
# DB_USER, DB_PASSWORD, DB_NAME for a MySQL instance you've created yourself
# GROQ_API_KEY=your_groq_api_key
```
Note: unlike the Docker setup, you'll need to create the MySQL database and user yourself first (`CREATE DATABASE reviseai;` and a user with privileges on it) — the app only creates *tables*, not the database itself.

**4. Run the application**
```bash
# The application will automatically create tables on first run
python3 app.py
# Access at http://localhost:5000
```

---

## Environment Variables

All variables live in `.env` (see `.env.example` for a ready-to-copy template).

| Variable | Required | Description |
|---|---|---|
| `DB_HOST` | Yes (non-Docker only) | MySQL host |
| `DB_USER` | Yes | MySQL user |
| `DB_PASSWORD` | Yes | MySQL password |
| `DB_NAME` | Yes | MySQL database name |
| `DB_ROOT_PASSWORD` | Docker only | Root password for the MySQL container |
| `GROQ_API_KEY` | Yes | API key from [console.groq.com](https://console.groq.com); required for flashcard generation |
| `GROQ_MODEL` | No | Groq model used to generate questions |
| `SECRET_KEY` | Recommended | Flask session signing key; set a fixed value in production |
| `MAIL_SERVER` | No | SMTP server for the contact form |
| `MAIL_PORT` | No | SMTP port |
| `MAIL_USE_TLS` | No | Whether to use TLS for SMTP |
| `MAIL_USERNAME` | For contact form | SMTP username |
| `MAIL_PASSWORD` | For contact form | SMTP password (use an app password for Gmail) |
| `MAIL_DEFAULT_SENDER` | No | "From" address for outgoing mail |
| `CONTACT_DESTINATION_EMAIL` | No | Where contact-form submissions are delivered |
| `DEBUG` | No | Flask debug mode (only used by `python app.py`, not gunicorn) |
| `HOST` | No | Bind host |
| `PORT` | No | Bind port |

The app will fail fast at startup if any of `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` are missing.

---

## Architecture Overview
```text
ReviseAI/
├─ blueprints/
│  ├─ auth.py          # /auth/login, /auth/status, /auth/logout
│  ├─ generate.py      # /generate_questions (Groq-powered flashcard generation)
│  ├─ sessions.py      # /save_flashcards, /get_sessions, /get_flashcards, /delete_session, /list_sessions
│  ├─ analytics.py     # /type-difficulty, /progress-data, /chart-data, etc.
│  ├─ contact.py       # /contact (GET page, POST submission)
│  └─ pages.py         # /, /analytics, /sessions, /donate, /upgrade (template routes)
├─ services/
│  ├─ ai_service.py       # Groq prompt building, response parsing, answer balancing
│  ├─ session_service.py  # Daily session limits, TTL caching of allowance data
│  └─ email_service.py    # Async email sending via Flask-Mail
├─ static/
│  ├─ css/              # base/layout/desktop/tablet + components + pages
│  └─ js/                # analytics.js, auth.js, flashcards.js, sessions.js, ui.js, utils.js
├─ templates/            # Jinja2 templates (index, sessions, analytics, contact, donate)
├─ app.py                # App bootstrap, auth middleware, user/tier routes
├─ config.py             # Centralized env-based configuration
├─ models.py             # Database class: connection pooling + schema creation + queries
├─ requirements.txt
├─ Dockerfile
├─ docker-compose.yml
├─ docker-entrypoint.sh  # Waits for MySQL to be reachable before starting Flask
├─ .env.example
└─ README.md
```

### Architecture Decisions
- **Modular CSS:** Scalable styling system with design tokens
- **RESTful API:** Clean separation between frontend and backend
- **Progressive Enhancement:** Core functionality works without JavaScript
- **Security:** Session-based auth middleware in `app.py`, with public routes explicitly allow-listed
- **Self-migrating schema:** `models.py` creates all tables on startup, so there's no separate migration step to run

### Scalability Features
- **Database Pooling:** Handles concurrent users efficiently (`MySQLConnectionPool`, pool size 5)
- **Caching Layer:** TTL cache reduces database load for frequent session-allowance checks
- **Modular Architecture:** Easy to extend with new question types or AI providers
- **Environment Configuration:** Ready for different deployment scenarios (local, Docker, Railway)

---

## API Reference

All endpoints return JSON except the page routes in `pages.py`, which render HTML templates.

| Method | Path | Blueprint | Description |
|---|---|---|---|
| POST | `/auth/login` | auth | Email-only login; creates the user if new |
| GET | `/auth/status` | auth | Returns current auth state |
| GET | `/auth/logout` | auth | Clears the session |
| POST | `/generate_questions` | generate | Generates flashcards from submitted notes via Groq |
| POST | `/save_flashcards` | sessions | Saves a completed study session |
| GET | `/get_sessions` | sessions | Lists saved sessions for the current user |
| GET | `/get_flashcards/<session_id>` | sessions | Fetches flashcards for a specific session |
| DELETE | `/delete_session/<session_id>` | sessions | Deletes a saved session |
| GET | `/list_sessions` | sessions | Lists sessions (used by the sessions page) |
| GET | `/type-difficulty` | analytics | Question-type/difficulty breakdown |
| POST | `/type-difficulty-filtered` | analytics | Filtered breakdown by date range/type |
| GET | `/progress-data` | analytics | Score progression over time |
| GET | `/chart-data` | analytics | Aggregated data for Chart.js dashboards |
| GET/POST | `/contact` | contact | Contact page / form submission (sends email) |
| GET | `/user/tier-info` | app.py | Current tier, daily limit, and usage |
| GET | `/user/session-allowance` | app.py | Remaining sessions for today |
| GET | `/user/session-count` | app.py | Sessions used today |
| GET | `/debug/pool-status` | app.py | DB connection pool health |
| GET | `/debug/email-config` | app.py | Confirms which mail env vars are set (not their values) |

Routes not in the public allow-list (`/`, `/contact`, `/donate`, `/upgrade`, `/auth/*`, `/static/*`) require an active session; API/JSON requests without one receive a `401`.

---

## Common Docker Commands

```bash
# Rebuild containers
docker compose up --build

# View logs
docker compose logs -f

# Run a one-off shell in the app container
docker compose exec web bash

# Open a MySQL shell inside the db container
docker compose exec db mysql -u user -p password

# Stop and remove containers (keeps data volume)
docker compose down

# Stop and remove containers + data volume (full reset)
docker compose down -v
```

## Troubleshooting

- **`web` container keeps restarting / "Database failed to initialize"**: usually means MySQL wasn't ready in time or the `.env` DB credentials don't match. Check `docker compose logs db` and confirm `DB_USER`/`DB_PASSWORD`/`DB_NAME` match what's in `.env` on both services.
- **Flashcard generation fails / returns an error**: confirm `GROQ_API_KEY` is set correctly in `.env` and that you rebuilt/restarted after changing it (`docker compose up --build`).
- **Contact form doesn't send email**: Gmail requires an [App Password](https://support.google.com/accounts/answer/185833), not your normal password, for `MAIL_PASSWORD`.
- **Port 5000 or 3306 already in use**: change the left-hand side of the `ports` mapping in `docker-compose.yml`, e.g. `"5001:5000"`.
- **Changes to `.env` aren't picked up**: environment variables are read at container start; run `docker compose up --build` (or at least `docker compose restart web`) after editing `.env`.

## Future Enhancements
- **Collaborative Features:** Study groups and shared sessions
- **Export Capabilities:** PDF and Anki deck exports
- **Multi-modal AI:** Image and document processing
- **Advanced Analytics:** Machine learning insights on study patterns

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
Feel free to use this project for learning and development purposes.

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

---

Built with ❤️ for accessible education and technical excellence
