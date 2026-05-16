# Multi-Model Manager
# Handles loading and switching between different prediction models

import os
import json
import logging
import joblib
from datetime import datetime

logger = logging.getLogger(__name__)

MODELS_DIR = 'models'
RESULTS_FILE = os.path.join(MODELS_DIR, 'model_results.json')


class MultiModelManager:
    """Manages multiple prediction models"""
    
    def __init__(self, ui_values_path='ui_values.joblib'):
        self.models = {}
        self.model_info = {}
        self.current_model_id = 'random_forest'
        self.ui_values_path = ui_values_path
        self.areas = []
        self.waste_types = []
        self.is_ready = False
        
        self._load_ui_values()
        self._load_model_info()
        self._load_default_model()
    
    def _load_ui_values(self):
        """Load UI values (areas and waste types)"""
        try:
            if os.path.exists(self.ui_values_path):
                ui_values = joblib.load(self.ui_values_path)
                self.areas = ui_values.get('areas', [])
                self.waste_types = ui_values.get('waste_types', [])
                logger.info("UI values loaded")
        except Exception as e:
            logger.error(f"Failed to load UI values: {e}")
    
    def _load_model_info(self):
        """Load model metadata from results file"""
        try:
            if os.path.exists(RESULTS_FILE):
                with open(RESULTS_FILE, 'r') as f:
                    self.model_info = json.load(f)
                logger.info(f"Loaded info for {len(self.model_info)} models")
            else:
                # Default model info if results file doesn't exist
                self.model_info = {
                    'random_forest': {
                        'name': 'Random Forest',
                        'description': 'Ensemble of decision trees, robust and accurate',
                        'color': '#27ae60',
                        'mae': 0,
                        'r2': 0
                    }
                }
        except Exception as e:
            logger.error(f"Failed to load model info: {e}")
    
    def _load_default_model(self):
        """Load the default model"""
        # Try to load from models directory first
        default_path = os.path.join(MODELS_DIR, 'random_forest_model.joblib')
        fallback_path = 'waste_model_pipeline.joblib'
        
        model_path = default_path if os.path.exists(default_path) else fallback_path
        
        if self.load_model('random_forest', model_path):
            self.is_ready = True
        else:
            logger.warning("No default model found. Run train_models.py first.")
    
    def load_model(self, model_id, model_path=None):
        """Load a specific model"""
        if model_path is None:
            model_path = os.path.join(MODELS_DIR, f'{model_id}_model.joblib')
        
        try:
            if os.path.exists(model_path):
                self.models[model_id] = joblib.load(model_path)
                logger.info(f"Loaded model: {model_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to load model {model_id}: {e}")
        
        return False
    
    def get_model(self, model_id=None):
        """Get a specific model, loading it if necessary"""
        if model_id is None:
            model_id = self.current_model_id
        
        if model_id not in self.models:
            self.load_model(model_id)
        
        return self.models.get(model_id)
    
    def set_current_model(self, model_id):
        """Set the current active model"""
        if model_id in self.model_info or self.load_model(model_id):
            self.current_model_id = model_id
            return True
        return False
    
    def predict(self, area, waste_type, date_obj, model_id=None):
        """Make a prediction using a specific model"""
        import pandas as pd
        
        if model_id is None:
            model_id = self.current_model_id
        
        model = self.get_model(model_id)
        if model is None:
            raise ValueError(f"Model {model_id} not found")
        
        # Prepare input
        input_data = pd.DataFrame([{
            'area': area,
            'waste_type': waste_type,
            'year': date_obj.year,
            'month': date_obj.month,
            'day': date_obj.day,
            'dayofweek': date_obj.weekday()
        }])
        
        prediction = model.predict(input_data)[0]
        return max(0, prediction)  # Ensure non-negative
    
    def predict_all_models(self, area, waste_type, date_obj):
        """Get predictions from all available models"""
        import pandas as pd
        
        input_data = pd.DataFrame([{
            'area': area,
            'waste_type': waste_type,
            'year': date_obj.year,
            'month': date_obj.month,
            'day': date_obj.day,
            'dayofweek': date_obj.weekday()
        }])
        
        predictions = {}
        
        for model_id in self.model_info.keys():
            model = self.get_model(model_id)
            if model:
                try:
                    pred = model.predict(input_data)[0]
                    predictions[model_id] = {
                        'prediction': round(max(0, pred), 2),
                        'name': self.model_info[model_id].get('name', model_id),
                        'color': self.model_info[model_id].get('color', '#27ae60')
                    }
                except Exception as e:
                    logger.error(f"Prediction failed for {model_id}: {e}")
        
        return predictions
    
    def get_available_models(self):
        """Get list of available models with their info"""
        models = []
        for model_id, info in self.model_info.items():
            model_data = {
                'id': model_id,
                'name': info.get('name', model_id),
                'description': info.get('description', ''),
                'color': info.get('color', '#27ae60'),
                'mae': info.get('mae', 0),
                'rmse': info.get('rmse', 0),
                'r2': info.get('r2', 0),
                'is_current': model_id == self.current_model_id
            }
            models.append(model_data)
        
        # Sort by MAE (lower is better)
        models.sort(key=lambda x: x['mae'] if x['mae'] > 0 else float('inf'))
        return models
    
    def get_model_comparison(self):
        """Get model comparison data for visualization"""
        models = self.get_available_models()
        return {
            'labels': [m['name'] for m in models],
            'mae': [m['mae'] for m in models],
            'rmse': [m['rmse'] for m in models],
            'r2': [m['r2'] for m in models],
            'colors': [m['color'] for m in models]
        }
