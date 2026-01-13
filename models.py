from mysql.connector import Error
from mysql.connector.pooling import MySQLConnectionPool
from config import Config
import json
from datetime import datetime, timedelta

class Database:
    def __init__(self):
        self.config = {
            'host': Config.DB_HOST,
            'database': Config.DB_NAME,
            'user': Config.DB_USER,
            'password': Config.DB_PASSWORD
        }

        if not all(self.config.values()):
            raise RuntimeError(f"Missing DB config: {self.config}")
    
        # Initialize connection pool
        try:
            self.pool = MySQLConnectionPool(
                pool_name="reviseAI_pool",
                pool_size=5,
                pool_reset_session=True,
                **self.config
            )
            print(f"✅ Database pool initialized for {Config.DB_HOST}")
        except Error as e:
            print(f"❌ Database connection error: {e}")
            print(f"Config: host={Config.DB_HOST}, db={Config.DB_NAME}, user={Config.DB_USER}")
            self.pool = None
    
    def get_connection(self):
        """Get a connection from the pool"""
        return self.pool.get_connection()

    def execute_query(self, query, params=None):
        """Run INSERT/UPDATE/DELETE queries"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params or ())
            conn.commit()
            return cursor.lastrowid  # useful for inserts
        except Error as e:
            print(f"Database error: {e}")
            conn.rollback()
            return None
        finally:
            cursor.close()
            conn.close()

    def fetch_all(self, query, params=None):
        """Run SELECT queries that return multiple rows"""
        conn = self.get_connection()
        if not conn:
            return []
        
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
            result = cursor.fetchall()
            return result
        
        except Error as e:
            return []
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def test_connection(self):
        """Test database connection"""
        try:
            conn = self.get_connection()
            if conn:
                print("✅ Database connection successful")
                conn.close()
                return True
            else:
                print("❌ Database connection failed")
                return False
        except Exception as e:
            print(f"❌ Database connection test failed: {e}")
            return False

    def initialize_database(self):
        """Create necessary tables if they don't exist"""
        if self.pool is None:
            print("❌ Cannot initialize database: No connection pool available")
            return False
        
        connection = self.get_connection()
        if connection is None:
            print("❌ Cannot initialize database: Failed to get connection")
            return False
        
        cursor = None
        
        try:
            cursor = connection.cursor()

            # --- Users table ---
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    subscription_tier VARCHAR(20) DEFAULT 'free',
                    sessions_used_today INT DEFAULT 0,
                    last_session_date DATE,
                    total_sessions_used INT DEFAULT 0
                ) ENGINE=InnoDB
            """)

            # --- Study Sessions ---
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS study_sessions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    notes TEXT,
                    user_id INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    session_duration FLOAT,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    INDEX idx_user_id (user_id),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB
            """)

            # --- Studycards ---
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS studycards (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    session_id INT,
                    question TEXT NOT NULL,
                    options JSON NOT NULL,
                    correct_answer INT NOT NULL,
                    user_answer INT,
                    is_correct BOOLEAN,
                    question_type VARCHAR(20) DEFAULT 'mcq',
                    difficulty VARCHAR(20) DEFAULT 'normal',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES study_sessions(id) ON DELETE CASCADE,
                    INDEX idx_session_id (session_id)
                ) ENGINE=InnoDB
            """)

            # REMOVED: Anonymous user creation

            connection.commit()
            print("✅ Database initialized with clean schema (no anonymous users)")
            return True

        except Error as e:
            print(f"Error initializing database: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def create_study_session(self, title, notes, user_id):
        """Create a study session and return session ID"""
        try:
            query = "INSERT INTO study_sessions (title, notes, user_id) VALUES (%s, %s, %s)"
            session_id = self.execute_query(query, (title, notes, user_id))
            return session_id
        except Error as e:
            print(f"Error creating study session: {e}")
            return None

    def save_flashcards(self, session_id, flashcards):
        """Save flashcards for a session with type and difficulty"""
        try:
            # Delete any existing flashcards for this session
            delete_query = "DELETE FROM studycards WHERE session_id = %s"
            self.execute_query(delete_query, (session_id,))
            
            # Insert new flashcards with type and difficulty
            for card in flashcards:
                user_answer = card.get('userAnswer')
                correct_answer = card.get('correctAnswer', 0)
                is_correct = user_answer is not None and user_answer == correct_answer
                
                question_type = card.get('questionType', card.get('question_type', 'mcq'))
                difficulty = card.get('difficulty', 'normal')
                
                query = """
                    INSERT INTO studycards 
                    (session_id, question, options, correct_answer, user_answer, 
                    is_correct, question_type, difficulty)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                params = (
                    session_id,
                    card.get('question', ''),
                    json.dumps(card.get('options', [])),
                    correct_answer,
                    user_answer,
                    is_correct,
                    question_type,
                    difficulty
                )
                self.execute_query(query, params)
            
            return True
            
        except Error as e:
            print(f"Error saving flashcards: {e}")
            return False

    def get_sessions(self, user_id=None):
        """Get study sessions for a user"""
        query = """
            SELECT 
                s.id, s.title, s.created_at, s.updated_at, s.session_duration,
                DATE_FORMAT(s.created_at, '%%Y-%%m-%%dT%%H:%%i:%%s') AS created_at_formatted,
                COUNT(c.id) AS total_questions,
                SUM(CASE WHEN c.is_correct = 1 THEN 1 ELSE 0 END) as correct_answers,
                CASE 
                    WHEN COUNT(c.id) > 0 
                    THEN ROUND(SUM(CASE WHEN c.is_correct = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(c.id), 2) 
                    ELSE 0 
                END AS score_percentage,
                GROUP_CONCAT(DISTINCT c.question_type) AS question_types
            FROM study_sessions s
            LEFT JOIN studycards c ON s.id = c.session_id
        """
        
        params = {}
        if user_id is not None:
            query += " WHERE s.user_id = %(user_id)s"
            params['user_id'] = user_id
        
        query += " GROUP BY s.id, s.title, s.created_at ORDER BY s.created_at DESC"
        
        sessions = self.fetch_all(query, params)
        
        # Process the results
        formatted_sessions = []
        for s in sessions:
            types = []
            if s.get("question_types"):
                types = list(set(s["question_types"].split(",")))
            
            formatted_sessions.append({
                "id": s["id"],
                "title": s["title"],
                "created_at": s["created_at"],
                "created_at_formatted": s["created_at_formatted"],
                "total_questions": int(s["total_questions"]) if s.get("total_questions") is not None else 0,
                "correct_answers": int(s["correct_answers"]) if s.get("correct_answers") is not None else 0,
                "score_percentage": float(s["score_percentage"]) if s.get("score_percentage") is not None else 0.0,
                "question_types": types,
                "session_duration": float(s["session_duration"]) if s.get("session_duration") is not None else None,
                "updated_at": s["updated_at"]
            })

        return {"status": "success", "sessions": formatted_sessions}
    
    def get_or_create_user(self, email):
        """Get user by email, create if not exists - PREVENT ANONYMOUS"""
        # Don't allow anonymous email
        if email == 'anonymous@example.com' or not email or email.strip() == '':
            return None
        
        connection = self.get_connection()  
        if connection is None:
            return None
        
        cursor = None
        try:
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT id, email FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            
            if user:
                return user
            
            cursor.execute("INSERT INTO users (email) VALUES (%s)", (email,))
            connection.commit()
            user_id = cursor.lastrowid
            
            cursor.execute("SELECT id, email FROM users WHERE id = %s", (user_id,))
            return cursor.fetchone()
            
        except Error as e:
            print(f"Error getting/creating user: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

    def get_sessions_for_chart(self, user_id=None, limit=10):
        """Get sessions for chart data, including score and question type summary"""
        connection = self.get_connection() 
        if connection is None:
            return []
        
        cursor = None
        try:
            cursor = connection.cursor(dictionary=True)
            
            query = """
                SELECT 
                    s.id,
                    s.title,
                    s.created_at,
                    s.updated_at,
                    s.session_duration,
                    DATE_FORMAT(s.created_at, '%%Y-%%m-%%dT%%H:%%i:%%s') AS created_at_formatted,
                    COUNT(c.id) AS total_questions,
                    SUM(CASE WHEN c.is_correct = 1 THEN 1 ELSE 0 END) as correct_answers,
                    CASE 
                        WHEN COUNT(c.id) > 0 
                        THEN ROUND(SUM(CASE WHEN c.is_correct = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(c.id), 2) 
                        ELSE 0 
                    END AS score_percentage,
                    GROUP_CONCAT(DISTINCT c.question_type) AS question_types
                FROM study_sessions s
                LEFT JOIN studycards c ON s.id = c.session_id
            """
            
            params = {}
            where_clauses = []
            
            if user_id is not None:
                where_clauses.append("s.user_id = %(user_id)s")
                params['user_id'] = user_id
            else:
                cursor.execute("SELECT id FROM users WHERE email = 'anonymous@example.com'")
                anonymous_user = cursor.fetchone()
                if anonymous_user:
                    where_clauses.append("s.user_id = %(anonymous_user_id)s")
                    params['anonymous_user_id'] = anonymous_user['id']
            
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            
            query += " GROUP BY s.id, s.title, s.created_at ORDER BY s.created_at DESC LIMIT %(limit)s"
            params['limit'] = limit
            
            cursor.execute(query, params)
            sessions = cursor.fetchall()

            formatted_sessions = []
            for s in sessions:
                types = []
                if s.get("question_types"):
                    types = list(set(s["question_types"].split(",")))
                
                formatted_sessions.append({
                    "id": s["id"],
                    "title": s["title"],
                    "created_at": s["created_at"],
                    "created_at_formatted": s["created_at_formatted"],
                    "total_questions": int(s["total_questions"]) if s.get("total_questions") is not None else 0,
                    "correct_answers": int(s["correct_answers"]) if s.get("correct_answers") is not None else 0,
                    "score_percentage": float(s["score_percentage"]) if s.get("score_percentage") is not None else 0.0,
                    "question_types": types,
                    "session_duration": float(s["session_duration"]) if s.get("session_duration") is not None else None,
                    "updated_at": s["updated_at"]
                })
            
            return formatted_sessions
            
        except Error as e:
            print(f"Error retrieving sessions for chart: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

    def get_flashcards_by_session(self, session_id):
        """Retrieve studycards for a specific study session"""
        connection = self.get_connection() 
        if connection is None:
            return []
        
        cursor = None
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """SELECT id, session_id, question, question_type, options, 
                        correct_answer, user_answer, is_correct, created_at
                FROM studycards 
                WHERE session_id = %s 
                ORDER BY id""",
                (session_id,)
            )
            
            studycards = cursor.fetchall()
            for card in studycards:
                # Parse JSON options into Python list
                card['options'] = json.loads(card['options'])
            
            return studycards
            
        except Error as e:
            print(f"Error retrieving studycards: {e}")
            return []
        finally:
            if cursor: 
                cursor.close()
            if connection and connection.is_connected():
                connection.close() 

    def delete_session(self, session_id):
        """Delete a study session and its associated cards"""
        connection = self.get_connection() 
        if connection is None:
            return False
        
        cursor = None
        try:
            cursor = connection.cursor()
            
            cursor.execute("DELETE FROM studycards WHERE session_id = %s", (session_id,))
            cursor.execute("DELETE FROM study_sessions WHERE id = %s", (session_id,))
            connection.commit()
            
            return True
            
        except Error as e:
            print(f"Error deleting session {session_id}: {e}")
            connection.rollback()
            return False
        finally:
            if cursor: 
                cursor.close()
            if connection and connection.is_connected():
                connection.close() 

    def get_user_tier_info(self, user_id):
        """Get user's subscription tier and usage information - SIMPLIFIED"""
        connection = self.get_connection() 
        if connection is None:
            return None

        cursor = None
        try:
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT 
                    subscription_tier,
                    sessions_used_today,
                    last_session_date,
                    total_sessions_used
                FROM users
                WHERE id = %s
            """, (user_id,))
            
            result = cursor.fetchone()
            
            if not result:
                return None
                
            # Calculate remaining sessions
            sessions_used_today = result['sessions_used_today'] or 0
            last_date = result['last_session_date']
            today = datetime.now().date()
            
            # Reset counter if it's a new day
            if last_date != today:
                remaining_sessions = 10
            else:
                remaining_sessions = max(0, 10 - sessions_used_today)
            
            return {
                'tier': 'free',
                'sessions_used_today': sessions_used_today,
                'session_limit': 10,
                'remaining_sessions': remaining_sessions,
                'reset_in': 'midnight',
                'billing_period': 'daily',
                'total_sessions_used': result['total_sessions_used'] or 0
            }

        except Exception as e:
            print(f"Error getting user tier info: {e}")
            return None
        finally:
            if cursor: 
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

    def check_session_allowance(self, user_id):
        """Check session allowance - SIMPLIFIED"""
        connection = self.get_connection()
        if connection is None:
            return {"allowed": True, "remaining": 10, "limit": 10, "reset_in": "midnight", "period": "daily", "sessions_used_today": 0}
        
        cursor = None
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Get user's current session usage
            cursor.execute("""
                SELECT sessions_used_today, 
                    DATE(last_session_date) as last_date,
                    CURDATE() as today
                FROM users WHERE id = %s
            """, (user_id,))
            user = cursor.fetchone()
            
            if not user:
                return {"allowed": True, "remaining": 10, "limit": 10, "reset_in": "midnight", "period": "daily", "sessions_used_today": 0}
            
            sessions_used_today = user['sessions_used_today'] or 0
            last_date = user['last_date']
            today = user['today']
            
            # Reset counter if it's a new day
            if last_date != today:
                sessions_used_today = 0
                # Update the last_session_date
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
                "reset_in": "midnight",
                "period": "daily",
                "sessions_used_today": sessions_used_today
            }
                    
        except Exception as e:
            print(f"Error checking session allowance: {e}")
            return {"allowed": True, "remaining": 10, "limit": 10, "reset_in": "midnight", "period": "daily", "sessions_used_today": 0}
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

    def fetch_one(self, query, params=None):
        """Run SELECT query that returns single row"""
        conn = self.get_connection()
        if not conn:
            return None
        
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
            result = cursor.fetchone()
            return result
        except Exception as e:
            print(f"Database fetch_one error: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()