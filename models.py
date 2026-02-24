from flask_login import UserMixin
from database import get_db
from werkzeug.security import check_password_hash

class User(UserMixin):
    """User model for authentication"""
    def __init__(self, id, username):
        self.id = id
        self.username = username
    
    @staticmethod
    def get(user_id):
        """Get user by ID"""
        db = get_db()
        user = db.execute('SELECT id, username FROM users WHERE id = ?', (user_id,)).fetchone()
        db.close()
        if user:
            return User(user['id'], user['username'])
        return None
    
    @staticmethod
    def authenticate(username, password):
        """Authenticate user with username and password"""
        db = get_db()
        user = db.execute('SELECT id, username, password_hash FROM users WHERE username = ?', 
                         (username,)).fetchone()
        db.close()
        
        if user and check_password_hash(user['password_hash'], password):
            return User(user['id'], user['username'])
        return None

class Event:
    """Event model"""
    @staticmethod
    def get_all():
        """Get all events ordered by date"""
        db = get_db()
        events = db.execute('SELECT * FROM events ORDER BY date DESC').fetchall()
        db.close()
        return events
    
    @staticmethod
    def get_recent(limit=3):
        """Get recent events"""
        db = get_db()
        events = db.execute('SELECT * FROM events ORDER BY date DESC LIMIT ?', (limit,)).fetchall()
        db.close()
        return events
    
    @staticmethod
    def create(title, date, description, image_url):
        """Create new event"""
        db = get_db()
        db.execute('INSERT INTO events (title, date, description, image_url) VALUES (?, ?, ?, ?)',
                  (title, date, description, image_url))
        db.commit()
        db.close()
    
    @staticmethod
    def delete(event_id):
        """Delete event"""
        db = get_db()
        db.execute('DELETE FROM events WHERE id = ?', (event_id,))
        db.commit()
        db.close()

class Sermon:
    """Sermon model"""
    @staticmethod
    def get_all():
        """Get all sermons ordered by date"""
        db = get_db()
        sermons = db.execute('SELECT * FROM sermons ORDER BY date DESC').fetchall()
        db.close()
        return sermons
    
    @staticmethod
    def get_recent(limit=3):
        """Get recent sermons"""
        db = get_db()
        sermons = db.execute('SELECT * FROM sermons ORDER BY date DESC LIMIT ?', (limit,)).fetchall()
        db.close()
        return sermons
    
    @staticmethod
    def create(title, preacher, date, youtube_url, description):
        """Create new sermon"""
        db = get_db()
        db.execute('INSERT INTO sermons (title, preacher, date, youtube_url, description) VALUES (?, ?, ?, ?, ?)',
                  (title, preacher, date, youtube_url, description))
        db.commit()
        db.close()
    
    @staticmethod
    def delete(sermon_id):
        """Delete sermon"""
        db = get_db()
        db.execute('DELETE FROM sermons WHERE id = ?', (sermon_id,))
        db.commit()
        db.close()
