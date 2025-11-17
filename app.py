from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_mail import Mail, Message
import os
from dotenv import load_dotenv
from models import Database
from datetime import datetime, timezone, timedelta
import requests
import json
import re
from cachetools import TTLCache


load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or os.urandom(24).hex()

# Configure Flask-Mail
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', True)
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME'])
mail = Mail(app)

# Initialize database
db = Database()
db.initialize_database()

session_cache = TTLCache(maxsize=100, ttl=60)  # 60-second TTL, max 100 users

def get_user_sessions(user_id):
    """Get sessions from cache or database"""
    cache_key = f"sessions_{user_id}"
    
    # Check cache first
    try:
        if cache_key in session_cache:
            return session_cache[cache_key]
    except Exception:
        pass
    
    # Fetch from database
    result = db.get_sessions(user_id)
    sessions = result.get('sessions', []) if isinstance(result, dict) and result.get('status') == 'success' else []
    
    # Store in cache
    try:
        session_cache[cache_key] = sessions
    except Exception:
        pass
    
    return sessions

def invalidate_user_cache(user_id):
    """Invalidate cache for a user's sessions"""
    cache_key = f"sessions_{user_id}"
    try:
        if cache_key in session_cache:
            del session_cache[cache_key]
    except Exception:
        pass

def check_daily_session_limit(user_id):
    """Check if user has exceeded daily session limit (10 sessions per day)"""
    try:
        connection = db.get_connection()
        if not connection:
            return {"allowed": True, "remaining": 10, "limit": 10, "reset_in": "midnight", "period": "daily", "sessions_used_today": 0}
        
        cursor = connection.cursor(dictionary=True)
        
        # Get user's session count for today using last_session_date
        cursor.execute("""
            SELECT 
                sessions_used_today, 
                last_session_date,
                CURDATE() as today,
                DATE(last_session_date) as last_date_formatted
            FROM users 
            WHERE id = %s
        """, (user_id,))
        
        user_data = cursor.fetchone()
        
        if not user_data:
            return {"allowed": True, "remaining": 10, "limit": 10, "reset_in": "midnight", "period": "daily", "sessions_used_today": 0}
        
        sessions_used_today = user_data['sessions_used_today'] or 0
        last_session_date = user_data['last_session_date']
        today = user_data['today']
        last_date_formatted = user_data['last_date_formatted']
        
        # Reset counter if it's a new day (midnight reset)
        needs_reset = False
        if last_session_date is None:
            needs_reset = True
        else:
            # Compare dates directly
            if last_date_formatted != today:
                needs_reset = True
        
        if needs_reset:
            sessions_used_today = 0
            cursor.execute("""
                UPDATE users 
                SET sessions_used_today = 0, last_session_date = CURDATE()
                WHERE id = %s
            """, (user_id,))
            connection.commit()
        
        remaining_sessions = max(0, 10 - sessions_used_today)
        allowed = sessions_used_today < 10
        
        return {
            "allowed": allowed,
            "remaining": remaining_sessions,
            "limit": 10,
            "reset_in": "midnight",  # Simplified message
            "period": "daily",
            "sessions_used_today": sessions_used_today
        }
        
    except Exception as e:
        print(f"Error checking daily session limit: {e}")
        return {"allowed": True, "remaining": 10, "limit": 10, "reset_in": "midnight", "period": "daily", "sessions_used_today": 0}
    finally:
        if 'cursor' in locals():
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

