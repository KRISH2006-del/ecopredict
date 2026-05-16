# Tests for API routes

import pytest
import json


class TestHealthEndpoint:
    """Tests for health check endpoint"""
    
    def test_health_check(self, client):
        """Test that health endpoint returns status"""
        response = client.get('/api/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'status' in data
        assert 'model_loaded' in data
        assert 'database_connected' in data


class TestStatsEndpoint:
    """Tests for statistics endpoint"""
    
    def test_stats_returns_structure(self, client):
        """Test that stats endpoint returns expected structure"""
        response = client.get('/api/stats')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'by_area' in data
        assert 'by_date' in data
        assert 'total_predictions' in data
        assert 'avg_prediction' in data


class TestExportEndpoints:
    """Tests for export endpoints"""
    
    def test_csv_export(self, client):
        """Test CSV export returns correct content type"""
        response = client.get('/export/csv')
        assert response.status_code == 200
        assert 'text/csv' in response.content_type
    
    def test_json_export(self, client):
        """Test JSON export returns correct structure"""
        response = client.get('/export/json')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'predictions' in data
        assert 'count' in data


class TestAnalyticsEndpoints:
    """Tests for analytics endpoints"""
    
    def test_trends_endpoint(self, client):
        """Test trends endpoint returns data"""
        response = client.get('/api/analytics/trends')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'daily' in data
        assert 'weekly' in data
        assert 'monthly' in data
    
    def test_patterns_endpoint(self, client):
        """Test patterns endpoint returns data"""
        response = client.get('/api/analytics/patterns')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'day_of_week' in data
        assert 'monthly' in data
    
    def test_summary_endpoint(self, client):
        """Test summary endpoint returns statistics"""
        response = client.get('/api/analytics/summary')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'total_predictions' in data
        assert 'avg_weight' in data


class TestPageRoutes:
    """Tests for page routes"""
    
    def test_index_page_loads(self, client):
        """Test that index page loads"""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_dashboard_page_loads(self, client):
        """Test that dashboard page loads"""
        response = client.get('/dashboard')
        assert response.status_code == 200
    
    def test_history_page_loads(self, client):
        """Test that history page loads"""
        response = client.get('/history')
        assert response.status_code == 200
    
    def test_analytics_page_loads(self, client):
        """Test that analytics page loads"""
        response = client.get('/analytics')
        assert response.status_code == 200
    
    def test_api_docs_page_loads(self, client):
        """Test that API docs page loads"""
        response = client.get('/api-docs')
        assert response.status_code == 200


class TestAuthRoutes:
    """Tests for authentication routes"""
    
    def test_login_page_loads(self, client):
        """Test that login page loads"""
        response = client.get('/login')
        assert response.status_code == 200
    
    def test_register_page_loads(self, client):
        """Test that register page loads"""
        response = client.get('/register')
        assert response.status_code == 200
