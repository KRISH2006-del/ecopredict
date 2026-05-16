# Flask Application - Waste Prediction System
# Complete implementation with all modules integrated

import os
import logging
import sqlite3
from flask import Flask, render_template, request, jsonify, session

# Local imports
from config import get_config
from database import DatabaseManager, DatabaseError
from models import WastePredictionModel, PredictionError
from validators import validate_prediction_input, ValidationError
from auth import register_auth_routes, init_auth_tables
from exports import register_export_routes
from analytics import register_analytics_routes
from api_docs import register_api_docs_routes
from admin import register_admin_routes
from settings import register_settings_routes
from compare import register_compare_routes
from upload import register_upload_routes
from multi_model import MultiModelManager
from model_routes import register_model_routes

# ============================================================================
# Application Setup
# ============================================================================

def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)
    app.secret_key = config.SECRET_KEY
    
    # Setup logging
    setup_logging(app)
    
    # Initialize components
    app.db = DatabaseManager(config.DATABASE_PATH)
    app.model = WastePredictionModel(config.MODEL_PATH, config.UI_VALUES_PATH)
    app.model_manager = MultiModelManager(config.UI_VALUES_PATH)
    
    # Initialize auth tables
    init_auth_tables(app.db)
    
    # Register routes
    register_routes(app)
    register_auth_routes(app, app.db)
    register_export_routes(app, app.db)
    register_analytics_routes(app, app.db)
    register_api_docs_routes(app)
    register_admin_routes(app, app.db)
    register_settings_routes(app, app.db, app.model)
    register_compare_routes(app, app.db)
    register_upload_routes(app, app.db)
    register_model_routes(app, app.model_manager)
    
    # Register error handlers
    register_error_handlers(app)
    
    app.logger.info("Application initialized successfully")
    return app


def setup_logging(app):
    """Configure application logging"""
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
    log_format = app.config.get('LOG_FORMAT', '%(asctime)s - %(levelname)s - %(message)s')
    
    logging.basicConfig(level=log_level, format=log_format)
    app.logger.setLevel(log_level)


def register_error_handlers(app):
    """Register custom error handlers"""
    
    @app.errorhandler(404)
    def not_found(error):
        return render_template('error.html', error='Page not found', code=404), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal server error: {error}")
        return render_template('error.html', error='Internal server error', code=500), 500
    
    @app.errorhandler(ValidationError)
    def validation_error(error):
        return jsonify({'error': error.message, 'field': error.field}), 400
    
    @app.errorhandler(PredictionError)
    def prediction_error(error):
        return jsonify({'error': str(error)}), 400
    
    @app.errorhandler(DatabaseError)
    def database_error(error):
        app.logger.error(f"Database error: {error}")
        return jsonify({'error': 'Database operation failed'}), 500


# ============================================================================
# Routes
# ============================================================================