def balance_correct_answers(questions):
    """
    Ensure correct answers are distributed across different positions (A, B, C, D)
    to prevent patterns like all answers being 'A'
    """
    if not questions or len(questions) <= 1:
        return questions
    
    positions = [0, 1, 2, 3]  # A, B, C, D
    position_count = {0: 0, 1: 0, 2: 0, 3: 0}
    
    # Count current distribution and validate questions
    valid_questions = []
    for q in questions:
        # Skip questions with invalid options or correctAnswer
        options = q.get('options', [])
        correct_answer = q.get('correctAnswer')
        
        if (not options or 
            correct_answer is None or 
            correct_answer >= len(options) or 
            correct_answer < 0 or
            len(options) < 2):  # At least 2 options needed
            print(f"⚠️ Skipping invalid question: {len(options)} options, correctAnswer: {correct_answer}")
            valid_questions.append(q)  # Keep invalid questions as-is
            continue
            
        valid_questions.append(q)
        if correct_answer in position_count:
            position_count[correct_answer] += 1
    
    # If we filtered out questions, use the valid ones
    if len(valid_questions) != len(questions):
        print(f"⚠️ Filtered {len(questions) - len(valid_questions)} invalid questions")
        questions = valid_questions
    
    # Check if we need to rebalance (if any position has more than its fair share)
    max_allowed = (len(questions) // 4) + 1
    needs_rebalancing = any(count > max_allowed for count in position_count.values())
    
    if not needs_rebalancing:
        print("✅ Distribution is already balanced")
        return questions
    
    print(f"📊 Rebalancing answer positions. Current distribution: A={position_count[0]}, B={position_count[1]}, C={position_count[2]}, D={position_count[3]}")
    
    # STRATEGY: Try to balance by processing questions
    import random
    question_indices = list(range(len(questions)))
    random.shuffle(question_indices)
    
    # Target distribution
    target_distribution = {}
    total_questions = len(questions)
    base_count = total_questions // 4
    remainder = total_questions % 4
    
    for i, pos in enumerate(positions):
        target_distribution[pos] = base_count + (1 if i < remainder else 0)
    
    print(f"🎯 Target distribution: A={target_distribution[0]}, B={target_distribution[1]}, C={target_distribution[2]}, D={target_distribution[3]}")
    
    # Safe rebalancing
    rebalanced_count = 0
    
    for i in question_indices:
        q = questions[i]
        current_pos = q.get('correctAnswer')
        options = q.get('options', [])
        
        # Skip if invalid
        if (current_pos is None or 
            current_pos >= len(options) or 
            len(options) < 2):
            continue
        
        # Only rebalance if this position is over target
        if current_pos in position_count and position_count[current_pos] > target_distribution[current_pos]:
            # Find positions that are under target
            underused_positions = [
                pos for pos in positions 
                if (position_count.get(pos, 0) < target_distribution.get(pos, 0) and
                    pos < len(options))  # Ensure the position exists in options
            ]
            
            if underused_positions:
                # Choose the most underused position
                new_pos = min(underused_positions, key=lambda p: position_count.get(p, 0))
                
                # SAFE SWAP: Only swap if both positions exist in options
                if (current_pos < len(options) and 
                    new_pos < len(options) and 
                    current_pos != new_pos):
                    
                    # Swap the correct answer with the new position
                    correct_text = options[current_pos]
                    other_text = options[new_pos]
                    
                    q['options'][current_pos] = other_text
                    q['options'][new_pos] = correct_text
                    q['correctAnswer'] = new_pos
                    
                    position_count[current_pos] -= 1
                    position_count[new_pos] = position_count.get(new_pos, 0) + 1
                    rebalanced_count += 1
                    print(f"🔄 Swapped Q{i+1} from position {current_pos} to {new_pos}")
                    
                    # Early exit if we've achieved good distribution
                    if all(position_count.get(pos, 0) <= target_distribution.get(pos, 0) for pos in positions):
                        break
    
    print(f"✅ Balanced {rebalanced_count} questions. Final distribution: A={position_count[0]}, B={position_count[1]}, C={position_count[2]}, D={position_count[3]}")
    return questions

def generate_questions_with_claude(notes, num_questions=6, question_type="mcq", difficulty="normal"):
    """
    Generate quiz questions using Anthropic Claude API.
    """
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ No Anthropic API key found")
        return None, "no_api_key"
    
    try:
        import anthropic
        
        client = anthropic.Anthropic(api_key=api_key)
        
        # Build optimized prompt for Claude
        prompt = build_claude_prompt(notes, num_questions, question_type, difficulty)
        
        print(f"🔄 Calling Claude API with {len(notes)} characters of notes...")
        
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=2000,
            temperature=0.8,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        if response and response.content:
            response_text = response.content[0].text
            print("✅ Claude API call successful!")
            return process_api_response(response_text, num_questions, question_type, difficulty)
        else:
            print("❌ Claude API returned empty response")
            return None, "empty_response"
            
    except anthropic.APIConnectionError as e:
        print(f"❌ Claude API connection error: {str(e)}")
        return None, "api_error"
    except anthropic.RateLimitError as e:
        print(f"❌ Claude API rate limit exceeded: {str(e)}")
        return None, "quota_exceeded"
    except anthropic.APIStatusError as e:
        print(f"❌ Claude API status error: {e.status_code} - {str(e)}")
        if e.status_code == 401:
            return None, "auth_error"
        return None, "api_error"
    except ImportError:
        print("❌ Anthropic module not installed")
        return None, "module_missing"
    except Exception as e:
        print(f"❌ Claude API error: {str(e)}")
        return None, "api_error"

def build_claude_prompt(notes, num_questions, question_type, difficulty):
    """Build optimized prompt for Claude with clear question type instructions"""
    truncated_notes = notes[:1500]
    
    # More specific instructions for each question type
    type_instructions = {
        "mcq": f"""Generate exactly {num_questions} multiple-choice questions. Each question must have exactly 4 options (A, B, C, D).
- Use meaningful, distinct options
- Avoid "All of the above" or "None of the above" unless absolutely necessary
- Ensure only one correct answer per question""",
        
        "tf": f"""Generate exactly {num_questions} True/False questions. Each question must have exactly 2 options: ["True", "False"].
- Questions should be clear factual statements that can be definitively true or false
- Use the exact options: "True" and "False" (capitalized)"""
    }
    
    difficulty_instructions = {
        "normal": "Focus on factual recall and basic understanding from the notes.",
        "difficult": "Test deeper understanding, analysis, and application of concepts from the notes."
    }
    
    return f"""Create a quiz based on these study notes. Follow these instructions carefully:

{type_instructions.get(question_type, type_instructions['mcq'])}

{difficulty_instructions.get(difficulty, difficulty_instructions['normal'])}

CRITICAL: All questions must be of the same type ({question_type.upper()}).
- For MCQ: All questions must have exactly 4 options
- For True/False: All questions must have exactly 2 options: "True" and "False"

Return ONLY valid JSON in this exact format:
{{
  "questions": [
    {{
      "question": "Clear question text here?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correctAnswer": 0
    }}
  ]
}}

NOTES:
{truncated_notes}

Important:
- correctAnswer must be the index (0, 1, 2, or 3 for MCQ; 0 or 1 for True/False)
- Questions must be directly based on the provided notes
- Return ONLY the JSON, no additional text or explanations
- Ensure consistent question type throughout"""

def build_optimized_prompt(notes, num_questions, question_type, difficulty):
    """Build optimized prompt with reduced length"""
    # Truncate notes more aggressively
    truncated_notes = notes[:1500]  # Reduced from 2000
    
    type_instructions = {
        "mcq": f"Generate {num_questions} multiple-choice questions with 4 options each.",
        "tf": f"Generate {num_questions} True/False questions with 2 options each."
    }
    
    difficulty_instructions = {
        "normal": "Focus on factual recall and basic understanding.",
        "difficult": "Test deeper understanding and application."
    }
    
    return f"""
Create a quiz based on these notes. Keep questions concise.

{type_instructions.get(question_type, type_instructions['mcq'])}
{difficulty_instructions.get(difficulty, difficulty_instructions['normal'])}

NOTES: {truncated_notes}

Return as JSON: {{"questions": [{{"question": "...", "options": ["A","B"], "correctAnswer": 0}}]}}
"""

def process_api_response(response_text, num_questions, question_type, difficulty):
    """Process API response with question type validation"""
    try:
        # Find JSON more efficiently
        json_str = extract_json_from_text(response_text)
        if not json_str:
            return None, "invalid_response"
            
        questions_data = json.loads(json_str)
        raw_questions = questions_data.get('questions', [])[:num_questions]
        
        if not raw_questions:
            return None, "no_questions"
            
        # Validate and process questions with type checking
        processed_questions = []
        validation_errors = []
        
        for i, q in enumerate(raw_questions):
            # Validate required fields
            if not all(key in q for key in ['question', 'options', 'correctAnswer']):
                validation_errors.append(f"Question {i+1} missing required fields")
                continue
                
            # Validate options array and type consistency
            options = q.get('options', [])
            correct_answer = q.get('correctAnswer')
            expected_option_count = 4 if question_type == "mcq" else 2
            
            # Check option count matches question type
            if len(options) != expected_option_count:
                validation_errors.append(f"Question {i+1}: Expected {expected_option_count} options for {question_type}, got {len(options)}")
                continue
            
            # Validate correct answer index
            if (not isinstance(correct_answer, int) or 
                correct_answer < 0 or 
                correct_answer >= len(options)):
                validation_errors.append(f"Question {i+1}: Invalid correctAnswer index {correct_answer} for {len(options)} options")
                continue
            
            # For True/False questions, validate option labels
            if question_type == "tf":
                if options != ["True", "False"] and options != ["False", "True"]:
                    validation_errors.append(f"Question {i+1}: True/False questions must have options ['True', 'False'], got {options}")
                    continue
            
            q.update({
                "question_type": question_type,
                "difficulty": difficulty
            })
            processed_questions.append(q)
        
        # Log validation errors for debugging
        if validation_errors:
            print(f"⚠️ Validation errors: {validation_errors}")
        
        if not processed_questions:
            return None, "no_valid_questions"
        
        # Balance answers only for MCQ with enough questions
        if question_type == "mcq" and len(processed_questions) >= 2:
            processed_questions = balance_correct_answers(processed_questions)
            
        print(f"✅ Processed {len(processed_questions)} valid {question_type} questions")
        return processed_questions, "success"
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing failed: {e}")
        return None, "parse_error"
    except Exception as e:
        print(f"❌ Unexpected error in process_api_response: {e}")
        return None, "process_error"

def extract_json_from_text(text):
    """Efficiently extract JSON from response text"""
    start = text.find('{')
    end = text.rfind('}') + 1
    return text[start:end] if start >= 0 and end > start else None

@app.route('/auth/login', methods=['POST'])
def auth_login():
    """Handle email-only login"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        # Basic email validation
        if not email or not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            return jsonify({"status": "error", "message": "Please enter a valid email address"}), 400
        
        # Get or create user in database
        user = db.get_or_create_user(email)
        if not user:
            return jsonify({"status": "error", "message": "Failed to create user account"}), 500
        
        # Set user session
        session['user_id'] = user['id']
        session['user_email'] = user['email']
        
        print(f"✅ User logged in: {user['email']} (ID: {user['id']})")
        
        return jsonify({
            "status": "success", 
            "message": "Login successful",
            "user": {
                "id": user['id'],
                "email": user['email']
            }
        })
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return jsonify({"status": "error", "message": "Login failed. Please try again."}), 500

@app.route('/auth/status')
def auth_status():
    """Check authentication status"""
    user_id = session.get('user_id')
    user_email = session.get('user_email')
    
    return jsonify({
        "status": "success",
        "authenticated": user_id is not None,
        "user": {
            "id": user_id,
            "email": user_email
        } if user_id else None
    })

@app.route('/auth/logout')
def auth_logout():
    """Log out user - UPDATED WITH CACHE INVALIDATION"""
    user_id = session.get('user_id')
    user_email = session.get('user_email', 'Unknown')
    
    if user_id:
        invalidate_user_cache(user_id)  # Invalidate cache on logout
        
    session.pop('user_id', None)
    session.pop('user_email', None)
    print(f"✅ User logged out: {user_email}")
    return jsonify({"status": "success", "message": "Logged out successfully"})

@app.before_request
def require_auth():
    # Allow these routes without authentication
    if request.path in ['/auth/login', '/auth/status', '/', '/static/', '/contact']:
        return None
    
    # Allow static files
    if request.path.startswith('/static/'):
        return None
    
    # Check if user is authenticated
    if 'user_id' not in session:
        # For AJAX/API requests, return JSON error
        if request.path.startswith('/api/') or request.is_json:
            return jsonify({"status": "error", "message": "Authentication required"}), 401
        else:
            # For page requests, just allow through - frontend will handle auth modal
            return None
    
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_questions', methods=['POST'])
def generate_questions():
    try:
        user_id = session.get('user_id')
        if user_id:
            allowance = check_daily_session_limit(user_id)
            if not allowance['allowed']:
                return jsonify({
                    "status": "error", 
                    "code": "SESSION_LIMIT_EXCEEDED",
                    "message": f"Daily limit exceeded. You can create {allowance['limit']} sessions per day.",
                    "reset_in": allowance['reset_in'],
                    "remaining": allowance['remaining'],
                    "limit": allowance['limit']
                }), 429

        data = request.get_json()        
        notes = data.get('notes', '')
        num_questions = min(int(data.get('num_questions', 6)), 12)
        question_type = data.get('question_type', 'mcq')
        difficulty = data.get('difficulty', 'normal')
        
        if not notes or not notes.strip():
            return jsonify({"status": "error", "message": "Please provide study notes"}), 400

        # ✅ FIRST: Try AI generation with Claude
        ai_questions, api_status = generate_questions_with_claude(notes, num_questions, question_type, difficulty)
        
        # ✅ ONLY increment session count if AI generation was successful
        if ai_questions and user_id:
            connection = db.get_connection()
            if connection:
                try:
                    cursor = connection.cursor(dictionary=True)
                    
                    # Double-check we're not exceeding the limit before incrementing
                    allowance = check_daily_session_limit(user_id)
                    if not allowance['allowed']:
                        return jsonify({
                            "status": "error", 
                            "code": "SESSION_LIMIT_EXCEEDED", 
                            "message": f"Daily limit exceeded. You can create {allowance['limit']} sessions per day.",
                            "reset_in": allowance['reset_in'],
                            "remaining": allowance['remaining'],
                            "limit": allowance['limit']
                        }), 429
                    
                    # Only increment if AI generation was successful
                    cursor.execute("""
                        UPDATE users 
                        SET sessions_used_today = sessions_used_today + 1,
                            total_sessions_used = total_sessions_used + 1,
                            last_session_date = CURDATE()
                        WHERE id = %s
                    """, (user_id,))
                    
                    connection.commit()
                    print(f"✅ Incremented session count for user {user_id} (successful AI generation)")
                            
                except Exception as e:
                    print(f"Error updating session count: {e}")
                    # Don't fail the request if count update fails
                finally:
                    if cursor:
                        cursor.close()
                    connection.close()
        
        # ✅ Handle AI response
        if ai_questions:
            response_data = {
                "status": "success", 
                "questions": ai_questions[:num_questions],
                "source": "ai",
                "message": "Questions generated successfully"
            }
            return jsonify(response_data)
        else:
            # ✅ AI failed - return error without using a session
            error_messages = {
                "no_api_key": "AI service not configured. Please contact support.",
                "quota_exceeded": "AI service quota exceeded. Please try again later.", 
                "auth_error": "AI service authentication failed. Please contact support.",
                "invalid_response": "AI returned an invalid response format. Please try again.",
                "no_questions": "AI didn't generate any questions. Please try again.",
                "no_valid_questions": "AI generated invalid questions. Please try again.",
                "parse_error": "Failed to parse AI response. Please try again.",
                "api_error": "AI service temporarily unavailable. Please try again in a moment.",
                "process_error": "Error processing AI response. Please try again."
            }
            
            error_msg = error_messages.get(api_status, "AI service error. Please try again.")
            
            return jsonify({
                "status": "error", 
                "message": error_msg,
                "code": "AI_ERROR"
            }), 500
        
    except Exception as e:
        print(f"❌ Error in generate_questions: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": f"Internal server error: {str(e)}"}), 500

@app.route('/save_flashcards', methods=['POST'])
def save_flashcards():
    try:
        data = request.get_json()
        flashcards = data.get('flashcards', [])
        notes = data.get('notes', '')
        session_start_time = data.get('session_start_time')
        session_end_time = data.get('session_end_time') 
        session_duration = data.get('session_duration', 0)
        
        # Validate data
        if not flashcards:
            return jsonify({"status": "error", "message": "No flashcards to save"}), 400
        
        # Check for unanswered questions
        unanswered = [i for i, card in enumerate(flashcards) if card.get('userAnswer') is None]
        if unanswered:
            return jsonify({
                "status": "error", 
                "message": f"Please answer all questions first. Unanswered: {len(unanswered)}",
                "unanswered": unanswered
            }), 400
        
        # Get user_id from session
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"status": "error", "message": "Authentication required"}), 401
        
        # ✅ MODIFIED: Don't check session allowance here for saving
        # The session was already counted during generation, so allow saving even if limit is reached
        # This ensures users can complete and save their 10th session
        
        # Convert ISO timestamps to MySQL format
        def convert_to_mysql_datetime(iso_string):
            """Convert ISO 8601 string to MySQL datetime format in UTC+3"""
            if not iso_string:
                return None
            try:
                # Parse ISO string
                dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
                
                # Convert to UTC+3 (East Africa Time)
                dt_utc3 = dt.astimezone(timezone(timedelta(hours=3)))
                
                # Format for MySQL
                return dt_utc3.strftime('%Y-%m-%d %H:%M:%S')
            except (ValueError, AttributeError):
                print(f"❌ Failed to parse timestamp: {iso_string}")
                return None
        
        mysql_start_time = convert_to_mysql_datetime(session_start_time)
        mysql_end_time = convert_to_mysql_datetime(session_end_time)
        
        if not mysql_start_time or not mysql_end_time:
            return jsonify({"status": "error", "message": "Invalid timestamp format"}), 400
        
        # Create study session with converted timestamps
        title = f"Study Session {datetime.now().strftime('%Y-%m-%d at %H:%M')}"
        query = """
            INSERT INTO study_sessions 
            (title, notes, user_id, created_at, updated_at, session_duration) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        # Convert milliseconds to seconds for storage
        duration_seconds = session_duration / 1000
        session_id = db.execute_query(query, (
            title, 
            notes, 
            user_id,
            mysql_start_time,  # created_at = start time
            mysql_end_time,    # updated_at = end time  
            duration_seconds   # session_duration in seconds
        ))
        
        if not session_id:
            return jsonify({"status": "error", "message": "Failed to create study session"}), 500
        
        # Save flashcards
        success = db.save_flashcards(session_id, flashcards)
        if not success:
            # If flashcards fail, delete the orphaned session
            db.execute_query("DELETE FROM study_sessions WHERE id = %s", (session_id,))
            return jsonify({"status": "error", "message": "Failed to save flashcards"}), 500
        
        invalidate_user_cache(user_id)
        return jsonify({
            "status": "success", 
            "message": "Flashcards saved successfully",
            "session_id": session_id
        })
        
    except Exception as e:
        print(f"❌ Exception in save_flashcards: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get_sessions', methods=['GET'])
def get_sessions_route():
    """Get all study sessions for current user"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({"status": "error", "message": "Authentication required"}), 401
            
        result = db.get_sessions(user_id)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error in /get_sessions: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.route('/get_flashcards/<int:session_id>', methods=['GET'])
def get_flashcards(session_id):
    """Get flashcards for a specific session"""
    try:
        flashcards = db.get_flashcards_by_session(session_id)
        return jsonify({"status": "success", "flashcards": flashcards})
    except Exception as e:
        print(f"❌ Error in get_flashcards: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/delete_session/<int:session_id>', methods=['DELETE'])
def delete_session(session_id):
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"status": "error", "message": "Authentication required"}), 401
            
        if db.delete_session(session_id):
            invalidate_user_cache(user_id)  # Invalidate cache after deletion
            return jsonify({"status": "success", "message": "Session deleted successfully"})
        else:
            return jsonify({"status": "error", "message": "Failed to delete session"}), 500
            
    except Exception as e:
        print(f"Error deleting session {session_id}: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/list_sessions')
def list_sessions():
    """Get sessions list for current user with proper duration calculation"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"status": "error", "message": "Authentication required"}), 401
        
        # Use the new helper method
        sessions = db.get_user_sessions_with_analytics(user_id)

        
        # Process sessions
        processed_sessions = []
        for session_data in sessions:
            total = session_data['total_questions'] or 0
            correct = session_data['correct_answers'] or 0
            score = round((correct / total) * 100, 1) if total > 0 else 0
            
            # Convert datetime objects to ISO format strings
            processed_session = {
                'id': session_data['id'],
                'title': session_data['title'],
                'notes': session_data['notes'],
                'total_questions': total,
                'score_percentage': score,
                'session_duration': session_data['session_duration'] or 0
            }
            
            # Add timestamp fields only if they exist
            if session_data['created_at']:
                processed_session['created_at'] = session_data['created_at'].isoformat()
            if session_data['updated_at']:
                processed_session['updated_at'] = session_data['updated_at'].isoformat()
            if session_data['session_start_time']:
                processed_session['session_start_time'] = session_data['session_start_time'].isoformat()
            if session_data['session_end_time']:
                processed_session['session_end_time'] = session_data['session_end_time'].isoformat()
            
            processed_sessions.append(processed_session)
        
        return jsonify({
            "status": "success", 
            "sessions": processed_sessions
        })
        
    except Exception as e:
        print(f"Error in list_sessions: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.route('/progress-data')
def progress_data():
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
            
        sessions = get_user_sessions(user_id)  # Use cached version
        
        # Prepare data for chart.js
        data = {
            "labels": [s['created_at_formatted'] for s in sessions[:10]],
            "scores": [float(s['score_percentage']) for s in sessions[:10]],
            "questions": [s['total_questions'] for s in sessions[:10]]
        }
        return jsonify(data)
        
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/chart-data')
def chart_data():
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
            
        limit = int(request.args.get('limit', 5))
        sessions = db.get_sessions_for_chart(user_id, limit)
        
        data = {
            "labels": [s['created_at_formatted'] for s in sessions],
            "scores": [float(s['score_percentage']) for s in sessions],
            "questions": [s['total_questions'] for s in sessions]
        }
        return jsonify(data)
        
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/user/tier-info')
def user_tier_info():
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                "status": "success",
                "tier_info": {
                    "tier": "free",
                    "remaining_sessions": 10,
                    "session_limit": 10,
                    "sessions_used_today": 0,
                    "reset_in": "24h 0m",
                    "billing_period": "daily",
                    "total_sessions_used": 0
                }
            })

        allowance = check_daily_session_limit(user_id)
        
        # Get total sessions used
        connection = db.get_connection()
        total_sessions = 0
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("""
                    SELECT total_sessions_used FROM users WHERE id = %s
                """, (user_id,))
                user_data = cursor.fetchone()
                total_sessions = user_data.get('total_sessions_used', 0) if user_data else 0
            finally:
                cursor.close()
                connection.close()

        return jsonify({
            "status": "success",
            "tier_info": {
                "tier": "free",
                "remaining_sessions": allowance['remaining'],
                "session_limit": allowance['limit'],
                "sessions_used_today": allowance.get('sessions_used_today', 0),
                "reset_in": allowance['reset_in'],
                "billing_period": "daily",
                "total_sessions_used": total_sessions
            }
        })

    except Exception as e:
        print(f"Error getting tier info: {e}")
        return jsonify({
            "status": "error", 
            "message": "Internal server error"
        }), 500

@app.route('/donate')
def upgrade_page():
    """Render the donate page"""
    return render_template('donate.html')

@app.route('/analytics')
def analytics():
    return render_template('analytics.html')

@app.route('/sessions')
def sessions():
    return render_template('sessions.html')

@app.route('/analytics/type-difficulty')
def analytics_type_difficulty():
    """Get aggregated type and difficulty analytics"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"status": "error", "message": "Authentication required"}), 401
        
        analytics_data = db.get_analytics_type_difficulty(user_id)
        
        if analytics_data is None:
            return jsonify({"status": "error", "message": "Failed to fetch analytics data"}), 500
        
        return jsonify({
            "status": "success",
            "data": analytics_data
        })
        
    except Exception as e:
        print(f"Error in analytics_type_difficulty: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.route('/analytics/type-difficulty-filtered', methods=['POST'])
def analytics_type_difficulty_filtered():
    """Get analytics for specific session IDs"""
    connection = None
    cursor = None
    try:       
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"status": "error", "message": "Authentication required"}), 401
        
        data = request.get_json()
        session_ids = data.get('session_ids', [])
        
        if not session_ids:
            return jsonify({
                "status": "success",
                "data": {
                    "question_types": [],
                    "difficulties": []
                }
            })
        
        # Convert to tuple for SQL IN clause
        session_ids_tuple = tuple(session_ids)
        if len(session_ids) == 1:
            session_ids_tuple = f"({session_ids[0]})"
        
        connection = db.get_connection()
        if not connection:
            return jsonify({"status": "error", "message": "Database connection failed"}), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # Query for question type analytics
        type_query = f"""
            SELECT 
                sc.question_type,
                COUNT(*) as total_questions,
                SUM(CASE WHEN sc.is_correct = 1 THEN 1 ELSE 0 END) as correct_answers
            FROM studycards sc
            WHERE sc.session_id IN {session_ids_tuple}
            GROUP BY sc.question_type
        """
        cursor.execute(type_query)
        type_data = cursor.fetchall()
        
        # Query for difficulty analytics
        difficulty_query = f"""
            SELECT 
                sc.difficulty,
                COUNT(*) as total_questions,
                SUM(CASE WHEN sc.is_correct = 1 THEN 1 ELSE 0 END) as correct_answers
            FROM studycards sc
            WHERE sc.session_id IN {session_ids_tuple}
            GROUP BY sc.difficulty
        """
        
        cursor.execute(difficulty_query)
        difficulty_data = cursor.fetchall()
        
        result = {
            'question_types': type_data,
            'difficulties': difficulty_data
        }
        
        return jsonify({
            "status": "success",
            "data": result
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": "Internal server error"}), 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@app.route('/debug/pool-status')
def debug_pool_status():
    try:
        # Use the public API, not private attributes
        try:
            # Try to get a connection to test if pool works
            test_conn = db.get_connection()
            if test_conn:
                test_conn.close()
                status = "Pool working"
            else:
                status = "Pool failed"
        except Exception as e:
            status = f"Pool error: {e}"
        
        return jsonify({
            "status": "success",
            "pool_status": status,
            "pool_size": db.pool.pool_size if hasattr(db, 'pool') else 'No pool'
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to render contact page
@app.route('/contact', methods=['GET'])
def contact_page():
    return render_template('contact.html')

# AJAX endpoint to receive contact form and send email
@app.route('/contact', methods=['POST'])
def send_contact():
    try:
        data = request.get_json() or {}
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        message_body = data.get('message', '').strip()

        # Basic server-side validation
        if not name or not email or not message_body:
            return jsonify({'status': 'error', 'message': 'Please provide name, email and message.'}), 400

        # Build email
        recipients = [os.environ.get('CONTACT_DESTINATION_EMAIL', app.config.get('MAIL_USERNAME'))]
        subject = f"Contact form message from {name}"
        body = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message_body}"

        msg = Message(subject=subject, sender=app.config.get('MAIL_DEFAULT_SENDER'), recipients=recipients, body=body, reply_to=email)
        mail.send(msg)

        return jsonify({'status': 'success', 'message': 'Message sent successfully!'}), 200

    except Exception as e:
        print("Error sending contact email:", e)
        return jsonify({'status': 'error', 'message': 'Failed to send message. Please try again later.'}), 500

@app.route('/user/session-allowance')
def user_session_allowance():
    """Get user's current session allowance - SIMPLIFIED"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                "status": "success",
                "allowance": {
                    "allowed": True,
                    "remaining": 10,
                    "limit": 10,
                    "reset_in": "24h",
                    "period": "daily"
                }
            })
        
        allowance = check_daily_session_limit(user_id)
        return jsonify({
            "status": "success",
            "allowance": allowance
        })
        
    except Exception as e:
        print(f"Error getting session allowance: {e}")
        return jsonify({
            "status": "error",
            "message": "Failed to get session allowance"
        }), 500

@app.route('/user/session-count')
def user_session_count():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"status": "success", "session_count": 0})
    
    # Simple query - just get sessions_used_today
    result = db.fetch_one("SELECT sessions_used_today FROM users WHERE id = %s", (user_id,))
    return jsonify({"status": "success", "session_count": result['sessions_used_today'] if result else 0})

# Development server run
# if __name__ == '__main__':
#     # Use environment variable for host/port in production
#     host = os.environ.get('HOST', '127.0.0.1')
#     port = int(os.environ.get('PORT', 5000))
#     app.run(host=host, port=port, debug=os.environ.get('DEBUG', 'False').lower() == 'true')

# Production server run
if __name__ == '__main__':
    # Use environment variable for host/port in production
    host = os.environ.get('HOST', '0.0.0.0')  # Changed to 0.0.0.0 for Railway
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host=host, port=port, debug=debug)