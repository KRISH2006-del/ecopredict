# Validation utilities for input data

import re
from datetime import datetime, timedelta


class ValidationError(Exception):
    """Custom exception for validation errors"""
    def __init__(self, message, field=None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class InputValidator:
    """Utility class for validating user inputs"""
    
    @staticmethod
    def validate_required(value, field_name):
        """Check if a value is provided"""
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValidationError(f"{field_name} is required", field=field_name)
        return value.strip() if isinstance(value, str) else value
    
    @staticmethod
    def validate_date(date_str, field_name="Date", min_date=None, max_date=None):
        """
        Validate a date string.
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            field_name: Name of the field for error messages
            min_date: Minimum allowed date (optional)
            max_date: Maximum allowed date (optional)
        
        Returns:
            datetime object
        """
        if not date_str:
            raise ValidationError(f"{field_name} is required", field=field_name)
        
        try:
            date_obj = datetime.strptime(date_str.strip(), '%Y-%m-%d')
        except ValueError:
            raise ValidationError(
                f"Invalid {field_name.lower()} format. Use YYYY-MM-DD.", 
                field=field_name
            )
        
        if min_date and date_obj < min_date:
            raise ValidationError(
                f"{field_name} cannot be before {min_date.strftime('%Y-%m-%d')}", 
                field=field_name
            )
        
        if max_date and date_obj > max_date:
            raise ValidationError(
                f"{field_name} cannot be after {max_date.strftime('%Y-%m-%d')}", 
                field=field_name
            )
        
        return date_obj
    
    @staticmethod
    def validate_in_list(value, valid_list, field_name):
        """Check if value is in a list of valid options"""
        if value not in valid_list:
            raise ValidationError(
                f"Invalid {field_name.lower()}. Please select a valid option.", 
                field=field_name
            )
        return value
    
    @staticmethod
    def sanitize_string(value, max_length=255):
        """Sanitize a string input"""
        if not isinstance(value, str):
            return value
        
        # Strip whitespace
        value = value.strip()
        
        # Limit length
        if len(value) > max_length:
            value = value[:max_length]
        
        # Remove potentially dangerous characters for SQL (basic protection)
        # Note: Parameterized queries are the primary protection
        value = re.sub(r'[;<>]', '', value)
        
        return value


def validate_prediction_input(area, waste_type, date_str, valid_areas, valid_waste_types):
    """
    Validate all inputs for a prediction request.
    
    Returns:
        Tuple of (validated_area, validated_waste_type, validated_date)
    
    Raises:
        ValidationError: If any validation fails
    """
    validator = InputValidator()
    
    # Validate required fields
    area = validator.validate_required(area, "Area")
    waste_type = validator.validate_required(waste_type, "Waste Type")
    date_str = validator.validate_required(date_str, "Date")
    
    # Sanitize strings
    area = validator.sanitize_string(area)
    waste_type = validator.sanitize_string(waste_type)
    
    # Validate against valid options
    area = validator.validate_in_list(area, valid_areas, "Area")
    waste_type = validator.validate_in_list(waste_type, valid_waste_types, "Waste Type")
    
    # Validate date (allow dates within a reasonable range)
    min_date = datetime(2000, 1, 1)
    max_date = datetime.now() + timedelta(days=365 * 10)  # 10 years in future
    date_obj = validator.validate_date(date_str, "Forecast Date", min_date, max_date)
    
    return area, waste_type, date_obj
