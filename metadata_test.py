import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

def fetch_advanced_metadata():
    """Fetch advanced metadata including columns BP, BQ, and BR."""
    try:
        SPREADSHEET_ID = "1tFo867jOPKON5SrCmFUcaqKFdvLkpU6kTcY0i7QcDw8"
        SERVICE_ACCOUNT_FILE = "credentials.json"
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds)

        # Define range for advanced metadata
        range_advanced = "BP2:BR"

        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=range_advanced
        ).execute()

        values = result.get('values', [])

        if not values:
            print("No data found in the range BP2:BR.")
            return None

        # Convert to DataFrame
        headers = ["English", "Latin", "Swedish"]  # Adjust based on expected column names
        data = values
        metadata = pd.DataFrame(data, columns=headers)

        print("[DEBUG] Fetched Advanced Metadata:")
        print(metadata.head())  # Show first rows for debugging

        return metadata

    except Exception as e:
        print(f"[ERROR] Error fetching advanced metadata: {e}")
        return None

# Test function
if __name__ == "__main__":
    advanced_metadata = fetch_advanced_metadata()
    if advanced_metadata is not None:
        print("Advanced Metadata Loaded Successfully")
        print(advanced_metadata)
    else:
        print("Failed to load Advanced Metadata")
