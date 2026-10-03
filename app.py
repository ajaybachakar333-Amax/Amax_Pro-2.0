import os
import re
import sqlite3
import shutil
import tempfile
import hashlib
import hmac
import mimetypes
import base64
import requests
import secrets
import time
from uuid import uuid4
from datetime import datetime, timedelta
from urllib.parse import quote

import werkzeug
from werkzeug.utils import secure_filename

if tuple(int(part) for part in werkzeug.__version__.split('.')[:2]) >= (3, 0):
    raise RuntimeError(
        'Incompatible Werkzeug version detected. This app requires Werkzeug<3.0.0 with Flask 2.3.x. '
        'Please run: python -m pip install -r requirements.txt'
    )

from flask import Flask, render_template, redirect, url_for, flash, request, abort, jsonify, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from dotenv import load_dotenv
from dialogues import get_dialogue_reply, get_faq_reply, get_safety_reply

# Load environment variables from .env file
load_dotenv()

# Initialize Flask App with correct paths (IMPORTANT for your CSS issue)
app = Flask(__name__, 
            template_folder='templates', 
            static_folder='static')
IS_VERCEL = os.getenv('VERCEL') == '1'
IS_PRODUCTION = os.getenv('ENV', 'development').lower() == 'production' or IS_VERCEL
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = (
    os.path.join(tempfile.gettempdir(), 'amax-uploads')
    if IS_VERCEL else os.path.join(app.static_folder, 'uploads')
)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
app.config['ALLOWED_CHAT_IMAGE_TYPES'] = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'Image is too large. Please choose an image smaller than 4 MB.'}), 413

# Secret Key (For security and sessions)
secret_key = os.getenv('SECRET_KEY', '').strip()
if IS_PRODUCTION and not secret_key:
    raise RuntimeError('SECRET_KEY must be set when ENV=production')
app.config['SECRET_KEY'] = secret_key or 'development-only-secret-change-me'
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=3650)
app.config['REMEMBER_COOKIE_REFRESH_EACH_REQUEST'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['REMEMBER_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_SAMESITE'] = 'Lax'
if IS_PRODUCTION:
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['REMEMBER_COOKIE_SECURE'] = True

# Database Configuration (SQLite)
basedir = os.path.abspath(os.path.dirname(__file__))
database_url = (os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URL') or '').strip()
if database_url.startswith('postgres://'):
    database_url = 'postgresql://' + database_url[len('postgres://'):]

if database_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    DB_PATH = database_url[len('sqlite:///'):] if database_url.startswith('sqlite:///') else None
else:
    database_dir = tempfile.gettempdir() if IS_VERCEL else os.path.join(basedir, 'database')
    os.makedirs(database_dir, exist_ok=True)
    DB_PATH = os.path.join(database_dir, 'amax.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + DB_PATH
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:'):
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'connect_args': {'timeout': 5}}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Database
db = SQLAlchemy(app)


def repair_corrupted_database():
    if not DB_PATH or not os.path.exists(DB_PATH):
        return

    try:
        with sqlite3.connect(DB_PATH) as connection:
            connection.execute('SELECT 1').fetchone()
        return
    except sqlite3.DatabaseError:
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        backup_path = f'{DB_PATH}.corrupt-{timestamp}'
        try:
            os.replace(DB_PATH, backup_path)
        except OSError:
            shutil.copy2(DB_PATH, backup_path)
            os.remove(DB_PATH)
        app.logger.warning('Corrupted SQLite database detected; moved it to %s and created a fresh database.', backup_path)


repair_corrupted_database()

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect to login page if not authenticated


@login_manager.unauthorized_handler
def unauthorized_callback():
    if request.path.startswith('/api/') or request.accept_mimetypes.accept_json:
        return jsonify({'error': 'Authentication required. Please log in again.'}), 401
    return redirect(url_for('login'))


@app.errorhandler(404)
def handle_not_found(error):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'API endpoint not found.'}), 404
    return error


@app.errorhandler(500)
def handle_internal_error(error):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'The chat service encountered an internal error. Please try again.'}), 500
    return error


