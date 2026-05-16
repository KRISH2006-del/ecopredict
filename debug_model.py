import pandas as pd
import joblib
import os

MODEL_PATH = 'waste_model_pipeline.joblib'

if not os.path.exists(MODEL_PATH):
    print(f"Error: {MODEL_PATH} not found.")
    exit(1)

print("Loading model...")
model = joblib.load(MODEL_PATH)

# Define test cases: Same date, different categorical values
test_cases = [
    {'area': 'Boralesgamuwa UC', 'waste_type': 'MSW', 'year': 2026, 'month': 2, 'day': 3, 'dayofweek': 1},
    {'area': 'Dehiwala MC', 'waste_type': 'MSW', 'year': 2026, 'month': 2, 'day': 3, 'dayofweek': 1},
    {'area': 'Boralesgamuwa UC', 'waste_type': 'Biodegradable', 'year': 2026, 'month': 2, 'day': 3, 'dayofweek': 1},
]

print("\n--- Test Predictions ---")
for case in test_cases:
    df = pd.DataFrame([case])
    
    # Predict
    try:
        # Step 1: Preprocessing check (if possible to access internal steps)
        if hasattr(model, 'named_steps'):
            preprocessor = model.named_steps['preprocessor']
            transformed_X = preprocessor.transform(df)
            print(f"\nInput: {case}")
            print(f"Transformed Features Shape: {transformed_X.shape}")
            # print(f"Transformed Data (sample): {transformed_X.toarray() if hasattr(transformed_X, 'toarray') else transformed_X}") # Verbose
            
        pred = model.predict(df)[0]
        print(f"Prediction: {pred:.2f} kg")
    except Exception as e:
        print(f"Error predicting for {case}: {e}")
