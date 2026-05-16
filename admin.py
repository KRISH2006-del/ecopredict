# Admin module for administrative functions

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from functools import wraps
import logging
import sqlite3

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


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


def register_admin_routes(app, db):
    """Register admin routes"""
    
    @admin_bp.route('/')
    @admin_required
    def admin_dashboard():
        """Admin dashboard overview"""
        stats = get_admin_stats(db)
        return render_template('admin/dashboard.html', stats=stats)
    
    @admin_bp.route('/users')
    @admin_required
    def manage_users():
        """Manage users page"""
        users = db.execute_query(
            'SELECT id, username, email, is_admin, created_at FROM users ORDER BY id DESC',
            fetch_all=True
        )
        return render_template('admin/users.html', users=users)
    
    @admin_bp.route('/users/<int:user_id>/toggle-admin', methods=['POST'])
    @admin_required
    def toggle_admin(user_id):
        """Toggle admin status for a user"""
        if user_id == session.get('user_id'):
            return jsonify({'error': 'Cannot modify your own admin status'}), 400
        
        try:
            user = db.execute_query(
                'SELECT is_admin FROM users WHERE id = ?',
                (user_id,),
                fetch_one=True
            )
            if user:
                new_status = 0 if user[0] else 1
                db.execute_query(
                    'UPDATE users SET is_admin = ? WHERE id = ?',
                    (new_status, user_id)
                )
                return jsonify({'success': True, 'is_admin': bool(new_status)})
        except Exception as e:
            logger.error(f"Failed to toggle admin: {e}")
        
        return jsonify({'error': 'Failed to update user'}), 500
    
    @admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
    @admin_required
    def delete_user(user_id):
        """Delete a user"""
        if user_id == session.get('user_id'):
            return jsonify({'error': 'Cannot delete your own account'}), 400
        
        try:
            db.execute_query('DELETE FROM users WHERE id = ?', (user_id,))
            return jsonify({'success': True})
        except Exception as e:
            logger.error(f"Failed to delete user: {e}")
        
        return jsonify({'error': 'Failed to delete user'}), 500
    
    @admin_bp.route('/data')
    @admin_required
    def manage_data():
        """Data management page"""
        stats = {
            'training_count': 0,
            'prediction_count': 0,
            'areas': [],
            'waste_types': []
        }
        
        try:
            result = db.execute_query('SELECT COUNT(*) FROM training_data', fetch_one=True)
            stats['training_count'] = result[0] if result else 0
            
            result = db.execute_query('SELECT COUNT(*) FROM prediction_logs', fetch_one=True)
            stats['prediction_count'] = result[0] if result else 0
            
            areas = db.execute_query('SELECT DISTINCT area FROM training_data', fetch_all=True)
            stats['areas'] = [a[0] for a in areas] if areas else []
            
            types = db.execute_query('SELECT DISTINCT waste_type FROM training_data', fetch_all=True)
            stats['waste_types'] = [t[0] for t in types] if types else []
        except Exception as e:
            logger.error(f"Failed to get data stats: {e}")
        
        return render_template('admin/data.html', stats=stats)
    
    @admin_bp.route('/import', methods=['GET', 'POST'])
    @admin_required
    def import_data():
        """Import data page"""
        if request.method == 'POST':
            if 'file' not in request.files:
                flash('No file uploaded', 'error')
                return redirect(request.url)
            
            file = request.files['file']
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(request.url)
            
            if file and file.filename.endswith('.csv'):
                try:
                    import pandas as pd
                    import io
                    
                    content = file.read().decode('utf-8')
                    df = pd.read_csv(io.StringIO(content))
                    
                    # Validate columns
                    required = ['area', 'waste_type', 'ticket_date', 'net_weight_kg']
                    if not all(col in df.columns for col in required):
                        flash(f'CSV must contain columns: {", ".join(required)}', 'error')
                        return redirect(request.url)
                    
                    # Insert data
                    count = 0
                    with db.get_connection() as conn:
                        cursor = conn.cursor()
                        for _, row in df.iterrows():
                            cursor.execute('''
                                INSERT INTO training_data (area, waste_type, ticket_date, net_weight_kg)
                                VALUES (?, ?, ?, ?)
                            ''', (row['area'], row['waste_type'], row['ticket_date'], row['net_weight_kg']))
                            count += 1
                        conn.commit()
                    
                    flash(f'Successfully imported {count} records', 'success')
                    logger.info(f"Imported {count} records via admin")
                    return redirect(url_for('admin.manage_data'))
                    
                except Exception as e:
                    logger.error(f"Import failed: {e}")
                    flash(f'Import failed: {str(e)}', 'error')
            else:
                flash('Please upload a CSV file', 'error')
        
        return render_template('admin/import.html')
    
    @admin_bp.route('/clear-predictions', methods=['POST'])
    @admin_required
    def clear_predictions():
        """Clear all prediction logs"""
        try:
            db.execute_query('DELETE FROM prediction_logs')
            flash('All prediction logs cleared', 'success')
        except Exception as e:
            logger.error(f"Failed to clear predictions: {e}")
            flash('Failed to clear predictions', 'error')
        
        return redirect(url_for('admin.manage_data'))
    
    @admin_bp.route('/backup')
    @admin_required
    def backup_database():
        """Create a database backup"""
        import shutil
        from datetime import datetime
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f'waste_backup_{timestamp}.db'
            shutil.copy('waste.db', backup_path)
            flash(f'Backup created: {backup_path}', 'success')
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            flash('Backup failed', 'error')
        
        return redirect(url_for('admin.manage_data'))
    
    @admin_bp.route('/logs')
    @admin_required
    def view_logs():
        """View recent activity logs"""
        logs = db.execute_query('''
            SELECT p.*, u.username 
            FROM prediction_logs p 
            LEFT JOIN users u ON p.user_id = u.id 
            ORDER BY p.id DESC LIMIT 100
        ''', fetch_all=True, row_factory=sqlite3.Row)
        
        return render_template('admin/logs.html', logs=logs)
    
    app.register_blueprint(admin_bp)


