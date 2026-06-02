from flask import Blueprint, request, jsonify, session
import re

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    """Handle email-only login"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email or not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            return jsonify({"status": "error", "message": "Valid email required"}), 400
        
        from app import db  # Lazy import to avoid circular dependency
        user = db.get_or_create_user(email)
        
        if not user:
            return jsonify({"status": "error", "message": "Failed to create user"}), 500
        
        session['user_id'] = user['id']
        session['user_email'] = user['email']
        
        return jsonify({
            "status": "success",
            "message": "Login successful",
            "user": {"id": user['id'], "email": user['email']}
        })
        
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"status": "error", "message": "Login failed"}), 500

@auth_bp.route('/status')
def status():
    """Check authentication status"""
    return jsonify({
        "status": "success",
        "authenticated": 'user_id' in session,
        "user": {
            "id": session.get('user_id'),
            "email": session.get('user_email')
        } if 'user_id' in session else None
    })

@auth_bp.route('/logout')
def logout():
    """Log out user"""
    user_id = session.get('user_id')
    session.clear()
    
    if user_id:
        from app import session_service
        session_service.invalidate_cache(user_id)
    
    return jsonify({"status": "success", "message": "Logged out"})