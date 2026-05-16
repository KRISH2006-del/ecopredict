# Model selection routes

from flask import Blueprint, render_template, request, jsonify, session
import logging

logger = logging.getLogger(__name__)

models_bp = Blueprint('models', __name__, url_prefix='/models')


def register_model_routes(app, model_manager):
    """Register model selection routes"""
    
    @models_bp.route('/')
    def models_page():
        """Model selection page"""
        models = model_manager.get_available_models()
        comparison = model_manager.get_model_comparison()
        
        # Get current model info
        current_id = model_manager.current_model_id
        current_info = model_manager.model_info.get(current_id, {})
        current_model = {
            'id': current_id,
            'name': current_info.get('name', current_id),
            'description': current_info.get('description', ''),
            'mae': current_info.get('mae', 0),
            'r2': current_info.get('r2', 0)
        }
        
        return render_template(
            'models.html',
            models=models,
            current_model=current_model,
            comparison=comparison,
            areas=model_manager.areas,
            waste_types=model_manager.waste_types
        )
    
    @models_bp.route('/select', methods=['POST'])
    def select_model():
        """Select a model"""
        data = request.get_json()
        model_id = data.get('model_id')
        
        if model_id and model_manager.set_current_model(model_id):
            # Save preference in session
            session['selected_model'] = model_id
            return jsonify({'success': True, 'model': model_id})
        
        return jsonify({'error': 'Model not found'}), 400
    
    @models_bp.route('/predict-all', methods=['POST'])
    def predict_all():
        """Get predictions from all models"""
        from validators import validate_prediction_input
        from datetime import datetime
        
        try:
            area = request.form.get('area')
            waste_type = request.form.get('waste_type')
            date_str = request.form.get('date')
            
            # Validate
            area, waste_type, date_obj = validate_prediction_input(
                area, waste_type, date_str,
                model_manager.areas,
                model_manager.waste_types
            )
            
            # Get predictions from all models
            predictions = model_manager.predict_all_models(area, waste_type, date_obj)
            
            return jsonify({
                'predictions': predictions,
                'input': {
                    'area': area,
                    'waste_type': waste_type,
                    'date': date_str
                }
            })
            
        except Exception as e:
            logger.error(f"Multi-predict failed: {e}")
            return jsonify({'error': str(e)}), 400
    
    @models_bp.route('/api/list')
    def list_models():
        """API endpoint for available models"""
        return jsonify({
            'models': model_manager.get_available_models(),
            'current': model_manager.current_model_id
        })
    
    @models_bp.route('/api/comparison')
    def model_comparison():
        """API endpoint for model comparison data"""
        return jsonify(model_manager.get_model_comparison())
    
    app.register_blueprint(models_bp)