def get_admin_stats(db):
    """Get statistics for admin dashboard"""
    stats = {
        'total_users': 0,
        'total_predictions': 0,
        'total_training_records': 0,
        'predictions_today': 0,
        'new_users_today': 0,
        'top_areas': [],
        'recent_users': []
    }
    
    try:
        # Total counts
        result = db.execute_query('SELECT COUNT(*) FROM users', fetch_one=True)
        stats['total_users'] = result[0] if result else 0
        
        result = db.execute_query('SELECT COUNT(*) FROM prediction_logs', fetch_one=True)
        stats['total_predictions'] = result[0] if result else 0
        
        result = db.execute_query('SELECT COUNT(*) FROM training_data', fetch_one=True)
        stats['total_training_records'] = result[0] if result else 0
        
        # Today's activity
        result = db.execute_query(
            "SELECT COUNT(*) FROM prediction_logs WHERE DATE(timestamp) = DATE('now')",
            fetch_one=True
        )
        stats['predictions_today'] = result[0] if result else 0
        
        result = db.execute_query(
            "SELECT COUNT(*) FROM users WHERE DATE(created_at) = DATE('now')",
            fetch_one=True
        )
        stats['new_users_today'] = result[0] if result else 0
        
        # Top areas
        top_areas = db.execute_query('''
            SELECT area, COUNT(*) as count 
            FROM prediction_logs 
            GROUP BY area 
            ORDER BY count DESC 
            LIMIT 5
        ''', fetch_all=True)
        stats['top_areas'] = [{'area': a[0], 'count': a[1]} for a in top_areas] if top_areas else []
        
        # Recent users
        recent = db.execute_query(
            'SELECT username, email, created_at FROM users ORDER BY id DESC LIMIT 5',
            fetch_all=True
        )
        stats['recent_users'] = [{'username': u[0], 'email': u[1], 'created_at': u[2]} for u in recent] if recent else []
        
    except Exception as e:
        logger.error(f"Failed to get admin stats: {e}")
    
    return stats
