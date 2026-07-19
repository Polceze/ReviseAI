from flask import Flask, jsonify, session, request
from flask_mail import Mail
import os
from dotenv import load_dotenv
from models import Database
from services.session_service import SessionService
from services.email_service import EmailService

# Import blueprints
from blueprints import (
    auth_bp, generate_bp, sessions_bp, 
    analytics_bp, contact_bp, pages_bp
)

load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or os.urandom(24).hex()

# Configure email
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME'])

mail = Mail(app)

# Initialize database
db = Database()
if not db or not db.pool:
    raise RuntimeError("Database failed to initialize")

# Initialize services (making them available to blueprints via app context)
session_service = SessionService(db)
email_service = EmailService(mail, app.config['MAIL_DEFAULT_SENDER'])

# Make services available to blueprints
app.db = db
app.session_service = session_service
app.email_service = email_service

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(generate_bp)
app.register_blueprint(sessions_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(contact_bp)
app.register_blueprint(pages_bp)

# Auth middleware
@app.before_request
def require_auth():
    # Public routes (no auth required)
    public_routes = ['/', '/static/', '/contact', '/donate', '/upgrade']
    public_prefixes = ('/auth/', '/static/')
    
    if request.path in public_routes or request.path.startswith(public_prefixes):
        return None
    
    # Check authentication
    if 'user_id' not in session:
        if request.path.startswith('/api/') or request.is_json:
            return jsonify({"status": "error", "message": "Authentication required"}), 401
        return None  # Frontend will handle auth modal
    
    return None

# Debug routes
@app.route('/debug/pool-status')
def debug_pool_status():
    return jsonify({
        "status": "success",
        "pool_status": "Pool working" if db.pool else "Pool failed",
        "pool_size": getattr(db.pool, 'pool_size', 'No pool')
    })

@app.route('/debug/email-config')
def debug_email_config():
    return jsonify({
        'MAIL_SERVER': app.config.get('MAIL_SERVER'),
        'MAIL_PORT': app.config.get('MAIL_PORT'),
        'MAIL_USERNAME': 'SET' if app.config.get('MAIL_USERNAME') else 'MISSING',
        'MAIL_PASSWORD': 'SET' if app.config.get('MAIL_PASSWORD') else 'MISSING',
    })

# User info routes
@app.route('/user/tier-info')
def user_tier_info():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({
            "status": "success",
            "tier_info": {
                "tier": "free",
                "remaining_sessions": 10,
                "session_limit": 10,
                "sessions_used_today": 0,
                "reset_in": "midnight",
                "billing_period": "daily",
                "total_sessions_used": 0
            }
        })
    
    allowance = session_service.check_daily_limit(user_id)
    
    # Get total sessions
    conn = db.get_connection()
    total_sessions = 0
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT total_sessions_used FROM users WHERE id = %s", (user_id,))
        user_data = cursor.fetchone()
        total_sessions = user_data.get('total_sessions_used', 0) if user_data else 0
        cursor.close()
        conn.close()
    
    return jsonify({
        "status": "success",
        "tier_info": {
            "tier": "free",
            "remaining_sessions": allowance['remaining'],
            "session_limit": allowance['limit'],
            "sessions_used_today": allowance['sessions_used_today'],
            "reset_in": allowance['reset_in'],
            "billing_period": "daily",
            "total_sessions_used": total_sessions
        }
    })

@app.route('/user/session-allowance')
def user_session_allowance():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({
            "status": "success",
            "allowance": {"allowed": True, "remaining": 10, "limit": 10, "reset_in": "24h", "period": "daily"}
        })
    
    allowance = session_service.check_daily_limit(user_id)
    return jsonify({"status": "success", "allowance": allowance})

@app.route('/user/session-count')
def user_session_count():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"status": "success", "session_count": 0})
    
    result = db.fetch_one("SELECT sessions_used_today FROM users WHERE id = %s", (user_id,))
    return jsonify({"status": "success", "session_count": result['sessions_used_today'] if result else 0})

if __name__ == '__main__':
    # Initialize database tables
    with app.app_context():
        if db.initialize_database():
            print("✅ Database tables created/verified")
        else:
            print("❌ Failed to initialize database tables")

    # In local development
    if __name__ == '__main__':
        host = os.environ.get('HOST', '0.0.0.0')
        port = int(os.environ.get('PORT', 5000))
        debug = os.environ.get('DEBUG', 'False').lower() == 'true'
        app.run(host=host, port=port, debug=debug)