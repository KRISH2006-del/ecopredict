# Pytest configuration and fixtures

import pytest
import os
import sys
import tempfile
import sqlite3

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def app():
    """Create application for testing"""
    from app import create_app
    from config import TestingConfig
    
    # Create a temporary database
    db_fd, db_path = tempfile.mkstemp()
    
    class TestConfig(TestingConfig):
        DATABASE_PATH = db_path
        TESTING = True
        SECRET_KEY = 'test-secret-key'
    
    app = create_app()
    app.config.from_object(TestConfig)
    
    # Initialize test database
    with app.app_context():
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS training_data (
                id INTEGER PRIMARY KEY,
                area TEXT,
                waste_type TEXT,
                ticket_date TEXT,
                net_weight_kg REAL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prediction_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                area TEXT,
                waste_type TEXT,
                prediction_date TEXT,
                predicted_weight_kg REAL,
                user_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                email TEXT UNIQUE,
                password_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_admin INTEGER DEFAULT 0
            )
        ''')
        
        # Insert sample data
        cursor.execute('''
            INSERT INTO training_data (area, waste_type, ticket_date, net_weight_kg)
            VALUES ('TestArea', 'TestType', '2026-01-01', 100.0)
        ''')
        
        conn.commit()
        conn.close()
    
    yield app
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Test client for the application"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Test CLI runner"""
    return app.test_cli_runner()
