from flask import Blueprint, request, jsonify, session

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')

@analytics_bp.route('/type-difficulty', methods=['GET'])
def type_difficulty():
    from app import db
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "Auth required"}), 401
    
    data = db.get_analytics_type_difficulty(user_id)
    return jsonify({"status": "success", "data": data}) if data else jsonify({"status": "error"}), 500

@analytics_bp.route('/type-difficulty-filtered', methods=['POST'])
def type_difficulty_filtered():
    from app import db
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "Auth required"}), 401
    
    data = request.get_json()
    session_ids = data.get('session_ids', [])
    
    if not session_ids:
        return jsonify({"status": "success", "data": {"question_types": [], "difficulties": []}})
    
    # Build IN clause safely
    placeholders = ','.join(['%s'] * len(session_ids))
    
    conn = db.get_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute(f"""
        SELECT question_type, COUNT(*) as total_questions,
               SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct_answers
        FROM studycards
        WHERE session_id IN ({placeholders})
        GROUP BY question_type
    """, session_ids)
    type_data = cursor.fetchall()
    
    cursor.execute(f"""
        SELECT difficulty, COUNT(*) as total_questions,
               SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct_answers
        FROM studycards
        WHERE session_id IN ({placeholders})
        GROUP BY difficulty
    """, session_ids)
    difficulty_data = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify({
        "status": "success",
        "data": {"question_types": type_data, "difficulties": difficulty_data}
    })

@analytics_bp.route('/progress-data')
def progress_data():
    from app import session_service
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Auth required"}), 401
    
    sessions = session_service.get_user_sessions(user_id)
    
    return jsonify({
        "labels": [s['created_at_formatted'] for s in sessions[:10]],
        "scores": [float(s['score_percentage']) for s in sessions[:10]],
        "questions": [s['total_questions'] for s in sessions[:10]]
    })

@analytics_bp.route('/chart-data')
def chart_data():
    from app import db
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Auth required"}), 401
    
    limit = int(request.args.get('limit', 5))
    sessions = db.get_sessions_for_chart(user_id, limit)
    
    return jsonify({
        "labels": [s['created_at_formatted'] for s in sessions],
        "scores": [float(s['score_percentage']) for s in sessions],
        "questions": [s['total_questions'] for s in sessions]
    })