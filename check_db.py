import sqlite3
import pandas as pd
import os

DB_PATH = 'waste.db'

if not os.path.exists(DB_PATH):
    print(f"Error: Database not found at {DB_PATH}")
    exit(1)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print(f"--- Database Inspection: {DB_PATH} ---\n")

# Check Training Data
try:
    cursor.execute("SELECT COUNT(*) FROM training_data")
    count = cursor.fetchone()[0]
    print(f"Training Data Rows: {count}")
    print("Sample (first 3 rows):")
    print(pd.read_sql_query("SELECT * FROM training_data LIMIT 3", conn))
except Exception as e:
    print(f"Error reading training_data: {e}")

print("\n------------------------------------------------\n")

# Check Prediction Logs
try:
    print("Prediction Logs:")
    logs_df = pd.read_sql_query("SELECT * FROM prediction_logs ORDER BY id DESC", conn)
    if logs_df.empty:
        print("No predictions logged yet.")
    else:
        print(logs_df)
except Exception as e:
    print(f"Error reading prediction_logs: {e}")

conn.close()
