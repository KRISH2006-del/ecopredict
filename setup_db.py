import pandas as pd
import sqlite3
import os

# Configuration
CSV_PATH = r"C:\Users\DELL\Documents\wmgmt.csv"
DB_PATH = 'waste.db'

def setup_database():
    if not os.path.exists(CSV_PATH):
        print(f"Error: CSV file not found at {CSV_PATH}")
        return

    print(f"Reading data from {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH)

    # Clean data (Fixing previous issue persistently)
    print("Cleaning data (stripping whitespace)...")
    df['area'] = df['area'].astype(str).str.strip()
    df['waste_type'] = df['waste_type'].astype(str).str.strip()
    
    # Standardize date format for SQL storage
    df['ticket_date'] = pd.to_datetime(df['ticket_date'], dayfirst=True).dt.strftime('%Y-%m-%d')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Create Training Data Table
    print("Creating 'training_data' table...")
    df.to_sql('training_data', conn, if_exists='replace', index=False)

    # 2. Create Predictions Log Table
    print("Creating 'prediction_logs' table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prediction_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            area TEXT,
            waste_type TEXT,
            prediction_date TEXT,
            predicted_weight_kg REAL
        )
    ''')

    conn.commit()
    conn.close()
    print(f"Database setup complete. Data saved to {DB_PATH}")

if __name__ == '__main__':
    setup_database()