# --- Database Models ---
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    full_name = db.Column(db.String(150), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    phone_number = db.Column(db.String(30), nullable=True)
    profile_photo = db.Column(db.String(255), nullable=True)
    email_verified = db.Column(db.Boolean, nullable=False, default=False)
    verification_code_hash = db.Column(db.String(128), nullable=True)
    verification_expires_at = db.Column(db.DateTime, nullable=True)
    login_otp_verified = db.Column(db.Boolean, nullable=False, default=False)
    login_otp_hash = db.Column(db.String(128), nullable=True)
    login_otp_expires_at = db.Column(db.DateTime, nullable=True)

    chats = db.relationship('Chat', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class ProPayment(db.Model):
    __tablename__ = 'pro_payments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    transaction_id = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class Chat(db.Model):
    __tablename__ = 'chats'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    title = db.Column(db.String(80), nullable=True)
    is_pinned = db.Column(db.Boolean, nullable=False, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)


def save_chat_history(user_id, message, response):
    try:
        db.session.add(Chat(user_id=user_id, message=message, response=response))
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        app.logger.exception('Chat reply could not be saved; returning it without history.')


class HelpRequest(db.Model):
    __tablename__ = 'help_requests'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(160), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending', index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)


def user_has_pro(user_id):
    return ProPayment.query.filter(
        ProPayment.user_id == user_id,
        ProPayment.status.in_(('active', 'pending')),
    ).first() is not None


def payment_webhook_is_valid(payload, signature):
    webhook_secret = os.getenv('PAYMENT_WEBHOOK_SECRET', '').strip()
    if not webhook_secret or not signature:
        return False
    expected_signature = hmac.new(
        webhook_secret.encode('utf-8'), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)


def ensure_database_schema():
    db.create_all()

    try:
        schema_inspector = inspect(db.engine)
        user_columns = {column['name'] for column in schema_inspector.get_columns('user')}
        chat_columns = {column['name'] for column in schema_inspector.get_columns('chats')}
        view_names = set(schema_inspector.get_view_names())
    except Exception:
        user_columns = set()
        chat_columns = set()
        view_names = set()

    additions = {
        'full_name': 'VARCHAR(150)',
        'date_of_birth': 'DATE',
        'phone_number': 'VARCHAR(30)',
        'profile_photo': 'VARCHAR(255)',
        'email_verified': 'BOOLEAN NOT NULL DEFAULT 1',
        'verification_code_hash': 'VARCHAR(128)',
        'verification_expires_at': 'DATETIME',
        'login_otp_verified': 'BOOLEAN NOT NULL DEFAULT 0',
        'login_otp_hash': 'VARCHAR(128)',
        'login_otp_expires_at': 'DATETIME',
    }
    chat_additions = {
        'title': 'VARCHAR(80)',
        'is_pinned': 'BOOLEAN NOT NULL DEFAULT FALSE',
    }

    with db.engine.begin() as connection:
        if 'users' not in view_names:
            try:
                connection.execute(text('CREATE VIEW users AS SELECT * FROM user'))
            except Exception:
                pass

        for column_name, column_type in additions.items():
            if column_name not in user_columns:
                try:
                    connection.execute(text(f'ALTER TABLE user ADD COLUMN {column_name} {column_type}'))
                except Exception:
                    pass

        for column_name, column_type in chat_additions.items():
            if column_name not in chat_columns:
                try:
                    connection.execute(text(f'ALTER TABLE chats ADD COLUMN {column_name} {column_type}'))
                except Exception:
                    pass

        # Accounts created before email verification was introduced are already trusted.
        # Leave only users with an active verification code pending.
        try:
            needs_legacy_verification_update = connection.execute(text(
                'SELECT 1 FROM user '
                'WHERE email_verified = 0 AND verification_code_hash IS NULL LIMIT 1'
            )).first()
            if needs_legacy_verification_update:
                connection.execute(text(
                    'UPDATE user SET email_verified = 1 '
                    'WHERE email_verified = 0 AND verification_code_hash IS NULL'
                ))
        except Exception:
            pass


with app.app_context():
    ensure_database_schema()


APP_PAGES = [
    {"slug": "ai-assistant", "title": "AI Assistant", "category": "Core", "badge": "Smart", "description": "Conversational intelligence for actionable answers and support."},
    {"slug": "chat-workspace", "title": "Chat Workspace", "category": "Core", "badge": "Live", "description": "Collaborative AI chat for brainstorming and daily tasks."},
    {"slug": "voice-chat", "title": "Voice Chat", "category": "Core", "badge": "New", "description": "Voice-driven prompts and faster AI interaction flows."},
    {"slug": "smart-search", "title": "Smart Search", "category": "Core", "badge": "Fast", "description": "Search with context-aware summaries and discovery."},
    {"slug": "writing-studio", "title": "Writing Studio", "category": "Creator", "badge": "Pro", "description": "Create cleaner content, drafts, and polished marketing text."},
    {"slug": "code-helper", "title": "Code Helper", "category": "Developer", "badge": "Dev", "description": "Generate logic, debug ideas, and improve implementation flow."},
    {"slug": "summarizer", "title": "Summarizer", "category": "Productivity", "badge": "AI", "description": "Turn long documents into short, useful summaries."},
    {"slug": "planner", "title": "Daily Planner", "category": "Productivity", "badge": "Plan", "description": "Prioritize work and organize your next actions."},
    {"slug": "analytics", "title": "Analytics", "category": "Insights", "badge": "Data", "description": "Track useful insights from your conversations and tasks."},
    {"slug": "insight-boards", "title": "Insight Boards", "category": "Insights", "badge": "Board", "description": "Visualize trends and decision-ready summaries."},
    {"slug": "automations", "title": "Automations", "category": "Automation", "badge": "Flow", "description": "Trigger smart actions across common daily routines."},
    {"slug": "assistant-hub", "title": "Assistant Hub", "category": "Core", "badge": "Hub", "description": "One place for every AI interaction and quick action."},
    {"slug": "career-coach", "title": "Career Coach", "category": "Growth", "badge": "Career", "description": "Guidance for resume, goals, learning, and productivity."},
    {"slug": "learning-lab", "title": "Learning Lab", "category": "Growth", "badge": "Learn", "description": "Personalized learning support and guidance."},
    {"slug": "brainstorm", "title": "Brainstorm", "category": "Ideas", "badge": "Idea", "description": "Generate fresh ideas and build concepts faster."},
    {"slug": "marketing-kit", "title": "Marketing Kit", "category": "Creator", "badge": "Brand", "description": "Campaign ideas, social content, and product messaging."},
    {"slug": "design-helper", "title": "Design Helper", "category": "Creator", "badge": "UI", "description": "Support for layouts, styling, and product thinking."},
    {"slug": "meeting-notes", "title": "Meeting Notes", "category": "Work", "badge": "Notes", "description": "Turn discussions into structured follow-up items."},
    {"slug": "email-writer", "title": "Email Writer", "category": "Communication", "badge": "Email", "description": "Better outreach, replies, and customer conversations."},
    {"slug": "study-buddy", "title": "Study Buddy", "category": "Education", "badge": "Study", "description": "Quick revision help and brainstorming for learning."},
    {"slug": "project-brief", "title": "Project Brief", "category": "Work", "badge": "Brief", "description": "Build clear plans and scopes for new work."},
    {"slug": "content-calendar", "title": "Content Calendar", "category": "Marketing", "badge": "Cal", "description": "Schedule and organize campaigns and publishing ideas."},
    {"slug": "social-posts", "title": "Social Posts", "category": "Marketing", "badge": "Social", "description": "Reusable ideas for posts, promos, and engagement."},
    {"slug": "sales-coach", "title": "Sales Coach", "category": "Business", "badge": "Sales", "description": "Support for messaging, pitches, and outreach."},
    {"slug": "support-bot", "title": "Support Bot", "category": "Business", "badge": "Help", "description": "Reply to customers or create service templates."},
    {"slug": "knowledge-base", "title": "Knowledge Base", "category": "Business", "badge": "KB", "description": "Store critical info and quick reference guidance."},
    {"slug": "wellness-check", "title": "Wellness Check", "category": "Life", "badge": "Well", "description": "Focused support for habits, routines, and balance."},
    {"slug": "travel-planner", "title": "Travel Planner", "category": "Life", "badge": "Travel", "description": "Plan itineraries, budgets, and trip ideas."},
    {"slug": "finance-helper", "title": "Finance Helper", "category": "Life", "badge": "Money", "description": "Budget checks, planning, and spending awareness."},
    {"slug": "language-partner", "title": "Language Partner", "category": "Learning", "badge": "Lang", "description": "Support for practice, translation, and improvement."},
    {"slug": "role-play", "title": "Role Play", "category": "Learning", "badge": "Role", "description": "Practice interview, negotiation, and communication scenes."},
    {"slug": "customer-insights", "title": "Customer Insights", "category": "Research", "badge": "Insight", "description": "Summarize research and feedback better."},
    {"slug": "market-research", "title": "Market Research", "category": "Research", "badge": "Market", "description": "Analyze trends and articulate opportunities."},
    {"slug": "roadmap", "title": "Product Roadmap", "category": "Strategy", "badge": "Plan", "description": "Organize launch ideas and milestones."},
    {"slug": "risk-check", "title": "Risk Check", "category": "Strategy", "badge": "Risk", "description": "Review business risks and contingency planning."},
    {"slug": "decision-maker", "title": "Decision Maker", "category": "Strategy", "badge": "Decide", "description": "Evaluate options, trade-offs, and choices."},
    {"slug": "faq-center", "title": "FAQ Center", "category": "Support", "badge": "FAQ", "description": "Reusable answers and help content."},
    {"slug": "help-desk", "title": "Help Desk", "category": "Support", "badge": "Help", "description": "Support frames for users and internal answers."},
    {"slug": "security-center", "title": "Security Center", "category": "Security", "badge": "Safe", "description": "Tips and patterns for secure usage."},
    {"slug": "privacy-guide", "title": "Privacy Guide", "category": "Security", "badge": "Privacy", "description": "Understand and apply better digital privacy habits."},
    {"slug": "api-console", "title": "API Console", "category": "Developer", "badge": "API", "description": "Build and test smarter integrations."},
    {"slug": "webhooks", "title": "Webhooks", "category": "Developer", "badge": "Hook", "description": "Connect actions and trigger events."},
    {"slug": "templates", "title": "Templates", "category": "Work", "badge": "Kit", "description": "Ready-made systems for everyday tasks."},
    {"slug": "workflow-builder", "title": "Workflow Builder", "category": "Automation", "badge": "Build", "description": "Structure repeatable work patterns."},
    {"slug": "research-assistant", "title": "Research Assistant", "category": "Research", "badge": "Research", "description": "Collect, compare, and synthesize information faster."},
    {"slug": "story-creator", "title": "Story Creator", "category": "Creator", "badge": "Story", "description": "Turn themes into narratives and blog drafts."},
    {"slug": "brand-builder", "title": "Brand Builder", "category": "Marketing", "badge": "Brand", "description": "Develop consistent tone and positioning ideas."},
    {"slug": "team-collab", "title": "Team Collab", "category": "Work", "badge": "Team", "description": "Align discussions and team planning in one space."},
    {"slug": "document-mentor", "title": "Document Mentor", "category": "Work", "badge": "Doc", "description": "Refine documents, reports, and proposals."},
    {"slug": "onboarding", "title": "Onboarding", "category": "Work", "badge": "New", "description": "Make onboarding flows easy for teams and members."},
    {"slug": "community-hub", "title": "Community Hub", "category": "Community", "badge": "Com", "description": "Build user groups, channels, and community touchpoints."},
    {"slug": "events-planner", "title": "Events Planner", "category": "Community", "badge": "Event", "description": "Plan event ideas, timing, and outreach."},
    {"slug": "content-editor", "title": "Content Editor", "category": "Creator", "badge": "Edit", "description": "Polish language, tone, and structure for content."},
    {"slug": "smart-calendar", "title": "Smart Calendar", "category": "Productivity", "badge": "Cal", "description": "Plan time blocks and important milestones."},
    {"slug": "alerts", "title": "Smart Alerts", "category": "Productivity", "badge": "Alert", "description": "Get reminders and summary nudges for key tasks."},
    {"slug": "feedback-loop", "title": "Feedback Loop", "category": "Insights", "badge": "Loop", "description": "Collect and organize useful user feedback."},
    {"slug": "ideas-lab", "title": "Ideas Lab", "category": "Ideas", "badge": "Lab", "description": "Test and refine ideas quickly before execution."},
    {"slug": "mission-control", "title": "Mission Control", "category": "Operations", "badge": "Ops", "description": "View the most important tasks and project status."},
    {"slug": "report-builder", "title": "Report Builder", "category": "Operations", "badge": "Report", "description": "Create clear progress reports and summaries."},
    {"slug": "priority-map", "title": "Priority Map", "category": "Operations", "badge": "Map", "description": "Focus attention on the highest-value actions."},
    {"slug": "memory-bank", "title": "Memory Bank", "category": "Knowledge", "badge": "Bank", "description": "Store knowledge fragments and reusable context."},
    {"slug": "decision-tree", "title": "Decision Tree", "category": "Strategy", "badge": "Tree", "description": "Map decisions and outcomes for better choices."}
]

APP_PAGES.extend([
    {"slug": "article-explorer", "title": "Article Explorer", "category": "Knowledge", "badge": "Read", "description": "Explore concise articles with context, sources, and key ideas."},
    {"slug": "fact-checker", "title": "Fact Checker", "category": "Knowledge", "badge": "Verify", "description": "Separate supported facts from assumptions and unclear claims."},
    {"slug": "citation-finder", "title": "Citation Finder", "category": "Research", "badge": "Source", "description": "Organize reliable references for research and writing."},
    {"slug": "knowledge-graph", "title": "Knowledge Graph", "category": "Knowledge", "badge": "Map", "description": "Connect people, places, ideas, and events through relationships."},
    {"slug": "topic-timeline", "title": "Topic Timeline", "category": "Knowledge", "badge": "Time", "description": "Understand how a subject changes across important dates."},
    {"slug": "biography-builder", "title": "Biography Builder", "category": "History", "badge": "People", "description": "Create clear, structured profiles of notable people."},
    {"slug": "history-atlas", "title": "History Atlas", "category": "History", "badge": "World", "description": "Place historical events in geographic and cultural context."},
    {"slug": "science-lab", "title": "Science Lab", "category": "Science", "badge": "Explore", "description": "Break scientific concepts into experiments and explanations."},
    {"slug": "space-observer", "title": "Space Observer", "category": "Science", "badge": "Cosmos", "description": "Learn about planets, stars, missions, and the universe."},
    {"slug": "earth-guide", "title": "Earth Guide", "category": "Science", "badge": "Planet", "description": "Explore climate, geology, ecosystems, and natural systems."},
    {"slug": "medicine-glossary", "title": "Medicine Glossary", "category": "Reference", "badge": "Terms", "description": "Understand medical terms with careful, plain-language context."},
    {"slug": "law-explainer", "title": "Law Explainer", "category": "Reference", "badge": "Civic", "description": "Learn general legal concepts without replacing professional advice."},
    {"slug": "economics-guide", "title": "Economics Guide", "category": "Reference", "badge": "Market", "description": "Understand markets, incentives, trade, and policy basics."},
    {"slug": "government-guide", "title": "Government Guide", "category": "Civics", "badge": "Civic", "description": "Explore institutions, public services, and civic processes."},
    {"slug": "culture-encyclopedia", "title": "Culture Encyclopedia", "category": "Culture", "badge": "Culture", "description": "Discover traditions, language, art, and shared cultural history."},
    {"slug": "language-dictionary", "title": "Language Dictionary", "category": "Language", "badge": "Words", "description": "Learn definitions, usage, pronunciation, and related words."},
    {"slug": "translation-guide", "title": "Translation Guide", "category": "Language", "badge": "Translate", "description": "Compare meaning, tone, and usage across languages."},
    {"slug": "literature-library", "title": "Literature Library", "category": "Culture", "badge": "Books", "description": "Explore authors, genres, themes, and literary movements."},
    {"slug": "art-history", "title": "Art History", "category": "Culture", "badge": "Visual", "description": "Connect artworks with artists, periods, and visual ideas."},
    {"slug": "music-history", "title": "Music History", "category": "Culture", "badge": "Sound", "description": "Trace genres, instruments, movements, and influential artists."},
    {"slug": "film-reference", "title": "Film Reference", "category": "Culture", "badge": "Screen", "description": "Organize film topics, genres, creators, and historical context."},
    {"slug": "geography-guide", "title": "Geography Guide", "category": "World", "badge": "Places", "description": "Learn about regions, borders, landscapes, and populations."},
    {"slug": "country-profile", "title": "Country Profiles", "category": "World", "badge": "Nations", "description": "Compare countries through geography, history, and civic facts."},
    {"slug": "city-guide", "title": "City Guide", "category": "World", "badge": "Cities", "description": "Build an informative overview of a city and its neighborhoods."},
    {"slug": "map-compare", "title": "Map Compare", "category": "World", "badge": "Compare", "description": "Compare locations, distances, regions, and geographic patterns."},
    {"slug": "invention-index", "title": "Invention Index", "category": "Technology", "badge": "Ideas", "description": "Trace inventions, inventors, and the problems they solved."},
    {"slug": "technology-history", "title": "Technology History", "category": "Technology", "badge": "Timeline", "description": "Understand how technologies evolved and shaped everyday life."},
    {"slug": "computer-science", "title": "Computer Science", "category": "Technology", "badge": "Logic", "description": "Learn algorithms, systems, data, and computing fundamentals."},
    {"slug": "internet-guide", "title": "Internet Guide", "category": "Technology", "badge": "Web", "description": "Understand browsers, networks, protocols, and online services."},
    {"slug": "data-literacy", "title": "Data Literacy", "category": "Insights", "badge": "Data", "description": "Read charts, question claims, and reason from evidence."},
    {"slug": "statistics-helper", "title": "Statistics Helper", "category": "Insights", "badge": "Numbers", "description": "Understand averages, probability, samples, and uncertainty."},
    {"slug": "research-notebook", "title": "Research Notebook", "category": "Research", "badge": "Notes", "description": "Collect questions, evidence, summaries, and open research paths."},
    {"slug": "source-compare", "title": "Source Compare", "category": "Research", "badge": "Review", "description": "Compare sources by evidence, date, perspective, and reliability."},
    {"slug": "question-generator", "title": "Question Generator", "category": "Learning", "badge": "Ask", "description": "Turn any topic into useful questions for deeper understanding."},
    {"slug": "study-guide-maker", "title": "Study Guide Maker", "category": "Learning", "badge": "Review", "description": "Turn a subject into definitions, examples, and practice prompts."},
    {"slug": "concept-explainer", "title": "Concept Explainer", "category": "Learning", "badge": "Clear", "description": "Explain difficult ideas with analogies and progressive detail."},
    {"slug": "quiz-builder", "title": "Quiz Builder", "category": "Learning", "badge": "Practice", "description": "Create quizzes that test recall, reasoning, and application."},
    {"slug": "glossary-maker", "title": "Glossary Maker", "category": "Reference", "badge": "Terms", "description": "Build a focused glossary for any subject or project."},
    {"slug": "faq-builder", "title": "FAQ Builder", "category": "Reference", "badge": "Answers", "description": "Turn repeated questions into clear, searchable answers."},
    {"slug": "timeline-builder", "title": "Timeline Builder", "category": "History", "badge": "Events", "description": "Arrange events into a readable timeline with key milestones."},
    {"slug": "archive-organizer", "title": "Archive Organizer", "category": "Knowledge", "badge": "Archive", "description": "Sort notes and documents into a searchable knowledge archive."},
    {"slug": "fact-summary", "title": "Fact Summary", "category": "Knowledge", "badge": "Brief", "description": "Turn a broad topic into a balanced, quick reference summary."},
    {"slug": "pros-cons-research", "title": "Pros and Cons Research", "category": "Research", "badge": "Balance", "description": "Compare competing views with evidence and clearly stated limits."},
    {"slug": "reading-companion", "title": "Reading Companion", "category": "Learning", "badge": "Read", "description": "Discuss chapters, themes, vocabulary, and follow-up questions."},
    {"slug": "document-index", "title": "Document Index", "category": "Knowledge", "badge": "Index", "description": "Create a clean index for documents, topics, and references."},
    {"slug": "idea-chronicle", "title": "Idea Chronicle", "category": "Knowledge", "badge": "Trace", "description": "Follow how an idea developed from its origin to today."},
    {"slug": "reference-dashboard", "title": "Reference Dashboard", "category": "Knowledge", "badge": "Hub", "description": "Bring summaries, sources, timelines, and notes into one view."},
    {"slug": "open-knowledge", "title": "Open Knowledge", "category": "Knowledge", "badge": "Explore", "description": "Navigate connected topics and discover useful next questions."},
])

CATEGORY_DETAILS = {
    'Core': [
        'Fast workflows designed for daily productivity',
        'User-friendly actions with clear AI support',
        'Helpful outputs that are practical and easy to use',
    ],
    'Creator': [
        'Ideas and drafts built for content creation',
        'Better messaging, copy, and visual thinking',
        'Creative direction that is clear and reusable',
    ],
    'Developer': [
        'Logic and structure for coding tasks',
        'Debugging help and implementation guidance',
        'Clear, practical output for technical work',
    ],
    'Productivity': [
        'Planning tools for time, tasks, and follow-through',
        'Clear summaries and smarter daily operations',
        'Focused support for managing important work',
    ],
    'Insights': [
        'Summaries and comparisons based on evidence',
        'Pattern recognition for decisions and trends',
        'Actionable insights for smarter next steps',
    ],
    'Automation': [
        'Repeatable systems for everyday busywork',
        'Workflow logic that saves time and effort',
        'Smart triggers and structured execution steps',
    ],
    'Growth': [
        'Career and learning support for progress',
        'Clear guidance for development and opportunity',
        'Practical steps for long-term improvement',
    ],
    'Ideas': [
        'Fresh concepts and exploration of possibilities',
        'Brainstorming flows that stay actionable',
        'Creative thinking built for fast iteration',
    ],
    'Communication': [
        'Better writing for outreach and collaboration',
        'Helpful messaging, responses, and follow-up',
        'Clear communication that feels professional',
    ],
    'Education': [
        'Learning support for revision and understanding',
        'Short explanations and better study habits',
        'Questions and examples that improve retention',
    ],
    'Work': [
        'Collaboration support for diaries, meetings, and tasks',
        'Better planning and structured execution',
        'Clear outputs for everyday business workflows',
    ],
    'Marketing': [
        'Campaign ideas and stronger brand positioning',
        'Content systems that are creative and reusable',
        'Clear strategy, messaging, and engagement support',
    ],
    'Business': [
        'Practical support for selling and service work',
        'Helpful guidance for customer and team communication',
        'Clear paths for smarter business execution',
    ],
    'Support': [
        'Clear help flows and reusable answer patterns',
        'Support tools built for speed and consistency',
        'Strong customer and team response guidance',
    ],
    'Security': [
        'Protection-first habits for digital work',
        'Safer systems and responsible usage patterns',
        'Clear guidance for privacy and security practice',
    ],
    'Research': [
        'Evidence-first workflows and structured review',
        'Faster investigation and comparison of sources',
        'Clear summaries for research momentum',
    ],
    'Strategy': [
        'Better options and trade-off analysis',
        'Roadmaps and decision frameworks',
        'Focused planning for business direction',
    ],
    'Life': [
        'Support for daily habits and useful personal planning',
        'Practical routines with clear next steps',
        'Balance, health, and planning in one place',
    ],
    'Learning': [
        'A structured path for understanding and practice',
        'Clear examples that build confidence',
        'Progressive learning with extra context and review',
    ],
    'Knowledge': [
        'Better understanding through organized information',
        'Helpful summaries, references, and context',
        'Searchable knowledge that supports follow-up questions',
    ],
    'History': [
        'Context-rich understanding through timelines and stories',
        'Clear comparisons across events and societies',
        'Better historical framing and sequence of ideas',
    ],
    'Science': [
        'Curious and evidence-led explanation of systems',
        'Simple learning pathways for complex topics',
        'Helpful structure for experiments and discovery',
    ],
    'Reference': [
        'Quick-access explanations and subject guides',
        'Useful vocabulary and concept clarity',
        'Clear framing for technical or academic topics',
    ],
    'Culture': [
        'Broader context through art, literature, and traditions',
        'Meaningful cultural understanding and comparison',
        'Creative context for living and learning',
    ],
    'Language': [
        'Better vocabulary, translation, and expression',
        'Clear support for learning and communicating well',
        'Useful comparisons across meaning and intent',
    ],
    'World': [
        'Geography and place-based understanding',
        'Better regional context and comparison',
        'Helpful overviews for cities, countries, and maps',
    ],
    'Technology': [
        'A clear view of how digital systems work',
        'Helpful concepts for learning and building',
        'Practical understanding of modern tools',
    ],
    'Operations': [
        'Useful visibility into execution and progress',
        'Better prioritization and reporting workflows',
        'Thoughtful coordination for day-to-day work',
    ],
    'Community': [
        'Support for engagement, events, and interaction',
        'Better information flow across groups and members',
        'Clear community organization and planning',
    ],
}

for page in APP_PAGES:
    page['details'] = page.get('details') or CATEGORY_DETAILS.get(page.get('category'), [
        'AI-first workflow support',
        'Practical outputs for rapid progress',
        'A clear experience designed for real work',
    ])

FEATURE_DETAILS = [
    {
        'slug': 'intelligent-ai',
        'title': 'Intelligent AI',
        'category': 'Core Feature',
        'badge': 'Reasoning',
        'description': 'Get thoughtful, conversational answers that understand context and turn complex requests into practical next steps.',
        'details': [
            'Context-aware conversations for follow-up questions',
            'Structured answers for research, planning, writing, and coding',
            'Helpful fallback responses when an answer is unavailable',
        ],
    },
    {
        'slug': 'private-secure',
        'title': 'Private & Secure',
        'category': 'Trust & Safety',
        'badge': 'Protected',
        'description': 'Use a personal workspace with protected authentication, private conversations, and controlled account access.',
        'details': [
            'Secure password hashing for account credentials',
            'Login-protected chat and profile areas',
            'User-specific conversation history and profile data',
        ],
    },
    {
        'slug': 'conversation-memory',
        'title': 'Conversation Memory',
        'category': 'Productivity',
        'badge': 'Organized',
        'description': 'Keep important conversations accessible so you can review decisions, revisit ideas, and continue work later.',
        'details': [
            'Saved chat messages and AI responses in your history',
            'Recent conversations visible from your profile',
            'Clear-history control when you want a fresh workspace',
        ],
    },
    {
        'slug': 'instant-answers',
        'title': 'Instant Answers',
        'category': 'Speed & Workflow',
        'badge': 'Fast',
        'description': 'Move from question to useful action quickly with focused replies for brainstorming, support, and everyday planning.',
        'details': [
            'Fast chat interface with a live thinking indicator',
            'Quick suggestions for common questions',
            'Image upload support for visual analysis workflows',
        ],
    },
]


# --- User Loader for Flask-Login ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# --- Routes ---

@app.route('/')
def home():
    pro_active = current_user.is_authenticated and user_has_pro(current_user.id)
    return render_template('index.html', user=current_user, page_count=len(APP_PAGES), pro_active=pro_active)

@app.route('/contact')
def contact():
    return render_template('contact.html', user=current_user, developer_name='Ajay Bachkar', contact_email='ajaybachkar02@gmail.com')

@app.route('/help-desk', methods=['GET', 'POST'])
def help_desk():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

        if not name or not email or not subject or not message:
            flash('Please complete all Help Desk fields.', 'error')
            return render_template('help_desk.html', user=current_user, form=request.form)
        if len(message) < 10:
            flash('Please describe the problem in at least 10 characters.', 'error')
            return render_template('help_desk.html', user=current_user, form=request.form)
        if len(message) > 5000:
            flash('Your problem description must be 5000 characters or fewer.', 'error')
            return render_template('help_desk.html', user=current_user, form=request.form)

        help_request = HelpRequest(
            user_id=current_user.id if current_user.is_authenticated else None,
            name=name,
            email=email,
            subject=subject,
            message=message,
        )
        db.session.add(help_request)
        db.session.commit()
        flash('Your Help Desk message was sent. We will review it soon.', 'success')
        return redirect(url_for('help_desk'))

    default_form = {
        'name': current_user.full_name or current_user.username if current_user.is_authenticated else '',
        'email': current_user.email if current_user.is_authenticated else '',
    }
    return render_template('help_desk.html', user=current_user, form=default_form)

@app.route('/pricing')
@login_required
def pricing():
    upi_id = (os.getenv('UPI_ID') or 'bachkarajay@ybl').strip()
    pro_price = 2
    upi_link = ''
    if upi_id:
        upi_link = (
            f'upi://pay?pa={quote(upi_id)}&pn={quote("AMAX")}'
            f'&am={pro_price}&cu=INR&tn={quote("AMAX Pro subscription")}'
        )
    pro_active = current_user.is_authenticated and user_has_pro(current_user.id)
    payment_confirmed = request.args.get('confirmed') == '1'
    return render_template(
        'pricing.html',
        upi_id=upi_id,
        upi_link=upi_link,
        pro_price=pro_price,
        pro_active=pro_active,
        payment_confirmed=payment_confirmed,
    )

@app.route('/pricing/confirm', methods=['POST'])
@login_required
def confirm_pro_payment():
    transaction_id = (
        request.form.get('transaction_id')
        or request.form.get('utr_code')
        or ''
    ).strip()
    if not transaction_id or len(transaction_id) > 120:
        flash('Enter the UPI transaction ID or UTR after payment.', 'error')
        return redirect(url_for('pricing'))

    existing_payment = ProPayment.query.filter_by(transaction_id=transaction_id).first()
    if existing_payment and existing_payment.user_id != current_user.id:
        flash('This transaction ID is already linked to another account.', 'error')
        return redirect(url_for('pricing'))

    payment = existing_payment or ProPayment(
        user_id=current_user.id,
        transaction_id=transaction_id,
    )
    payment.user_id = current_user.id
    payment.transaction_id = transaction_id
    payment.status = 'active'
    db.session.add(payment)
    db.session.commit()
    flash('Payment confirmed successfully! Pro has been unlocked.', 'success')
    return redirect(url_for('pricing', confirmed=1))

@app.route('/api/payments/webhook', methods=['POST'])
def payment_webhook():
    payload = request.get_data()
    signature = request.headers.get('X-Payment-Signature', '')
    if not payment_webhook_is_valid(payload, signature):
        return jsonify({'error': 'Invalid payment webhook signature'}), 401

    data = request.get_json(silent=True) or {}
    if str(data.get('status', '')).lower() not in {'paid', 'success', 'captured'}:
        return jsonify({'received': True, 'updated': False})

    user_id = data.get('user_id')
    payment_id = str(data.get('payment_id') or data.get('transaction_id') or '').strip()
    if not payment_id:
        return jsonify({'error': 'payment_id or transaction_id is required'}), 400

    payment = ProPayment.query.filter_by(transaction_id=payment_id).first()
    if payment is None:
        if not user_id:
            return jsonify({'error': 'user_id is required for an unknown payment'}), 400
        payment = ProPayment(user_id=int(user_id), transaction_id=payment_id)
        db.session.add(payment)
    elif user_id and payment.user_id != int(user_id):
        return jsonify({'error': 'Payment does not belong to this user'}), 409
    payment.status = 'active'
    db.session.commit()
    return jsonify({'received': True, 'pro_unlocked': True})

@app.route('/api/pro-status')
@login_required
def pro_status():
    return jsonify({'pro_active': user_has_pro(current_user.id)})

@app.route('/pages')
def pages_directory():
    return render_template('pages_directory.html', pages=APP_PAGES, user=current_user)

@app.route('/pages/<slug>')
def page_detail(slug):
    page = next((item for item in APP_PAGES if item['slug'] == slug), None)
    if page is None:
        abort(404)
    return render_template('page.html', page=page, user=current_user)

@app.route('/features/<slug>')
def feature_detail(slug):
    feature = next((item for item in FEATURE_DETAILS if item['slug'] == slug), None)
    if feature is None:
        abort(404)
    return render_template('page.html', page=feature, user=current_user)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user, pages=APP_PAGES[:8], pro_active=user_has_pro(current_user.id))

@app.route('/profile')
@login_required
def profile():
    history = Chat.query.filter_by(user_id=current_user.id).order_by(Chat.timestamp.desc()).limit(20).all()
    return render_template('profile.html', user=current_user, history=history, pro_active=user_has_pro(current_user.id))

@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    if 'full_name' in request.form:
        current_user.full_name = request.form.get('full_name', '').strip() or None
    if 'phone_number' in request.form:
        current_user.phone_number = request.form.get('phone_number', '').strip() or None
    if 'date_of_birth' in request.form:
        date_of_birth = request.form.get('date_of_birth', '').strip()
        try:
            current_user.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date() if date_of_birth else None
        except ValueError:
            flash('Please enter a valid date of birth.', 'error')
            return redirect(url_for('profile'))

    photo = request.files.get('profile_photo')
    if photo and photo.filename:
        extension = os.path.splitext(photo.filename)[1].lower()
        if extension not in {'.jpg', '.jpeg', '.png', '.gif', '.webp'}:
            flash('Please upload a JPG, PNG, GIF, or WEBP photo.', 'error')
            return redirect(url_for('profile'))
        filename = f'user_{current_user.id}{extension}'
        photo.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename)))
        current_user.profile_photo = filename

    db.session.commit()
    flash('Profile updated successfully.', 'success')
    return redirect(url_for('profile'))

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html', user=current_user)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if is_disposable_email(email):
            flash('Temporary or disposable email addresses are not supported.', 'error')
            return render_template('signup.html', username=username, email=email, errors=['Please use a permanent Gmail address.'])

        if not is_valid_gmail_address(email):
            flash('Please use a valid Gmail address.', 'error')
            return render_template('signup.html', username=username, email=email, errors=['Only permanent @gmail.com addresses can be used.'])

        if not re.fullmatch(r'[A-Za-z0-9_]{3,80}', username):
            flash('Username must contain only letters, numbers, and underscore.', 'error')
            return render_template('signup.html', username=username, email=email)

        if len(password) < 6 or password != request.form.get('confirm_password', ''):
            flash('Please enter matching passwords of at least 6 characters.', 'error')
            return render_template('signup.html', username=username, email=email)

        existing_user = User.query.filter_by(email=email).first()
        other_user_with_same_username = User.query.filter(
            db.func.lower(User.username) == username.lower()
        ).first()
        if other_user_with_same_username and (existing_user is None or other_user_with_same_username.id != existing_user.id):
            flash('This username is already taken. Please choose a different username.', 'error')
            return render_template('signup.html', username=username, email=email)

        if existing_user:
            if existing_user.email_verified:
                flash('Email already registered. Please login.', 'error')
                return redirect(url_for('login'))
            db.session.delete(existing_user)
            db.session.flush()

        new_user = User(username=username, email=email)
        new_user.set_password(password)
        new_user.email_verified = True
        new_user.login_otp_verified = True

        try:
            for attempt in range(3):
                db.session.add(new_user)
                try:
                    db.session.commit()
                    break
                except OperationalError as error:
                    db.session.rollback()
                    if 'database is locked' not in str(error).lower() or attempt == 2:
                        raise
                    time.sleep(0.25 * (attempt + 1))
        except SQLAlchemyError:
            db.session.rollback()
            app.logger.exception('Could not save the new account.')
            flash('The account database is busy. Please try signing up again in a few seconds.', 'error')
            return render_template('signup.html', username=username, email=email)
        
        flash('Account created successfully. Login with your Gmail and password.', 'success')
        return redirect(url_for('login'))
        
    return render_template('signup.html')


