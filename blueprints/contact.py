from flask import Blueprint, request, jsonify, render_template
import os
from services.email_service import EmailService

contact_bp = Blueprint('contact', __name__)

@contact_bp.route('/contact', methods=['GET'])
def contact_page():
    return render_template('contact.html')

@contact_bp.route('/contact', methods=['POST'])
def send_contact():
    from app import mail
    
    try:
        data = request.get_json() or {}
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        message = data.get('message', '').strip()
        
        if not all([name, email, message]):
            return jsonify({'status': 'error', 'message': 'All fields required'}), 400
        
        if '@' not in email:
            return jsonify({'status': 'error', 'message': 'Valid email required'}), 400
        
        recipient = os.environ.get('CONTACT_DESTINATION_EMAIL', os.environ.get('MAIL_USERNAME'))
        
        email_service = EmailService(mail)
        email_service.send_async(
            subject=f"Contact from {name}",
            recipients=[recipient],
            body=f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}",
            reply_to=email
        )
        
        return jsonify({'status': 'success', 'message': 'Message sent!'})
        
    except Exception as e:
        print(f"Contact error: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to send'}), 500