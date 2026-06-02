from flask import Blueprint, request, jsonify, session
from services.ai_service import AIService

generate_bp = Blueprint('generate', __name__)
ai_service = AIService()

@generate_bp.route('/generate_questions', methods=['POST'])
def generate_questions():
    from app import db, session_service
    
    try:
        user_id = session.get('user_id')
        data = request.get_json()
        
        notes = data.get('notes', '')
        num_questions = min(int(data.get('num_questions', 6)), 12)
        question_type = data.get('question_type', 'mcq')
        difficulty = data.get('difficulty', 'normal')
        
        if not notes or not notes.strip():
            return jsonify({"status": "error", "message": "Notes required"}), 400
        
        # Check session limit for authenticated users
        if user_id:
            allowance = session_service.check_daily_limit(user_id)
            if not allowance['allowed']:
                return jsonify({
                    "status": "error",
                    "code": "SESSION_LIMIT_EXCEEDED",
                    "message": f"Daily limit reached. {allowance['remaining']} remaining",
                    "remaining": allowance['remaining'],
                    "limit": allowance['limit']
                }), 429
        
        # Generate questions
        questions, status = ai_service.generate_questions(
            notes, num_questions, question_type, difficulty
        )
        
        # Increment session count only on success
        if questions and user_id:
            session_service.increment_session_count(user_id)
            return jsonify({
                "status": "success",
                "questions": questions[:num_questions],
                "source": "ai"
            })
        
        # Handle errors
        error_messages = {
            "no_api_key": "AI service not configured",
            "quota_exceeded": "AI quota exceeded. Try later",
            "auth_error": "AI authentication failed",
            "no_valid_questions": "No valid questions generated",
            "api_error": "AI service temporarily unavailable"
        }
        
        return jsonify({
            "status": "error",
            "message": error_messages.get(status, "Generation failed"),
            "code": "AI_ERROR"
        }), 500
        
    except Exception as e:
        print(f"Generation error: {e}")
        return jsonify({"status": "error", "message": "Internal error"}), 500