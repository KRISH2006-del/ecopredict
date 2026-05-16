# API Documentation module

from flask import Blueprint, render_template, jsonify
import logging

logger = logging.getLogger(__name__)

api_docs_bp = Blueprint('api_docs', __name__)


def register_api_docs_routes(app):
    """Register API documentation routes"""
    
    @api_docs_bp.route('/api-docs')
    def api_documentation():
        """Render API documentation page"""
        return render_template('api_docs.html', endpoints=get_api_endpoints())
    
    @api_docs_bp.route('/api/endpoints')
    def list_endpoints():
        """Return list of all API endpoints"""
        return jsonify(get_api_endpoints())
    
    app.register_blueprint(api_docs_bp)


def get_api_endpoints():
    """Return documentation for all API endpoints"""
    return {
        'prediction': {
            'title': 'Prediction API',
            'endpoints': [
                {
                    'method': 'POST',
                    'path': '/predict',
                    'description': 'Make a waste prediction',
                    'parameters': [
                        {'name': 'area', 'type': 'string', 'required': True, 'description': 'Municipality area name'},
                        {'name': 'waste_type', 'type': 'string', 'required': True, 'description': 'Type of waste'},
                        {'name': 'date', 'type': 'string', 'required': True, 'description': 'Prediction date (YYYY-MM-DD)'}
                    ],
                    'response': {
                        'prediction': '123.45 kg',
                        'prediction_value': 123.45,
                        'comparison': {
                            'area_avg': 100.5,
                            'type_avg': 95.3,
                            'overall_avg': 105.2
                        }
                    }
                }
            ]
        },
        'statistics': {
            'title': 'Statistics API',
            'endpoints': [
                {
                    'method': 'GET',
                    'path': '/api/stats',
                    'description': 'Get dashboard statistics',
                    'parameters': [],
                    'response': {
                        'by_area': [{'area': 'Area1', 'count': 10, 'avg_weight': 100.5}],
                        'by_date': [{'date': '2026-01-01', 'total_weight': 500.0}],
                        'total_predictions': 100,
                        'avg_prediction': 105.5
                    }
                },
                {
                    'method': 'GET',
                    'path': '/api/health',
                    'description': 'Check API health status',
                    'parameters': [],
                    'response': {
                        'status': 'healthy',
                        'model_loaded': True,
                        'database_connected': True
                    }
                }
            ]
        },
        'analytics': {
            'title': 'Analytics API',
            'endpoints': [
                {
                    'method': 'GET',
                    'path': '/api/analytics/trends',
                    'description': 'Get prediction trends (daily, weekly, monthly)',
                    'parameters': [],
                    'response': {
                        'daily': [{'date': '2026-01-01', 'count': 5, 'avg': 100.5, 'total': 502.5}],
                        'weekly': [{'week': '2026-W01', 'count': 20, 'avg': 98.2, 'total': 1964.0}],
                        'monthly': [{'month': '2026-01', 'count': 80, 'avg': 102.1, 'total': 8168.0}]
                    }
                },
                {
                    'method': 'GET',
                    'path': '/api/analytics/patterns',
                    'description': 'Get seasonal and day-of-week patterns',
                    'parameters': [],
                    'response': {
                        'day_of_week': [{'day': 'Monday', 'avg': 105.2, 'count': 15}],
                        'monthly': [{'month': 'Jan', 'avg': 98.5, 'count': 80}]
                    }
                },
                {
                    'method': 'GET',
                    'path': '/api/analytics/areas',
                    'description': 'Get area-wise analysis',
                    'parameters': [],
                    'response': {
                        'areas': [{
                            'area': 'Downtown',
                            'count': 50,
                            'avg': 120.5,
                            'min': 50.0,
                            'max': 200.0,
                            'total': 6025.0
                        }]
                    }
                },
                {
                    'method': 'GET',
                    'path': '/api/analytics/summary',
                    'description': 'Get overall summary statistics',
                    'parameters': [],
                    'response': {
                        'total_predictions': 500,
                        'avg_weight': 105.5,
                        'min_weight': 10.0,
                        'max_weight': 500.0,
                        'total_weight': 52750.0,
                        'unique_areas': 5,
                        'unique_waste_types': 3
                    }
                }
            ]
        },
        'exports': {
            'title': 'Export API',
            'endpoints': [
                {
                    'method': 'GET',
                    'path': '/export/csv',
                    'description': 'Export predictions as CSV file',
                    'parameters': [],
                    'response': 'CSV file download'
                },
                {
                    'method': 'GET',
                    'path': '/export/pdf',
                    'description': 'Export predictions as printable HTML report',
                    'parameters': [],
                    'response': 'HTML file (auto-prints)'
                },
                {
                    'method': 'GET',
                    'path': '/export/json',
                    'description': 'Export predictions as JSON',
                    'parameters': [],
                    'response': {
                        'predictions': [{'prediction_date': '2026-01-01', 'area': 'Downtown', 'waste_type': 'Recyclable', 'predicted_weight_kg': 100.5}],
                        'count': 100
                    }
                }
            ]
        }
    }
