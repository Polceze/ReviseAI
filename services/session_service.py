from cachetools import TTLCache
from typing import Dict, Any, Optional
from models import Database

class SessionService:
    """Handles session limits, caching, and allowance checking"""
    
    def __init__(self, db: Database):
        self.db = db
        self.cache = TTLCache(maxsize=100, ttl=60)  # 60-second TTL
    
    def check_daily_limit(self, user_id: int) -> Dict[str, Any]:
        """Check if user has exceeded daily session limit"""
        try:
            conn = self.db.get_connection()
            if not conn:
                return self._default_allowance()
            
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT sessions_used_today, last_session_date, CURDATE() as today
                FROM users WHERE id = %s
            """, (user_id,))
            user = cursor.fetchone()
            
            if not user:
                return self._default_allowance()
            
            sessions_used = user['sessions_used_today'] or 0
            needs_reset = user['last_session_date'] is None or user['last_session_date'].date() != user['today']
            
            if needs_reset:
                sessions_used = 0
                cursor.execute("""
                    UPDATE users SET sessions_used_today = 0, last_session_date = CURDATE()
                    WHERE id = %s
                """, (user_id,))
                conn.commit()
            
            cursor.close()
            conn.close()
            
            return {
                "allowed": sessions_used < 10,
                "remaining": max(0, 10 - sessions_used),
                "limit": 10,
                "sessions_used_today": sessions_used,
                "reset_in": "midnight",
                "period": "daily"
            }
            
        except Exception as e:
            print(f"Error checking daily limit: {e}")
            return self._default_allowance()
    
    def increment_session_count(self, user_id: int) -> bool:
        """Increment user's session count after successful generation"""
        try:
            conn = self.db.get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users 
                SET sessions_used_today = sessions_used_today + 1,
                    total_sessions_used = total_sessions_used + 1,
                    last_session_date = CURDATE()
                WHERE id = %s
            """, (user_id,))
            conn.commit()
            cursor.close()
            conn.close()
            
            self.invalidate_cache(user_id)
            return True
            
        except Exception as e:
            print(f"Error incrementing session count: {e}")
            return False
    
    def get_user_sessions(self, user_id: int) -> list:
        """Get sessions from cache or database"""
        cache_key = f"sessions_{user_id}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        result = self.db.get_sessions(user_id)
        sessions = result.get('sessions', []) if isinstance(result, dict) else []
        
        self.cache[cache_key] = sessions
        return sessions
    
    def invalidate_cache(self, user_id: int) -> None:
        """Invalidate cached sessions for a user"""
        cache_key = f"sessions_{user_id}"
        if cache_key in self.cache:
            del self.cache[cache_key]
    
    def _default_allowance(self) -> Dict[str, Any]:
        return {
            "allowed": True,
            "remaining": 10,
            "limit": 10,
            "sessions_used_today": 0,
            "reset_in": "midnight",
            "period": "daily"
        }