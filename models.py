from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import re

# Initialize database (will be used by app.py)
db = SQLAlchemy()

# ============================================
# USER MODEL
# ============================================

class User(UserMixin, db.Model):
    """
    User model for authentication and profile management
    """
    __tablename__ = 'users'
    
    # ============================================
    # TABLE COLUMNS
    # ============================================
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    
    # Profile fields (optional)
    full_name = db.Column(db.String(100), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    profile_pic = db.Column(db.String(200), nullable=True)  # URL to profile picture
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Account status
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    email_verified = db.Column(db.Boolean, default=False)
    
    # ============================================
    # RELATIONSHIPS
    # ============================================
    
    # One user can have many chats
    chats = db.relationship('Chat', backref='user', lazy=True, cascade='all, delete-orphan')
    
    # ============================================
    # PROPERTIES
    # ============================================
    
    @property
    def password(self):
        """Prevent password from being accessed directly"""
        raise AttributeError('Password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        """Hash password before storing"""
        self.password_hash = generate_password_hash(password)
    
    # ============================================
    # METHODS
    # ============================================
    
    def verify_password(self, password):
        """Check if password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        """Get user's full name or username as fallback"""
        return self.full_name if self.full_name else self.username
    
    def get_chat_count(self):
        """Get total number of chats"""
        return len(self.chats) if self.chats else 0
    
    def get_recent_chats(self, limit=10):
        """Get most recent chats"""
        return Chat.query.filter_by(user_id=self.id)\
            .order_by(Chat.timestamp.desc())\
            .limit(limit).all()
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert user to dictionary for API responses"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'bio': self.bio,
            'profile_pic': self.profile_pic,
            'created_at': self.created_at.strftime('%Y-%m-%d %I:%M %p'),
            'chat_count': self.get_chat_count()
        }
    
    # ============================================
    # VALIDATION METHODS
    # ============================================
    
    @staticmethod
    def validate_username(username):
        """Validate username format"""
        if not username or len(username) < 3:
            return False, "Username must be at least 3 characters"
        if len(username) > 80:
            return False, "Username must be less than 80 characters"
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "Username can only contain letters, numbers, and underscore"
        return True, "Valid username"
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        if not email:
            return False, "Email is required"
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "Invalid email format"
        return True, "Valid email"
    
    @staticmethod
    def validate_password(password):
        """Validate password strength"""
        if not password or len(password) < 6:
            return False, "Password must be at least 6 characters"
        return True, "Valid password"
    
    # ============================================
    # STRING REPRESENTATION
    # ============================================
    
    def __repr__(self):
        return f'<User {self.username}>'


# ============================================
# CHAT MODEL
# ============================================

class Chat(db.Model):
    """
    Chat model to store conversation history
    """
    __tablename__ = 'chats'
    
    # ============================================
    # TABLE COLUMNS
    # ============================================
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    
    # Additional metadata
    message_tokens = db.Column(db.Integer, nullable=True)  # Token count for message
    response_tokens = db.Column(db.Integer, nullable=True)  # Token count for response
    response_time = db.Column(db.Float, nullable=True)  # Response time in seconds
    
    # Timestamps
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # ============================================
    # PROPERTIES
    # ============================================
    
    @property
    def message_length(self):
        """Get length of message"""
        return len(self.message) if self.message else 0
    
    @property
    def response_length(self):
        """Get length of response"""
        return len(self.response) if self.response else 0
    
    @property
    def total_tokens(self):
        """Get total tokens used"""
        return (self.message_tokens or 0) + (self.response_tokens or 0)
    
    # ============================================
    # METHODS
    # ============================================
    
    def get_summary(self):
        """Get a summary of the chat"""
        return {
            'message_preview': self.message[:100] + ('...' if len(self.message) > 100 else ''),
            'response_preview': self.response[:100] + ('...' if len(self.response) > 100 else ''),
            'timestamp': self.timestamp.strftime('%Y-%m-%d %I:%M %p'),
            'message_length': self.message_length,
            'response_length': self.response_length
        }
    
    def to_dict(self):
        """Convert chat to dictionary for API responses"""
        return {
            'id': self.id,
            'message': self.message,
            'response': self.response,
            'timestamp': self.timestamp.strftime('%I:%M %p'),
            'date': self.timestamp.strftime('%Y-%m-%d'),
            'message_length': self.message_length,
            'response_length': self.response_length
        }
    
    # ============================================
    # STRING REPRESENTATION
    # ============================================
    
    def __repr__(self):
        return f'<Chat {self.id} - User {self.user_id} - {self.timestamp.strftime("%Y-%m-%d %H:%M")}>'


# ============================================
# CREATE TABLES FUNCTION
# ============================================

def create_tables(app):
    """
    Create all database tables
    Usage: from models import create_tables; create_tables(app)
    """
    with app.app_context():
        db.create_all()
        print("✅ Database tables created successfully!")


def drop_tables(app):
    """
    Drop all database tables (use carefully!)
    """
    with app.app_context():
        db.drop_all()
        print("⚠️ All database tables dropped!")