def is_valid_gmail_address(email):
    """Validate Gmail address syntax before inbox ownership verification."""
    if len(email) > 254 or '@' not in email:
        return False
    local_part, domain = email.rsplit('@', 1)
    if domain != 'gmail.com' or not 1 <= len(local_part) <= 64:
        return False
    if local_part.startswith('.') or local_part.endswith('.') or '..' in local_part:
        return False
    return re.fullmatch(r"[a-z0-9.!#$%&'*+/=?^_`{|}~-]+", local_part) is not None


DEFAULT_DISPOSABLE_EMAIL_DOMAINS = {
    '10minutemail.com', '20minutemail.com', 'dispostable.com', 'emailondeck.com',
    'fakeinbox.com', 'guerrillamail.com', 'guerrillamailblock.com', 'maildrop.cc',
    'mailinator.com', 'mintemail.com', 'moakt.com', 'sharklasers.com',
    'temp-mail.org', 'temp-mail.io', 'tempmail.com', 'tempmailo.com',
    'throwawaymail.com', 'trashmail.com', 'yopmail.com',
}


def is_disposable_email(email):
    """Return True for known temporary domains and configured blocked domains."""
    if '@' not in email:
        return False
    domain = email.rsplit('@', 1)[1].strip().lower().rstrip('.')
    configured_domains = {
        item.strip().lower().rstrip('.')
        for item in os.getenv('DISPOSABLE_EMAIL_DOMAINS', '').split(',')
        if item.strip()
    }
    return domain in DEFAULT_DISPOSABLE_EMAIL_DOMAINS | configured_domains


