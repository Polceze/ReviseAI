from flask import Blueprint, request, jsonify, session
from datetime import datetime, timezone, timedelta

sessions_bp = Blueprint('sessions', __name__)

@ sessions_bp.route('/save_flashcards', methods=['POST'])
def save_flashcards():
    from app import db, session_service
    
    try:
        data = request.get_json()
        flashcards = data.get('flashcards', [])
        notes = data.get('notes', '')
        session_start = data.get('session_start_time')
        session_end = data.get('session_end_time')
        duration = data.get('session_duration', 0)
        
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"status": "error", "message": "Auth required"}), 401
        
        # Validate all questions answered
        unanswered = [i for i, card in enumerate(flashcards) if card.get('userAnswer') is None]
        if unanswered:
            return jsonify({
                "status": "error",
                "message": f"Answer all questions first. {len(unanswered)} unanswered",
                "unanswered": unanswered
            }), 400
        
        # Convert timestamps
        def to_mysql(iso_string):
            if not iso_string:
                return None
            dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
            return dt.astimezone(timezone(timedelta(hours=3))).strftime('%Y-%m-%d %H:%M:%S')
        
        mysql_start = to_mysql(session_start)
        mysql_end = to_mysql(session_end)
        
        title = f"Study Session {datetime.now().strftime('%Y-%m-%d at %H:%M')}"
        
        # Create session
        session_id = db.execute_query("""
            INSERT INTO study_sessions (title, notes, user_id, created_at, updated_at, session_duration)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (title, notes, user_id, mysql_start, mysql_end, duration / 1000))
        
        if not session_id:
            return jsonify({"status": "error", "message": "Failed to create session"}), 500
        
        # Save flashcards
        success = db.save_flashcards(session_id, flashcards)
        if not success:
            db.execute_query("DELETE FROM study_sessions WHERE id = %s", (session_id,))
            return jsonify({"status": "error", "message": "Failed to save flashcards"}), 500
        
        session_service.invalidate_cache(user_id)
        return jsonify({"status": "success", "message": "Saved", "session_id": session_id})
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@ sessions_bp.route('/get_sessions', methods=['GET'])
def get_sessions():
    from app import db, session_service
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "Auth required"}), 401
    
    result = db.get_sessions(user_id)
    return jsonify(result)

@ sessions_bp.route('/get_flashcards/<int:session_id>', methods=['GET'])
def get_flashcards(session_id):
    from app import db
    
    flashcards = db.get_flashcards_by_session(session_id)
    return jsonify({"status": "success", "flashcards": flashcards})

@ sessions_bp.route('/delete_session/<int:session_id>', methods=['DELETE'])
def delete_session(session_id):
    from app import db, session_service
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "Auth required"}), 401
    
    if db.delete_session(session_id):
        session_service.invalidate_cache(user_id)
        return jsonify({"status": "success", "message": "Deleted"})
    
    return jsonify({"status": "error", "message": "Delete failed"}), 500

@ sessions_bp.route('/list_sessions', methods=['GET'])
def list_sessions():
    from app import db
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "Auth required"}), 401
    
    sessions_data = db.get_user_sessions_with_analytics(user_id)
    
    processed = []
    for s in sessions_data:
        total = s['total_questions'] or 0
        correct = s['correct_answers'] or 0
        score = round((correct / total) * 100, 1) if total > 0 else 0
        
        processed.append({
            'id': s['id'],
            'title': s['title'],
            'notes': s['notes'],
            'total_questions': total,
            'score_percentage': score,
            'session_duration': s['session_duration'] or 0,
            'created_at': s['created_at'].isoformat() if s['created_at'] else None,
            'updated_at': s['updated_at'].isoformat() if s['updated_at'] else None
        })
    
    return jsonify({"status": "success", "sessions": processed})