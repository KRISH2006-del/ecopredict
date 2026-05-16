# Model loading and prediction utilities

import os
import logging
import joblib
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)


class ModelLoadError(Exception):
    """Exception raised when model fails to load"""
    pass


class PredictionError(Exception):
    """Exception raised when prediction fails"""
    pass


class WastePredictionModel:
    """Wrapper class for the waste prediction model"""
    
    def __init__(self, model_path, ui_values_path):
        self.model_path = model_path
        self.ui_values_path = ui_values_path
        self.model = None
        self.unique_values = {'areas': [], 'waste_types': []}
        self._load_model()
        self._load_ui_values()
    
    def _load_model(self):
        """Load the ML model from disk"""
        if not os.path.exists(self.model_path):
            logger.warning(f"Model file not found: {self.model_path}")
            return
        
        try:
            self.model = joblib.load(self.model_path)
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise ModelLoadError(f"Could not load model: {e}")
    
    def _load_ui_values(self):
        """Load UI dropdown values from disk"""
        if not os.path.exists(self.ui_values_path):
            logger.warning(f"UI values file not found: {self.ui_values_path}")
            return
        
        try:
            self.unique_values = joblib.load(self.ui_values_path)
            logger.info("UI values loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load UI values: {e}")
    
    @property
    def is_ready(self):
        """Check if model is loaded and ready"""
        return self.model is not None
    
    @property
    def areas(self):
        """Get list of valid areas"""
        return self.unique_values.get('areas', [])
    
    @property
    def waste_types(self):
        """Get list of valid waste types"""
        return self.unique_values.get('waste_types', [])
    
    def predict(self, area, waste_type, date):
        """
        Make a waste prediction.
        
        Args:
            area: Municipality area name
            waste_type: Type of waste
            date: Prediction date (datetime object or string)
        
        Returns:
            Predicted weight in kg
        
        Raises:
            PredictionError: If prediction fails
        """
        if not self.is_ready:
            raise PredictionError("Model not loaded. Run train_model.py first.")
        
        # Parse date if string
        if isinstance(date, str):
            try:
                date = datetime.strptime(date, '%Y-%m-%d')
            except ValueError as e:
                raise PredictionError(f"Invalid date format: {e}")
        
        # Prepare input DataFrame
        input_data = pd.DataFrame([{
            'area': area.strip(),
            'waste_type': waste_type.strip(),
            'year': date.year,
            'month': date.month,
            'day': date.day,
            'dayofweek': date.weekday()
        }])
        
        # Ensure column order
        feature_order = ['area', 'waste_type', 'year', 'month', 'day', 'dayofweek']
        input_data = input_data[feature_order]
        
        try:
            prediction = self.model.predict(input_data)[0]
            logger.debug(f"Prediction made: {prediction}")
            return float(prediction)
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise PredictionError(f"Prediction failed: {e}")