def email_verification_required():
    return False


@app.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    flash('Email verification is disabled in this project.', 'info')
    return redirect(url_for('login'))


@app.route('/verify-login-otp', methods=['GET', 'POST'])
def verify_login_otp():
    flash('Login OTP verification is disabled in this project.', 'info')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_id = (request.form.get('login_id') or request.form.get('email') or '').strip()
        email = login_id.lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()
        if not user and login_id:
            user = User.query.filter(db.func.lower(User.username) == login_id.lower()).first()

        if login_id.lower() == 'demo' and password == 'xyz':
            flash('Demo access is disabled. Please create a new account first.', 'error')
            return redirect(url_for('login'))

        if not user:
            flash('Invalid username, Gmail ID, or password.', 'error')
            return redirect(url_for('login'))
        if not user.check_password(password):
            flash('Invalid username, Gmail ID, or password.', 'error')
            return redirect(url_for('login'))

        login_user(user, remember=True)
        return redirect(url_for('chat'))

    return render_template('login.html')

@app.route('/chat')
@login_required
def chat():
    history = Chat.query.filter_by(user_id=current_user.id).order_by(
        Chat.is_pinned.desc(), Chat.timestamp.desc()
    ).limit(40).all()
    return render_template('chat.html', user=current_user, pro_active=user_has_pro(current_user.id), history=history)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    if filename.startswith('uploads/'):
        filename = filename[len('uploads/'):]
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- AI API Setup ---
gemini_api_key = os.getenv('GEMINI_API_KEY', os.getenv('GOOGLE_API_KEY', '')).strip()
gemini_key_is_configured = bool(gemini_api_key)
gemini_model = os.getenv('GEMINI_MODEL', 'gemini-3.5-flash-lite').strip()
gemini_api_url = os.getenv(
    'GEMINI_API_URL',
    'https://generativelanguage.googleapis.com/v1beta/models',
).strip()

