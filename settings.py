# User settings and preferences module

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from functools import wraps
import logging

logger = logging.getLogger(__name__)

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')


def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def init_settings_table(db):
    """Initialize user settings table"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    theme TEXT DEFAULT 'dark',
                    default_area TEXT,
                    default_waste_type TEXT,
                    notifications_enabled INTEGER DEFAULT 1,
                    email_reports INTEGER DEFAULT 0,
                    report_frequency TEXT DEFAULT 'weekly',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            logger.info("Settings table initialized")
    except Exception as e:
        logger.error(f"Failed to initialize settings table: {e}")


def get_user_settings(db, user_id):
    """Get settings for a user"""
    try:
        result = db.execute_query(
            'SELECT * FROM user_settings WHERE user_id = ?',
            (user_id,),
            fetch_one=True
        )
        
        if result:
            return {
                'theme': result[2],
                'default_area': result[3],
                'default_waste_type': result[4],
                'notifications_enabled': bool(result[5]),
                'email_reports': bool(result[6]),
                'report_frequency': result[7]
            }
    except Exception as e:
        logger.error(f"Failed to get user settings: {e}")
    
    # Return defaults
    return {
        'theme': 'dark',
        'default_area': None,
        'default_waste_type': None,
        'notifications_enabled': True,
        'email_reports': False,
        'report_frequency': 'weekly'
    }


def register_settings_routes(app, db, model):
    """Register settings routes"""
    
    init_settings_table(db)
    
    @settings_bp.route('/')
    @login_required
    def settings_page():
        """User settings page"""
        user_settings = get_user_settings(db, session['user_id'])
        return render_template(
            'settings.html',
            settings=user_settings,
            areas=model.areas,
            waste_types=model.waste_types
        )
    
    @settings_bp.route('/update', methods=['POST'])
    @login_required
    def update_settings():
        """Update user settings"""
        user_id = session['user_id']
        
        theme = request.form.get('theme', 'dark')
        default_area = request.form.get('default_area', '')
        default_waste_type = request.form.get('default_waste_type', '')
        notifications = 1 if request.form.get('notifications') else 0
        email_reports = 1 if request.form.get('email_reports') else 0
        report_frequency = request.form.get('report_frequency', 'weekly')
        
        try:
            # Check if settings exist
            existing = db.execute_query(
                'SELECT id FROM user_settings WHERE user_id = ?',
                (user_id,),
                fetch_one=True
            )
            
            if existing:
                db.execute_query('''
                    UPDATE user_settings SET 
                        theme = ?, default_area = ?, default_waste_type = ?,
                        notifications_enabled = ?, email_reports = ?, 
                        report_frequency = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                ''', (theme, default_area or None, default_waste_type or None,
                      notifications, email_reports, report_frequency, user_id))
            else:
                db.execute_query('''
                    INSERT INTO user_settings 
                        (user_id, theme, default_area, default_waste_type, 
                         notifications_enabled, email_reports, report_frequency)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, theme, default_area or None, default_waste_type or None,
                      notifications, email_reports, report_frequency))
            
            # Update session theme
            session['theme'] = theme
            
            flash('Settings saved successfully', 'success')
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            flash('Failed to save settings', 'error')
        
        return redirect(url_for('settings.settings_page'))
    
    @settings_bp.route('/change-password', methods=['POST'])
    @login_required
    def change_password():
        """Change user password"""
        from werkzeug.security import generate_password_hash, check_password_hash
        
        current = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm = request.form.get('confirm_password', '')
        
        if not all([current, new_password, confirm]):
            flash('All password fields are required', 'error')
            return redirect(url_for('settings.settings_page'))
        
        if new_password != confirm:
            flash('New passwords do not match', 'error')
            return redirect(url_for('settings.settings_page'))
        
        if len(new_password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return redirect(url_for('settings.settings_page'))
        
        try:
            user = db.execute_query(
                'SELECT password_hash FROM users WHERE id = ?',
                (session['user_id'],),
                fetch_one=True
            )
            
            if not user or not check_password_hash(user[0], current):
                flash('Current password is incorrect', 'error')
                return redirect(url_for('settings.settings_page'))
            
            new_hash = generate_password_hash(new_password)
            db.execute_query(
                'UPDATE users SET password_hash = ? WHERE id = ?',
                (new_hash, session['user_id'])
            )
            
            flash('Password changed successfully', 'success')
        except Exception as e:
            logger.error(f"Failed to change password: {e}")
            flash('Failed to change password', 'error')
        
        return redirect(url_for('settings.settings_page'))
    
    @settings_bp.route('/delete-account', methods=['POST'])
    @login_required
    def delete_account():
        """Delete user account"""
        password = request.form.get('password', '')
        
        if not password:
            flash('Password required to delete account', 'error')
            return redirect(url_for('settings.settings_page'))
        
        try:
            from werkzeug.security import check_password_hash
            
            user = db.execute_query(
                'SELECT password_hash FROM users WHERE id = ?',
                (session['user_id'],),
                fetch_one=True
            )
            
            if not user or not check_password_hash(user[0], password):
                flash('Incorrect password', 'error')
                return redirect(url_for('settings.settings_page'))
            
            user_id = session['user_id']
            
            # Delete user data
            db.execute_query('DELETE FROM user_settings WHERE user_id = ?', (user_id,))
            db.execute_query('DELETE FROM prediction_logs WHERE user_id = ?', (user_id,))
            db.execute_query('DELETE FROM users WHERE id = ?', (user_id,))
            
            session.clear()
            flash('Your account has been deleted', 'info')
            return redirect(url_for('index'))
            
        except Exception as e:
            logger.error(f"Failed to delete account: {e}")
            flash('Failed to delete account', 'error')
        
        return redirect(url_for('settings.settings_page'))
    
    @settings_bp.route('/api/theme', methods=['POST'])
    def set_theme():
        """Set theme via API (works without login)"""
        theme = request.json.get('theme', 'dark')
        session['theme'] = theme
        
        if 'user_id' in session:
            try:
                db.execute_query(
                    'UPDATE user_settings SET theme = ? WHERE user_id = ?',
                    (theme, session['user_id'])
                )
            except:
                pass
        
        return jsonify({'success': True, 'theme': theme})
    
    app.register_blueprint(settings_bp)
    
    # Context processor for theme
    @app.context_processor
    def inject_theme():
        return dict(theme=session.get('theme', 'dark'))
