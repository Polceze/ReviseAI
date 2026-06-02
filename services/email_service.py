from threading import Thread
from flask_mail import Message, Mail
from typing import Optional

class EmailService:
    """Handles async email sending"""
    
    def __init__(self, mail: Mail, default_sender: Optional[str] = None):
        self.mail = mail
        self.default_sender = default_sender
    
    def send_async(self, subject: str, recipients: list, body: str, 
                   reply_to: Optional[str] = None) -> None:
        """Send email in background thread"""
        msg = Message(
            subject=subject,
            sender=self.default_sender,
            recipients=recipients,
            body=body,
            reply_to=reply_to
        )
        
        def send_thread():
            try:
                self.mail.send(msg)
                print("✅ Email sent successfully")
            except Exception as e:
                print(f"❌ Email failed: {e}")
        
        thread = Thread(target=send_thread)
        thread.daemon = True
        thread.start()