deepseek_api_key = os.getenv('DEEPSEEK_API_KEY', '').strip()
deepseek_key_is_configured = bool(deepseek_api_key)
deepseek_model = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat').strip()
deepseek_api_url = os.getenv(
    'DEEPSEEK_API_URL',
    'https://api.deepseek.com/chat/completions',
).strip()
NO_ANSWER_REPLY = 'This bot is under construction and does not have an answer for that yet.'
IMAGE_UNSUPPORTED_REPLY = 'AMAX can receive images, but image analysis is not available yet. Please describe what you want to check in the message.'
IMAGE_RECEIVED_REPLY = 'Your image was uploaded successfully. AMAX can receive images, but image analysis is not available yet. Please describe what you want to check in the message.'
DEEPSEEK_BILLING_REPLY = 'AMAX AI service is temporarily unavailable because the account has no available balance. Please try again later.'


def generate_gemini_reply(message):
    """Generate a text response using the Gemini API."""
    url = f'{gemini_api_url.rstrip("/")}/{gemini_model}:generateContent?key={gemini_api_key}'
    response = requests.post(
        url,
        json={
            'contents': [
                {'parts': [{'text': f'You are AMAX, a helpful AI assistant. Give clear, practical answers.\n\n{message}'}]}
            ]
        },
        timeout=30,
    )
    response.raise_for_status()
    result = response.json()
    candidates = result.get('candidates', [])
    if not candidates:
        return NO_ANSWER_REPLY
    parts = candidates[0].get('content', {}).get('parts', [])
    if not parts:
        return NO_ANSWER_REPLY
    text = ''.join(part.get('text', '') for part in parts if isinstance(part, dict)).strip()
    return text or NO_ANSWER_REPLY