def register_routes(app):
    """Register all application routes"""
    
    @app.route('/')
    def index():
        """Render the main prediction page"""
        return render_template(
            'index.html',
            areas=app.model.areas,
            waste_types=app.model.waste_types
        )
    
    @app.route('/dashboard')
    def dashboard():
        """Render the analytics dashboard"""
        return render_template('dashboard.html')
    
    @app.route('/history')
    def history():
        """Render the prediction history page"""
        logs = []
        try:
            user_id = session.get('user_id')
            if user_id:
                logs = app.db.execute_query(
                    "SELECT * FROM prediction_logs WHERE user_id = ? ORDER BY id DESC LIMIT 50",
                    (user_id,),
                    fetch_all=True,
                    row_factory=sqlite3.Row
                )
            else:
                logs = app.db.execute_query(
                    "SELECT * FROM prediction_logs ORDER BY id DESC LIMIT 50",
                    fetch_all=True,
                    row_factory=sqlite3.Row
                )
        except DatabaseError as e:
            app.logger.error(f"Failed to fetch history: {e}")
        
        return render_template('history.html', history=logs)
    
    @app.route('/api/stats')
    def api_stats():
        """API endpoint for dashboard statistics"""
        stats = {
            'by_area': [],
            'by_date': [],
            'total_predictions': 0,
            'avg_prediction': 0
        }
        
        try:
            # Predictions by area
            results = app.db.execute_query('''
                SELECT area, COUNT(*) as count, AVG(predicted_weight_kg) as avg_weight 
                FROM prediction_logs 
                GROUP BY area 
                ORDER BY count DESC 
                LIMIT 10
            ''', fetch_all=True)
            
            if results:
                stats['by_area'] = [
                    {'area': r[0], 'count': r[1], 'avg_weight': round(r[2], 2)} 
                    for r in results
                ]
            
            # Predictions by date
            results = app.db.execute_query('''
                SELECT prediction_date, SUM(predicted_weight_kg) as total_weight 
                FROM prediction_logs 
                GROUP BY prediction_date 
                ORDER BY prediction_date DESC 
                LIMIT 7
            ''', fetch_all=True)
            
            if results:
                stats['by_date'] = [
                    {'date': r[0], 'total_weight': round(r[1], 2)} 
                    for r in results
                ]
            
            # Overall stats
            result = app.db.execute_query(
                'SELECT COUNT(*), AVG(predicted_weight_kg) FROM prediction_logs',
                fetch_one=True
            )
            
            if result:
                stats['total_predictions'] = result[0] or 0
                stats['avg_prediction'] = round(result[1], 2) if result[1] else 0
                
        except DatabaseError as e:
            app.logger.error(f"Failed to fetch stats: {e}")
        
        return jsonify(stats)
    
    @app.route('/predict', methods=['POST'])
    def predict():
        """Handle prediction requests"""
        
        # Check if model is ready
        if not app.model.is_ready:
            return jsonify({
                'error': 'Model not loaded. Please run train_model.py first.'
            }), 503
        
        try:
            # Get and validate input
            area = request.form.get('area')
            waste_type = request.form.get('waste_type')
            date_str = request.form.get('date')
            
            area, waste_type, date_obj = validate_prediction_input(
                area, waste_type, date_str,
                app.model.areas,
                app.model.waste_types
            )
            
            # Make prediction
            prediction = app.model.predict(area, waste_type, date_obj)
            
            app.logger.info(f"Prediction made: {prediction} for {area}, {waste_type}, {date_str}")
            
            # Log to database
            comparison = log_prediction_and_get_comparison(
                app.db, area, waste_type, date_str, prediction, session.get('user_id')
            )
            
            return jsonify({
                'prediction': f"{prediction:.2f} kg",
                'prediction_value': round(prediction, 2),
                'comparison': comparison,
                'labels': {
                    'area': area,
                    'waste_type': waste_type
                }
            })
            
        except ValidationError as e:
            return jsonify({'error': e.message, 'field': e.field}), 400
        except PredictionError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            app.logger.error(f"Unexpected error in prediction: {e}")
            return jsonify({'error': 'An unexpected error occurred'}), 500
    
    @app.route('/api/health')
    def health_check():
        """Health check endpoint for monitoring"""
        status = {
            'status': 'healthy',
            'model_loaded': app.model.is_ready,
            'database_connected': True
        }
        
        # Test database connection
        try:
            app.db.execute_query("SELECT 1", fetch_one=True)
        except:
            status['database_connected'] = False
            status['status'] = 'degraded'
        
        return jsonify(status)


def log_prediction_and_get_comparison(db, area, waste_type, date_str, prediction, user_id=None):
    """Log prediction and get comparison data"""
    comparison = {
        'area_avg': prediction,
        'type_avg': prediction,
        'overall_avg': prediction
    }
    
    try:
        # Insert prediction log
        data = {
            'area': area,
            'waste_type': waste_type,
            'prediction_date': date_str,
            'predicted_weight_kg': prediction
        }
        if user_id:
            data['user_id'] = user_id
        
        db.insert('prediction_logs', data)
        
        # Get area average
        result = db.execute_query(
            'SELECT AVG(net_weight_kg) FROM training_data WHERE area = ?',
            (area,),
            fetch_one=True
        )
        if result and result[0]:
            comparison['area_avg'] = round(result[0], 2)
        
        # Get waste type average
        result = db.execute_query(
            'SELECT AVG(net_weight_kg) FROM training_data WHERE waste_type = ?',
            (waste_type,),
            fetch_one=True
        )
        if result and result[0]:
            comparison['type_avg'] = round(result[0], 2)
        
        # Get overall average
        result = db.execute_query(
            'SELECT AVG(net_weight_kg) FROM training_data',
            fetch_one=True
        )
        if result and result[0]:
            comparison['overall_avg'] = round(result[0], 2)
            
    except DatabaseError as e:
        logging.error(f"Failed to log prediction: {e}")
    
    return comparison


# ============================================================================
# Application Entry Point
# ============================================================================

# Create application instance
app = create_app()

if __name__ == '__main__':
    print("=" * 60)
    print("EcoPredict - Waste Management Intelligence System")
    print("=" * 60)
    print(f"Model loaded: {app.model.is_ready}")
    print(f"Areas available: {len(app.model.areas)}")
    print(f"Waste types available: {len(app.model.waste_types)}")
    print("-" * 60)
    print("Pages:")
    print("  - Home:      http://127.0.0.1:5000/")
    print("  - Dashboard: http://127.0.0.1:5000/dashboard")
    print("  - Analytics: http://127.0.0.1:5000/analytics")
    print("  - Compare:   http://127.0.0.1:5000/compare")
    print("  - History:   http://127.0.0.1:5000/history")
    print("  - Upload:    http://127.0.0.1:5000/upload")
    print("  - Settings:  http://127.0.0.1:5000/settings")
    print("  - Admin:     http://127.0.0.1:5000/admin")
    print("=" * 60)
    app.run(debug=True, port=5000)