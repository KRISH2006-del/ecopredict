# User data upload module - allows users to upload their own datasets

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from functools import wraps
import logging
import io
import json

logger = logging.getLogger(__name__)

upload_bp = Blueprint('upload', __name__, url_prefix='/upload')


def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to upload data.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def init_upload_table(db):
    """Initialize user uploads table"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_uploads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    filename TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    record_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    upload_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    area TEXT,
                    waste_type TEXT,
                    date TEXT,
                    weight REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (upload_id) REFERENCES user_uploads(id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            logger.info("Upload tables initialized")
    except Exception as e:
        logger.error(f"Failed to initialize upload tables: {e}")


def parse_csv(content):
    """Parse CSV content"""
    import csv
    reader = csv.DictReader(io.StringIO(content))
    return list(reader)


def parse_excel(file_content):
    """Parse Excel file"""
    try:
        import pandas as pd
        df = pd.read_excel(io.BytesIO(file_content))
        return df.to_dict('records')
    except ImportError:
        raise ValueError("Excel support requires 'openpyxl' package. Install with: pip install openpyxl")


def parse_json(content):
    """Parse JSON content"""
    data = json.loads(content)
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'data' in data:
        return data['data']
    else:
        return [data]


def validate_record(record):
    """Validate and normalize a data record"""
    # Check for required fields (flexible column names)
    area_keys = ['area', 'Area', 'AREA', 'municipality', 'location', 'region']
    type_keys = ['waste_type', 'Waste_Type', 'type', 'waste', 'category']
    date_keys = ['date', 'Date', 'DATE', 'ticket_date', 'collection_date']
    weight_keys = ['weight', 'Weight', 'net_weight_kg', 'weight_kg', 'kg', 'amount']
    
    def find_value(record, keys):
        for key in keys:
            if key in record and record[key]:
                return record[key]
        return None
    
    area = find_value(record, area_keys)
    waste_type = find_value(record, type_keys)
    date = find_value(record, date_keys)
    weight = find_value(record, weight_keys)
    
    if not all([area, waste_type, date]):
        return None
    
    try:
        weight = float(weight) if weight else 0.0
    except (ValueError, TypeError):
        weight = 0.0
    
    return {
        'area': str(area).strip(),
        'waste_type': str(waste_type).strip(),
        'date': str(date).strip(),
        'weight': weight
    }


def register_upload_routes(app, db):
    """Register upload routes"""
    
    init_upload_table(db)
    
    @upload_bp.route('/')
    @login_required
    def upload_page():
        """Upload page"""
        # Get user's previous uploads
        uploads = db.execute_query(
            '''SELECT id, filename, file_type, record_count, status, created_at 
               FROM user_uploads WHERE user_id = ? ORDER BY id DESC LIMIT 10''',
            (session['user_id'],),
            fetch_all=True
        )
        return render_template('upload.html', uploads=uploads)
    
    @upload_bp.route('/process', methods=['POST'])
    @login_required
    def process_upload():
        """Process uploaded file"""
        if 'file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(url_for('upload.upload_page'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('upload.upload_page'))
        
        filename = file.filename.lower()
        user_id = session['user_id']
        
        try:
            # Determine file type and parse
            if filename.endswith('.csv'):
                content = file.read().decode('utf-8')
                records = parse_csv(content)
                file_type = 'CSV'
            elif filename.endswith(('.xlsx', '.xls')):
                content = file.read()
                records = parse_excel(content)
                file_type = 'Excel'
            elif filename.endswith('.json'):
                content = file.read().decode('utf-8')
                records = parse_json(content)
                file_type = 'JSON'
            else:
                flash('Unsupported file format. Please use CSV, Excel (.xlsx), or JSON.', 'error')
                return redirect(url_for('upload.upload_page'))
            
            if not records:
                flash('No valid records found in file', 'error')
                return redirect(url_for('upload.upload_page'))
            
            # Create upload record
            db.execute_query(
                '''INSERT INTO user_uploads (user_id, filename, file_type, status)
                   VALUES (?, ?, ?, 'processing')''',
                (user_id, file.filename, file_type)
            )
            
            # Get the upload ID
            upload_result = db.execute_query(
                'SELECT id FROM user_uploads WHERE user_id = ? ORDER BY id DESC LIMIT 1',
                (user_id,),
                fetch_one=True
            )
            upload_id = upload_result[0] if upload_result else None
            
            if not upload_id:
                flash('Failed to create upload record', 'error')
                return redirect(url_for('upload.upload_page'))
            
            # Process and insert records
            valid_count = 0
            with db.get_connection() as conn:
                cursor = conn.cursor()
                for record in records:
                    validated = validate_record(record)
                    if validated:
                        cursor.execute('''
                            INSERT INTO user_data (upload_id, user_id, area, waste_type, date, weight)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (upload_id, user_id, validated['area'], validated['waste_type'], 
                              validated['date'], validated['weight']))
                        valid_count += 1
                conn.commit()
            
            # Update upload record
            db.execute_query(
                'UPDATE user_uploads SET record_count = ?, status = ? WHERE id = ?',
                (valid_count, 'completed', upload_id)
            )
            
            flash(f'Successfully imported {valid_count} records from {file.filename}', 'success')
            logger.info(f"User {user_id} uploaded {valid_count} records from {file.filename}")
            
        except ValueError as e:
            flash(str(e), 'error')
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            flash(f'Upload failed: {str(e)}', 'error')
        
        return redirect(url_for('upload.upload_page'))
    
    @upload_bp.route('/data')
    @login_required
    def view_data():
        """View user's uploaded data"""
        user_id = session['user_id']
        
        data = db.execute_query(
            '''SELECT ud.id, ud.area, ud.waste_type, ud.date, ud.weight, uu.filename
               FROM user_data ud
               JOIN user_uploads uu ON ud.upload_id = uu.id
               WHERE ud.user_id = ?
               ORDER BY ud.id DESC LIMIT 100''',
            (user_id,),
            fetch_all=True
        )
        
        return render_template('upload_data.html', data=data)
    
    @upload_bp.route('/delete/<int:upload_id>', methods=['POST'])
    @login_required
    def delete_upload(upload_id):
        """Delete an upload and its data"""
        user_id = session['user_id']
        
        try:
            # Verify ownership
            upload = db.execute_query(
                'SELECT id FROM user_uploads WHERE id = ? AND user_id = ?',
                (upload_id, user_id),
                fetch_one=True
            )
            
            if not upload:
                flash('Upload not found', 'error')
                return redirect(url_for('upload.upload_page'))
            
            # Delete data first
            db.execute_query('DELETE FROM user_data WHERE upload_id = ?', (upload_id,))
            db.execute_query('DELETE FROM user_uploads WHERE id = ?', (upload_id,))
            
            flash('Upload deleted successfully', 'success')
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            flash('Failed to delete upload', 'error')
        
        return redirect(url_for('upload.upload_page'))
    
    @upload_bp.route('/api/stats')
    @login_required
    def upload_stats():
        """Get user's data statistics"""
        user_id = session['user_id']
        
        stats = {
            'total_records': 0,
            'total_uploads': 0,
            'by_area': [],
            'by_type': []
        }
        
        try:
            result = db.execute_query(
                'SELECT COUNT(*) FROM user_data WHERE user_id = ?',
                (user_id,),
                fetch_one=True
            )
            stats['total_records'] = result[0] if result else 0
            
            result = db.execute_query(
                'SELECT COUNT(*) FROM user_uploads WHERE user_id = ?',
                (user_id,),
                fetch_one=True
            )
            stats['total_uploads'] = result[0] if result else 0
            
            by_area = db.execute_query(
                '''SELECT area, COUNT(*), AVG(weight) FROM user_data 
                   WHERE user_id = ? GROUP BY area ORDER BY COUNT(*) DESC LIMIT 5''',
                (user_id,),
                fetch_all=True
            )
            if by_area:
                stats['by_area'] = [{'area': r[0], 'count': r[1], 'avg': round(r[2], 2)} for r in by_area]
            
            by_type = db.execute_query(
                '''SELECT waste_type, COUNT(*), AVG(weight) FROM user_data 
                   WHERE user_id = ? GROUP BY waste_type ORDER BY COUNT(*) DESC LIMIT 5''',
                (user_id,),
                fetch_all=True
            )
            if by_type:
                stats['by_type'] = [{'type': r[0], 'count': r[1], 'avg': round(r[2], 2)} for r in by_type]
                
        except Exception as e:
            logger.error(f"Failed to get upload stats: {e}")
        
        return jsonify(stats)
    
    app.register_blueprint(upload_bp)
