import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import os

import sqlite3

# Load Data
DB_PATH = 'waste.db'
if not os.path.exists(DB_PATH):
    print(f"Error: Database not found at {DB_PATH}. Run setup_db.py first.")
    exit(1)

print(f"Loading data from {DB_PATH}...")
conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT * FROM training_data", conn)
conn.close()

# Feature Engineering
print("Feature Engineering...")
df['ticket_date'] = pd.to_datetime(df['ticket_date'])
df['year'] = df['ticket_date'].dt.year
df['month'] = df['ticket_date'].dt.month
df['day'] = df['ticket_date'].dt.day
df['dayofweek'] = df['ticket_date'].dt.dayofweek

# Clean strings
df['area'] = df['area'].astype(str).str.strip()
df['waste_type'] = df['waste_type'].astype(str).str.strip()

# Select Features and Target
features = ['area', 'waste_type', 'year', 'month', 'day', 'dayofweek']
target = 'net_weight_kg'

X = df[features]
y = df[target]

# Preprocessing
categorical_features = ['area', 'waste_type']
categorical_transformer = OneHotEncoder(handle_unknown='ignore')

preprocessor = ColumnTransformer(
    transformers=[
        ('cat', categorical_transformer, categorical_features)
    ],
    remainder='passthrough'
)

# Pipeline
model = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('regressor', RandomForestRegressor(n_estimators=100, random_state=42))
])

# Splits
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train on Full Data for Production
print("Training Random Forest model on FULL dataset...")
model.fit(X, y)

# Evaluate (Optional, using split data just for metrics reference)
# Note: Evaluating on data allowed in training is optimistic, but we prioritize
# ensuring all UI categories are known to the encoder.
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
# We need a temporary model to verify metrics honestly if desired, 
# but here we just want the saved model to work.
# Let's just print that we are done.
print("Model trained on full dataset.")

# Save Model
output_model = 'waste_model_pipeline.joblib'
joblib.dump(model, output_model)
print(f"Model saved to {output_model}")

# Get unique areas and waste types for the UI
unique_values = {
    'areas': sorted(df['area'].astype(str).unique().tolist()),
    'waste_types': sorted(df['waste_type'].astype(str).unique().tolist())
}
output_values = 'ui_values.joblib'
joblib.dump(unique_values, output_values)
print(f"UI values saved to {output_values}")
