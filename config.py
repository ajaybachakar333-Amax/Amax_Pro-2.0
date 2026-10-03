import os
from dotenv import load_dotenv
from dialogues import DIALOGUE_COMBINATION_COUNT

# Load environment variables from .env file
load_dotenv()

class Config:
    """
    Application configuration class
    All settings are loaded from environment variables
    """
    
    # ============================================
    # FLASK CORE SETTINGS
    # ============================================
    
    # Secret key for session encryption (required for Flask-Login)
    SECRET_KEY = os.getenv('SECRET_KEY', 'amax-super-secret-key-2026')
    
    # Debug mode - True for development, False for production
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # ============================================
    # DATABASE SETTINGS
    # ============================================
    
    # SQLite database file path
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'database', 'amax.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
    
    # Disable tracking modifications for better performance
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # ============================================
    # DEEPSEEK AI SETTINGS
    # ============================================
    
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '').strip()
    DEEPSEEK_API_URL = os.getenv('DEEPSEEK_API_URL', 'https://api.deepseek.com/chat/completions').strip()
    DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat').strip()
    DEEPSEEK_TEMPERATURE = 0.7
    DEEPSEEK_MAX_TOKENS = 2000
    DEEPSEEK_TIMEOUT = 30

    # Merchant UPI ID for Pro payments, configured privately in .env
    UPI_ID = os.getenv('UPI_ID', '').strip()
    PRO_PRICE = 2
    PAYMENT_WEBHOOK_SECRET = os.getenv('PAYMENT_WEBHOOK_SECRET', '').strip()

    # Number of local fallback dialogue combinations
    LOCAL_DIALOGUE_COMBINATION_COUNT = DIALOGUE_COMBINATION_COUNT
    
    # ============================================
    # RATE LIMITING SETTINGS
    # ============================================
    
    # Maximum messages per minute (prevent spam)
    MAX_MESSAGES_PER_MINUTE = 30
    
    # Maximum messages per day
    MAX_MESSAGES_PER_DAY = 500
    
    # ============================================
    # SESSION SETTINGS
    # ============================================
    
    # Session expiration time (seconds) - 7 days
    PERMANENT_SESSION_LIFETIME = 604800
    
    # ============================================
    # CHAT SETTINGS
    # ============================================
    
    # Maximum chat history to keep in context
    MAX_CONTEXT_MESSAGES = 10
    
    # Maximum message length
    MAX_MESSAGE_LENGTH = 4000
    
    # ============================================
    # SECURITY SETTINGS
    # ============================================
    
    # Password minimum length
    MIN_PASSWORD_LENGTH = 6
    
    # Allowed file extensions (if file upload is enabled)
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt'}
    
    # Maximum file size (5 MB)
    MAX_FILE_SIZE = 5 * 1024 * 1024
    
    # ============================================
    # ENVIRONMENT SPECIFIC SETTINGS
    # ============================================
    
    @staticmethod
    def is_production():
        """Check if app is running in production"""
        return os.getenv('ENV', 'development').lower() == 'production'
    
    @staticmethod
    def is_development():
        """Check if app is running in development"""
        return os.getenv('ENV', 'development').lower() == 'development'
    
    @staticmethod
    def get_env():
        """Get current environment name"""
        return os.getenv('ENV', 'development')

# ============================================
# DEVELOPMENT CONFIGURATION
# ============================================

class DevelopmentConfig(Config):
    """Development specific settings"""
    DEBUG = True
    SQLALCHEMY_ECHO = True  # Log all SQL queries for debugging

# ============================================
# PRODUCTION CONFIGURATION
# ============================================

class ProductionConfig(Config):
    """Production specific settings"""
    DEBUG = False
    SQLALCHEMY_ECHO = False  # Don't log SQL queries
    
    # Stricter security in production
    PERMANENT_SESSION_LIFETIME = 86400  # 1 day
    
    # Use different secret key for production
    SECRET_KEY = os.getenv('SECRET_KEY', 'must-change-in-production')

# ============================================
# TESTING CONFIGURATION
# ============================================

class TestingConfig(Config):
    """Testing specific settings"""
    TESTING = True
    DEBUG = True
    
    # Use separate test database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database/test.db'
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False

# ============================================
# CONFIG SELECTION (Based on environment)
# ============================================

def get_config():
    """
    Return appropriate config based on environment
    Usage: app.config.from_object(get_config())
    """
    env = os.getenv('ENV', 'development').lower()
    
    if env == 'production':
        return ProductionConfig
    elif env == 'testing':
        return TestingConfig
    else:
        return DevelopmentConfig