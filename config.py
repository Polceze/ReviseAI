import os
from urllib.parse import urlparse

class Config:
    # Basic configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-for-study-buddy'

    # Database configuration for Railway
    if os.environ.get('MYSQL_URL'):
        # Parse Railway's MYSQL_URL
        db_url = urlparse(os.environ.get('MYSQL_URL'))
        DB_HOST = db_url.hostname
        DB_USER = db_url.username
        DB_PASSWORD = db_url.password
        DB_NAME = db_url.path[1:]  # Remove leading slash
        DB_PORT = db_url.port or 3306
    else:    
        # Database configuration
        DB_HOST = os.environ.get('DB_HOST') or 'localhost'
        DB_USER = os.environ.get('DB_USER') or 'reviseAI_user'
        DB_PASSWORD = os.environ.get('DB_PASSWORD') or 'password123'
        DB_NAME = os.environ.get('DB_NAME') or 'reviseAI_DB'
    
    # Anthropic Claude API (your current AI provider)
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY') or ''

    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', MAIL_USERNAME)
    
    # Contact form destination
    CONTACT_DESTINATION_EMAIL = os.environ.get('CONTACT_DESTINATION_EMAIL', MAIL_USERNAME)