def generate_gemini_image_reply(image_bytes, mime_type, prompt_text):
    """Analyze an uploaded image using the Gemini multimodal API."""
    if not gemini_api_key:
        raise ValueError('Gemini API key is not configured.')

    url = f'{gemini_api_url.rstrip("/")}/{gemini_model}:generateContent?key={gemini_api_key}'
    encoded_image = base64.b64encode(image_bytes).decode('utf-8')
    instruction = (
        'You are AMAX, a helpful AI assistant. Analyze the uploaded image carefully and answer the user question accurately. '
        'If the image contains text, read it carefully; if it contains objects, describe them clearly; if the image is unclear, '
        'mention that briefly and still provide the most likely interpretation.\n\n'
        f'User request: {prompt_text or "Describe this image in detail."}'
    )

    response = requests.post(
        url,
        json={
            'contents': [
                {'parts': [
                    {'text': instruction},
                    {'inline_data': {'mime_type': mime_type, 'data': encoded_image}},
                ]}
            ]
        },
        timeout=60,
    )
    response.raise_for_status()
    result = response.json()
    candidates = result.get('candidates', [])
    if not candidates:
        return NO_ANSWER_REPLY

    parts = candidates[0].get('content', {}).get('parts', [])
    if not parts:
        return NO_ANSWER_REPLY

    text = ''.join(part.get('text', '') for part in parts if isinstance(part, dict)).strip()
    return text or 'I reviewed the image, but I could not extract a clear answer from it. Please upload a clearer image or ask a more specific question.'


