# Authentication module for user management

import sqlite3
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)


def init_auth_tables(db):
    """Initialize authentication-related database tables"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_admin INTEGER DEFAULT 0
                )
            ''')
            
            # Add user_id column to prediction_logs if not exists
            cursor.execute("PRAGMA table_info(prediction_logs)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'user_id' not in columns:
                cursor.execute('ALTER TABLE prediction_logs ADD COLUMN user_id INTEGER')
            
            logger.info("Auth tables initialized")
    except Exception as e:
        logger.error(f"Failed to initialize auth tables: {e}")


def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if not session.get('is_admin'):
            flash('Admin access required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user(db):
    """Get current logged-in user from session"""
    if 'user_id' not in session:
        return None
    
    try:
        result = db.execute_query(
            'SELECT id, username, email, is_admin FROM users WHERE id = ?',
            (session['user_id'],),
            fetch_one=True
        )
        if result:
            return {
                'id': result[0],
                'username': result[1],
                'email': result[2],
                'is_admin': result[3]
            }
    except Exception as e:
        logger.error(f"Error fetching user: {e}")
    return None


def register_auth_routes(app, db):
    """Register authentication routes"""
    
    @auth_bp.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            # Validation
            errors = []
            if not username or len(username) < 3:
                errors.append('Username must be at least 3 characters')
            if not email or '@' not in email:
                errors.append('Valid email is required')
            if not password or len(password) < 6:
                errors.append('Password must be at least 6 characters')
            if password != confirm_password:
                errors.append('Passwords do not match')
            
            # Check if user exists
            if not errors:
                existing = db.execute_query(
                    'SELECT id FROM users WHERE username = ? OR email = ?',
                    (username, email),
                    fetch_one=True
                )
                if existing:
                    errors.append('Username or email already exists')
            
            if errors:
                for error in errors:
                    flash(error, 'error')
                return render_template('register.html')
            
            # Create user
            try:
                password_hash = generate_password_hash(password)
                db.insert('users', {
                    'username': username,
                    'email': email,
                    'password_hash': password_hash
                })
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('auth.login'))
            except Exception as e:
                logger.error(f"Registration failed: {e}")
                flash('Registration failed. Please try again.', 'error')
        
        return render_template('register.html')
    
    @auth_bp.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            
            user = db.execute_query(
                'SELECT id, username, password_hash, is_admin FROM users WHERE username = ? OR email = ?',
                (username, username),
                fetch_one=True
            )
            
            if user and check_password_hash(user[2], password):
                session['user_id'] = user[0]
                session['username'] = user[1]
                session['is_admin'] = bool(user[3])
                flash(f'Welcome back, {user[1]}!', 'success')
                
                next_page = request.args.get('next')
                return redirect(next_page or url_for('index'))
            else:
                flash('Invalid username or password', 'error')
        
        return render_template('login.html')
    
    @auth_bp.route('/logout')
    def logout():
        session.clear()
        flash('You have been logged out.', 'info')
        return redirect(url_for('index'))
    
    @auth_bp.route('/profile')
    @login_required
    def profile():
        user = get_current_user(db)
        
        # Get user's prediction count
        stats = db.execute_query(
            'SELECT COUNT(*), AVG(predicted_weight_kg) FROM prediction_logs WHERE user_id = ?',
            (session['user_id'],),
            fetch_one=True
        )
        
        user_stats = {
            'total_predictions': stats[0] if stats else 0,
            'avg_prediction': round(stats[1], 2) if stats and stats[1] else 0
        }
        
        return render_template('profile.html', user=user, stats=user_stats)
    
    app.register_blueprint(auth_bp)
    
    # Context processor to make user available in all templates
    @app.context_processor
    def inject_user():
        return dict(current_user=get_current_user(db))
