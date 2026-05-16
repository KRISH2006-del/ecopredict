# Multi-Model Training Script
# Trains multiple ML models for comparison

import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, AdaBoostRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.tree import DecisionTreeRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.svm import SVR
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import sqlite3
import os
import json
import numpy as np

# Configuration
DB_PATH = 'waste.db'
MODELS_DIR = 'models'

# Create models directory
os.makedirs(MODELS_DIR, exist_ok=True)

# Available models
MODELS = {
    'random_forest': {
        'name': 'Random Forest',
        'description': 'Ensemble of decision trees, robust and accurate',
        'model': RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1),
        'color': '#27ae60'
    },
    'gradient_boosting': {
        'name': 'Gradient Boosting',
        'description': 'Sequential ensemble with high accuracy',
        'model': GradientBoostingRegressor(n_estimators=100, random_state=42),
        'color': '#3498db'
    },
    'linear_regression': {
        'name': 'Linear Regression',
        'description': 'Simple and interpretable baseline model',
        'model': LinearRegression(),
        'color': '#9b59b6'
    },
    'ridge': {
        'name': 'Ridge Regression',
        'description': 'Linear model with L2 regularization',
        'model': Ridge(alpha=1.0),
        'color': '#e74c3c'
    },
    'decision_tree': {
        'name': 'Decision Tree',
        'description': 'Single tree, fast and interpretable',
        'model': DecisionTreeRegressor(max_depth=10, random_state=42),
        'color': '#f39c12'
    },
    'knn': {
        'name': 'K-Nearest Neighbors',
        'description': 'Instance-based learning',
        'model': KNeighborsRegressor(n_neighbors=5),
        'color': '#1abc9c'
    },
    'adaboost': {
        'name': 'AdaBoost',
        'description': 'Adaptive boosting ensemble',
        'model': AdaBoostRegressor(n_estimators=50, random_state=42),
        'color': '#e67e22'
    }
}

def load_data():
    """Load training data from database"""
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return None
    
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM training_data", conn)
    conn.close()
    return df

def prepare_features(df):
    """Prepare features for training"""
    df = df.copy()
    df['ticket_date'] = pd.to_datetime(df['ticket_date'])
    df['year'] = df['ticket_date'].dt.year
    df['month'] = df['ticket_date'].dt.month
    df['day'] = df['ticket_date'].dt.day
    df['dayofweek'] = df['ticket_date'].dt.dayofweek
    
    df['area'] = df['area'].astype(str).str.strip()
    df['waste_type'] = df['waste_type'].astype(str).str.strip()
    
    return df

def create_preprocessor():
    """Create the preprocessing pipeline"""
    categorical_features = ['area', 'waste_type']
    categorical_transformer = OneHotEncoder(handle_unknown='ignore')
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', categorical_transformer, categorical_features)
        ],
        remainder='passthrough'
    )
    return preprocessor

def train_all_models():
    """Train all available models"""
    print("=" * 60)
    print("Multi-Model Training System")
    print("=" * 60)
    
    # Load data
    print("\nLoading data...")
    df = load_data()
    if df is None:
        return
    
    print(f"Loaded {len(df)} records")
    
    # Prepare features
    print("Preparing features...")
    df = prepare_features(df)
    
    features = ['area', 'waste_type', 'year', 'month', 'day', 'dayofweek']
    target = 'net_weight_kg'
    
    X = df[features]
    y = df[target]
    
    # Split for evaluation
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Save UI values
    unique_values = {
        'areas': sorted(df['area'].unique().tolist()),
        'waste_types': sorted(df['waste_type'].unique().tolist())
    }
    joblib.dump(unique_values, 'ui_values.joblib')
    print("UI values saved")
    
    # Create preprocessor
    preprocessor = create_preprocessor()
    
    # Train and evaluate each model
    results = {}
    print("\n" + "-" * 60)
    print("Training Models...")
    print("-" * 60)
    
    for model_id, model_info in MODELS.items():
        print(f"\n[{model_info['name']}]")
        
        try:
            # Create pipeline
            pipeline = Pipeline(steps=[
                ('preprocessor', preprocessor),
                ('regressor', model_info['model'])
            ])
            
            # Train on full data
            pipeline.fit(X, y)
            
            # Evaluate on test set
            y_pred = pipeline.predict(X_test)
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            r2 = r2_score(y_test, y_pred)
            
            # Save model
            model_path = os.path.join(MODELS_DIR, f'{model_id}_model.joblib')
            joblib.dump(pipeline, model_path)
            
            results[model_id] = {
                'name': model_info['name'],
                'description': model_info['description'],
                'color': model_info['color'],
                'mae': round(mae, 2),
                'rmse': round(rmse, 2),
                'r2': round(r2, 4),
                'path': model_path
            }
            
            print(f"  MAE: {mae:.2f} | RMSE: {rmse:.2f} | R2: {r2:.4f}")
            print(f"  Saved to {model_path}")
            
        except Exception as e:
            print(f"  Error: {e}")
    
    # Save results
    results_path = os.path.join(MODELS_DIR, 'model_results.json')
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nModel results saved to {results_path}")
    
    # Also save default model (Random Forest)
    default_path = 'waste_model_pipeline.joblib'
    if 'random_forest' in results:
        import shutil
        shutil.copy(os.path.join(MODELS_DIR, 'random_forest_model.joblib'), default_path)
        print(f"Default model (Random Forest) saved to {default_path}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Training Complete!")
    print("=" * 60)
    print(f"Models trained: {len(results)}")
    
    # Find best model
    if results:
        best_model = min(results.items(), key=lambda x: x[1]['mae'])
        print(f"Best model (lowest MAE): {best_model[1]['name']} (MAE: {best_model[1]['mae']})")

if __name__ == '__main__':
    train_all_models()
