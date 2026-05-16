import pandas as pd
import sys

csv_path = r"C:\Users\DELL\Documents\wmgmt.csv"
try:
    print(f"Loading {csv_path}...")
    df = pd.read_csv(csv_path)
    print("Data loaded. Sample dates:")
    print(df['ticket_date'].head())
    print(df['ticket_date'].tail())

    print("\nAttempting default conversion (user's code)...")
    try:
        df['ticket_date'] = pd.to_datetime(df['ticket_date'])
        print("Default conversion SUCCESS (Unexpected if there are ambiguous dates).")
    except Exception as e:
        print(f"Default conversion FAILED as expected: {e}")

    print("\nAttempting fixed conversion (dayfirst=True)...")
    try:
        # Reload to reset
        df = pd.read_csv(csv_path)
        df['ticket_date'] = pd.to_datetime(df['ticket_date'], dayfirst=True)
        print("Fixed conversion SUCCESS.")
        print("Converted sample:")
        print(df['ticket_date'].head())
        print(df['ticket_date'].tail())
    except Exception as e:
        print(f"Fixed conversion FAILED: {e}")
        sys.exit(1)

except Exception as e:
    print(f"Error reading CSV: {e}")
    sys.exit(1)
