# Tests for validators module

import pytest
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validators import InputValidator, ValidationError, validate_prediction_input


class TestInputValidator:
    """Tests for InputValidator class"""
    
    def test_validate_required_with_value(self):
        """Test that validate_required passes with value"""
        result = InputValidator.validate_required("test", "Field")
        assert result == "test"
    
    def test_validate_required_with_empty_string(self):
        """Test that validate_required fails with empty string"""
        with pytest.raises(ValidationError) as exc_info:
            InputValidator.validate_required("", "Field")
        assert "required" in str(exc_info.value)
    
    def test_validate_required_with_none(self):
        """Test that validate_required fails with None"""
        with pytest.raises(ValidationError):
            InputValidator.validate_required(None, "Field")
    
    def test_validate_required_strips_whitespace(self):
        """Test that validate_required strips whitespace"""
        result = InputValidator.validate_required("  test  ", "Field")
        assert result == "test"
    
    def test_validate_date_valid(self):
        """Test date validation with valid date"""
        result = InputValidator.validate_date("2026-01-15", "Date")
        assert isinstance(result, datetime)
        assert result.year == 2026
        assert result.month == 1
        assert result.day == 15
    
    def test_validate_date_invalid_format(self):
        """Test date validation fails with invalid format"""
        with pytest.raises(ValidationError) as exc_info:
            InputValidator.validate_date("15/01/2026", "Date")
        assert "format" in str(exc_info.value).lower()
    
    def test_validate_date_min_date(self):
        """Test date validation with min_date constraint"""
        min_date = datetime(2026, 1, 1)
        
        # Valid: after min_date
        result = InputValidator.validate_date("2026-02-01", "Date", min_date=min_date)
        assert result is not None
        
        # Invalid: before min_date
        with pytest.raises(ValidationError):
            InputValidator.validate_date("2025-12-01", "Date", min_date=min_date)
    
    def test_validate_in_list_valid(self):
        """Test validate_in_list with valid value"""
        valid_list = ['a', 'b', 'c']
        result = InputValidator.validate_in_list('b', valid_list, "Field")
        assert result == 'b'
    
    def test_validate_in_list_invalid(self):
        """Test validate_in_list fails with invalid value"""
        valid_list = ['a', 'b', 'c']
        with pytest.raises(ValidationError):
            InputValidator.validate_in_list('d', valid_list, "Field")
    
    def test_sanitize_string_strips_whitespace(self):
        """Test that sanitize_string strips whitespace"""
        result = InputValidator.sanitize_string("  test  ")
        assert result == "test"
    
    def test_sanitize_string_limits_length(self):
        """Test that sanitize_string limits length"""
        long_string = "a" * 500
        result = InputValidator.sanitize_string(long_string, max_length=100)
        assert len(result) == 100
    
    def test_sanitize_string_removes_dangerous_chars(self):
        """Test that sanitize_string removes dangerous characters"""
        result = InputValidator.sanitize_string("test;<>value")
        assert ";" not in result
        assert "<" not in result
        assert ">" not in result


class TestValidatePredictionInput:
    """Tests for validate_prediction_input function"""
    
    def test_valid_input(self):
        """Test validation with valid input"""
        area, waste_type, date = validate_prediction_input(
            "TestArea",
            "TestType",
            "2026-01-15",
            ["TestArea", "OtherArea"],
            ["TestType", "OtherType"]
        )
        
        assert area == "TestArea"
        assert waste_type == "TestType"
        assert isinstance(date, datetime)
    
    def test_missing_area(self):
        """Test validation fails with missing area"""
        with pytest.raises(ValidationError) as exc_info:
            validate_prediction_input(
                "",
                "TestType",
                "2026-01-15",
                ["TestArea"],
                ["TestType"]
            )
        assert exc_info.value.field == "Area"
    
    def test_invalid_area(self):
        """Test validation fails with invalid area"""
        with pytest.raises(ValidationError):
            validate_prediction_input(
                "InvalidArea",
                "TestType",
                "2026-01-15",
                ["TestArea"],
                ["TestType"]
            )
    
    def test_invalid_waste_type(self):
        """Test validation fails with invalid waste type"""
        with pytest.raises(ValidationError):
            validate_prediction_input(
                "TestArea",
                "InvalidType",
                "2026-01-15",
                ["TestArea"],
                ["TestType"]
            )