def generate_deepseek_reply(message):
    """Generate a text response using DeepSeek's OpenAI-compatible API."""
    response = requests.post(
        deepseek_api_url,
        headers={
            'Authorization': f'Bearer {deepseek_api_key}',
            'Content-Type': 'application/json',
        },
        json={
            'model': deepseek_model,
            'messages': [
                {'role': 'system', 'content': 'You are AMAX, a helpful AI assistant. Give clear, practical answers.'},
                {'role': 'user', 'content': message},
            ],
            'temperature': 0.7,
            'max_tokens': 2000,
        },
        timeout=30,
    )
    response.raise_for_status()
    choices = response.json().get('choices', [])
    if not choices:
        return NO_ANSWER_REPLY
    return choices[0].get('message', {}).get('content', '').strip() or NO_ANSWER_REPLY

LOCAL_DIALOGUE_TOPICS = {
    'coding': {
        'keywords': ('code', 'coding', 'python', 'bug', 'error', 'program', 'software'),
        'steps': ('reproduce the issue with the smallest example', 'separate the input, logic, and output', 'read the error from the first relevant line', 'test one change at a time'),
        'checks': ('the expected and actual results', 'edge cases and invalid input', 'the simplest working version', 'whether the fix creates a new side effect'),
        'nexts': ('write a small test', 'add a clear explanation beside the fix', 'run the complete flow again', 'keep the change focused'),
    },
    'learning': {
        'keywords': ('learn', 'study', 'exam', 'question', 'meaning', 'explain', 'education'),
        'steps': ('start with the basic definition', 'connect the idea to a simple example', 'break the topic into smaller concepts', 'explain it in your own words'),
        'checks': ('whether you can give a new example', 'which part is still unclear', 'the difference between similar concepts', 'your understanding without notes'),
        'nexts': ('practice one short problem', 'summarize the key point', 'review it again later', 'ask a more specific question'),
    },
    'planning': {
        'keywords': ('plan', 'schedule', 'goal', 'task', 'organize', 'routine', 'steps'),
        'steps': ('define the result you want', 'list every required task', 'put the tasks in priority order', 'choose a realistic deadline'),
        'checks': ('what must happen first', 'how much time each task needs', 'which task can be removed', 'whether the plan fits your available time'),
        'nexts': ('start with the highest-value task', 'set a short review point', 'track progress visibly', 'adjust the plan when facts change'),
    },
    'decisions': {
        'keywords': ('choose', 'choice', 'decision', 'option', 'compare', 'better', 'should'),
        'steps': ('write down the available options', 'define the most important criterion', 'compare benefits and costs', 'identify the main risk of each option'),
        'checks': ('which facts are certain', 'what happens if nothing changes', 'the impact one month from now', 'whether the decision can be reversed'),
        'nexts': ('choose the option that best matches the goal', 'set a review date', 'record why you chose it', 'take one small first action'),
    },
    'writing': {
        'keywords': ('write', 'email', 'essay', 'content', 'grammar', 'sentence', 'message'),
        'steps': ('decide who will read the text', 'put the main point in the first sentence', 'use short sections with clear transitions', 'remove repeated or unnecessary words'),
        'checks': ('the tone and purpose', 'whether each sentence supports the main idea', 'spelling and factual accuracy', 'whether the reader knows the next action'),
        'nexts': ('read it aloud once', 'add a specific example', 'finish with a clear conclusion', 'revise after taking a short break'),
    },
    'work': {
        'keywords': ('work', 'job', 'career', 'project', 'meeting', 'team', 'business'),
        'steps': ('clarify the expected outcome', 'identify the people and resources involved', 'split the work into owners and deadlines', 'communicate the current status'),
        'checks': ('the highest-impact blocker', 'whether responsibilities are clear', 'what evidence shows progress', 'which issue needs escalation'),
        'nexts': ('send a concise update', 'document the decision', 'finish the smallest pending item', 'schedule the next checkpoint'),
    },
    'money': {
        'keywords': ('money', 'budget', 'cost', 'price', 'finance', 'saving', 'expense'),
        'steps': ('write down the exact amount', 'separate needs from optional spending', 'compare the recurring and one-time cost', 'keep a small safety margin'),
        'checks': ('the source of each number', 'hidden fees or future costs', 'the effect on your monthly budget', 'whether a cheaper option meets the same need'),
        'nexts': ('track the decision for one month', 'set a spending limit', 'compare two concrete alternatives', 'avoid deciding from incomplete numbers'),
    },
    'travel': {
        'keywords': ('travel', 'trip', 'holiday', 'flight', 'hotel', 'visit', 'tour'),
        'steps': ('set the dates and total budget', 'choose the most important places', 'check transport and accommodation together', 'keep time for delays and rest'),
        'checks': ('entry rules and opening times', 'the cancellation policy', 'local transport options', 'weather and safety conditions'),
        'nexts': ('save important confirmations offline', 'book the time-sensitive item first', 'keep an emergency contact list', 'review the itinerary before departure'),
    },
    'wellbeing': {
        'keywords': ('health', 'sleep', 'stress', 'exercise', 'habit', 'wellness', 'tired'),
        'steps': ('start with one small sustainable change', 'notice the situation that triggers the problem', 'keep a simple daily record', 'protect regular rest and recovery'),
        'checks': ('how the change affects your energy', 'whether the goal is realistic', 'patterns across several days', 'when professional advice is needed'),
        'nexts': ('repeat the helpful action tomorrow', 'reduce the goal if it feels overwhelming', 'share the concern with someone trusted', 'seek qualified medical help for serious symptoms'),
    },
    'general': {
        'keywords': (),
        'steps': ('define the exact result you want', 'separate facts from assumptions', 'break the request into smaller parts', 'compare the simplest available options'),
        'checks': ('what information is missing', 'the likely benefit and risk', 'whether the conclusion follows from the facts', 'what could change the answer'),
        'nexts': ('take the smallest useful next action', 'verify the result', 'write down the key decision', 'ask a more specific follow-up question'),
    },
}

LOCAL_DIALOGUE_QUALIFIERS = (
    'Keep the first step small and practical.',
    'Use clear facts before making a conclusion.',
    'Prefer a simple solution that you can verify.',
    'Write down the result so you can review it later.',
    'Change only one important thing at a time.',
    'Set a realistic time limit for the next step.',
    'Ask for the missing detail before guessing.',
    'Review the outcome and improve the process.',
    'Choose progress that is measurable and repeatable.',
)

