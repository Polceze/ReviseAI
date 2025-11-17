import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # # Basic configuration
    # SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-for-study-buddy'
    
    # # Database configuration
    # DB_HOST = os.environ.get('DB_HOST') or 'localhost'
    # DB_USER = os.environ.get('DB_USER') or 'reviseAI_user'
    # DB_PASSWORD = os.environ.get('DB_PASSWORD') or 'password123'
    # DB_NAME = os.environ.get('DB_NAME') or 'reviseAI_DB'

    # MySQL configuration - will use environment variables
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_NAME = os.environ.get('DB_NAME', 'reviseai')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', True)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Anthropic Claude API
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
    
    # Contact form destination
    CONTACT_DESTINATION_EMAIL = os.environ.get('CONTACT_DESTINATION_EMAIL')