def local_fallback_reply(message):
    """Return a deterministic, topic-aware reply without the AI service."""
    normalized_message = message.lower()

    if re.search(r'\b(?:hello|hi|hey|namaste)\b', normalized_message):
        return 'Hello! I can help you. Tell me what you need, and I will guide you with a logical answer.'
    if 'how are you' in normalized_message:
        return 'I am ready to help. The AI service is temporarily unavailable, so I am using local responses for now.'
    if any(word in normalized_message for word in ('calculate', 'plus', 'minus', 'multiply', 'divide')):
        return 'I can help solve this logically. Please provide the complete numbers and operation, for example: 24 multiplied by 3.'

    return get_dialogue_reply(message)


def local_image_analysis_reply(message):
    """Return a helpful message when vision analysis is unavailable."""
    normalized = (message or '').strip()
    if not normalized or normalized.lower() in {'please analyze this image', 'analyze this image', 'describe this image'}:
        return 'I can analyze uploaded images and answer questions about them. Please ask something specific like: "Describe this image," "What is written here?" or "What is shown in this image?"'
    return 'I can help with this image, but the image-analysis model is not available right now. Please upload a clearer image and ask a more specific question such as: "Describe this image," "Read the text in it," or "What is shown here?"'

@app.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    if request.content_type and request.content_type.startswith('multipart/form-data'):
        user_message = request.form.get('message', '').strip()
        image = request.files.get('image')
    else:
        data = request.get_json(silent=True) or {}
        user_message = data.get('message', '').strip()
        image = None

    if image and image.filename:
        image_type = (image.mimetype or mimetypes.guess_type(image.filename)[0] or '').lower()
        if image_type not in app.config['ALLOWED_CHAT_IMAGE_TYPES']:
            return jsonify({'error': 'Please upload a JPG, PNG, GIF, or WEBP image.'}), 400
        image_bytes = image.read()
        if not image_bytes:
            return jsonify({'error': 'The uploaded image is empty.'}), 400
        image_extension = mimetypes.guess_extension(image_type) or '.img'
        image_filename = f'{uuid4().hex}{image_extension}'
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
        try:
            with open(image_path, 'wb') as image_file:
                image_file.write(image_bytes)
        except OSError:
            app.logger.exception('Chat image could not be saved')
            return jsonify({'error': 'The image could not be uploaded. Please try again.'}), 500
    else:
        image_bytes = None
        image_filename = None
    
    if not user_message and not image_bytes:
        return jsonify({'error': 'Enter a message or choose an image.'}), 400

    stored_message = user_message or 'Please analyze this image.'
    safety_reply = get_safety_reply(stored_message)
    if safety_reply:
        save_chat_history(current_user.id, stored_message, safety_reply)
        return jsonify({'reply': safety_reply})

    if not image_bytes:
        faq_reply = get_faq_reply(stored_message)
        if faq_reply:
            save_chat_history(current_user.id, stored_message, faq_reply)
            return jsonify({'reply': faq_reply})

    if image_bytes:
        image_prompt = stored_message or 'Describe this image in detail.'
        if gemini_key_is_configured:
            try:
                ai_reply = generate_gemini_image_reply(image_bytes, image_type, image_prompt)
                save_chat_history(current_user.id, stored_message, ai_reply)
                return jsonify({'reply': ai_reply, 'image_url': url_for('uploaded_file', filename=image_filename)})
            except Exception:
                app.logger.exception('Gemini image-analysis request failed; falling back to local response.')

        ai_reply = local_image_analysis_reply(image_prompt)
        save_chat_history(current_user.id, stored_message, ai_reply)
        return jsonify({'reply': ai_reply, 'image_url': url_for('uploaded_file', filename=image_filename)})

    if gemini_key_is_configured:
        try:
            ai_reply = generate_gemini_reply(stored_message)
            save_chat_history(current_user.id, stored_message, ai_reply)
            return jsonify({'reply': ai_reply})
        except Exception:
            app.logger.exception('Gemini API request failed; falling back to local response.')
    
    if not deepseek_key_is_configured:
        ai_reply = local_fallback_reply(stored_message)
        save_chat_history(current_user.id, stored_message, ai_reply)
        return jsonify({'reply': ai_reply})
    
    try:
        ai_reply = generate_deepseek_reply(stored_message)
        save_chat_history(current_user.id, stored_message, ai_reply)
        return jsonify({'reply': ai_reply})
        
    except requests.HTTPError as error:
        if error.response is not None and error.response.status_code == 402:
            app.logger.warning('DeepSeek API account has insufficient balance.')
            ai_reply = DEEPSEEK_BILLING_REPLY
            save_chat_history(current_user.id, stored_message, ai_reply)
            return jsonify({'reply': ai_reply}), 503
        app.logger.exception('DeepSeek API request failed')
        ai_reply = local_fallback_reply(stored_message)
        save_chat_history(current_user.id, stored_message, ai_reply)
        return jsonify({'reply': ai_reply})
    except Exception:
        app.logger.exception('DeepSeek API request failed')
        ai_reply = local_fallback_reply(stored_message)
        save_chat_history(current_user.id, stored_message, ai_reply)
        return jsonify({'reply': ai_reply})

@app.route('/api/chats/<int:chat_id>', methods=['DELETE', 'PATCH'])
@login_required
def delete_chat(chat_id):
    chat_record = Chat.query.filter_by(id=chat_id, user_id=current_user.id).first()
    if chat_record is None:
        return jsonify({'error': 'Conversation not found'}), 404

    if request.method == 'PATCH':
        updates = request.get_json(silent=True)
        if not isinstance(updates, dict):
            return jsonify({'error': 'Conversation changes must be sent as an object.'}), 400
        if 'title' in updates:
            title = updates['title']
            if not isinstance(title, str) or len(title.strip()) > 80:
                return jsonify({'error': 'Conversation names must be 80 characters or fewer.'}), 400
            chat_record.title = title.strip() or None
        if 'is_pinned' in updates:
            if not isinstance(updates['is_pinned'], bool):
                return jsonify({'error': 'Pinned state must be true or false.'}), 400
            chat_record.is_pinned = updates['is_pinned']
        if not {'title', 'is_pinned'} & updates.keys():
            return jsonify({'error': 'No conversation changes were provided.'}), 400
        db.session.commit()
        return jsonify({
            'chat_id': chat_id,
            'title': chat_record.title,
            'is_pinned': chat_record.is_pinned,
        })

    db.session.delete(chat_record)
    db.session.commit()
    return jsonify({'deleted': True, 'chat_id': chat_id})

@app.route('/api/chats', methods=['DELETE'])
@login_required
def clear_chat_history():
    request_data = request.get_json(silent=True)
    if request_data is None:
        period = 'all_time'
    elif isinstance(request_data, dict):
        period = request_data.get('period')
    else:
        return jsonify({'error': 'A history period is required.'}), 400

    if period not in {'last_2_days', 'last_month', 'all_time'}:
        return jsonify({'error': 'Choose a valid history period.'}), 400

    chats = Chat.query.filter_by(user_id=current_user.id)
    if period == 'last_2_days':
        chats = chats.filter(Chat.timestamp >= datetime.utcnow() - timedelta(days=2))
    elif period == 'last_month':
        chats = chats.filter(Chat.timestamp >= datetime.utcnow() - timedelta(days=30))

    deleted_count = chats.delete(synchronize_session=False)
    db.session.commit()
    return jsonify({'deleted': True, 'deleted_count': deleted_count})

# --- Run the App ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    app.run(
        debug=os.getenv('DEBUG', 'False').lower() == 'true',
        host='0.0.0.0',
        port=int(os.getenv('PORT', '5000')),
    )