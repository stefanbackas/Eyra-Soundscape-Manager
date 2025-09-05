from googleapiclient.discovery import build
from google.oauth2 import service_account

# Konfigurera dina parametrar här
SPREADSHEET_ID = "1tFo867jOPKON5SrCmFUcaqKFdvLkpU6kTcY0i7QcDw8"  # Ersätt med ditt Spreadsheet-ID
RANGE_NAME = "Sheet1!A1:J"  # Justera intervallet om nödvändigt
CREDENTIALS_FILE = "credentials.json"  # Sökvägen till din credentials-fil

def fetch_metadata():
    """Hämta metadata från Google Sheets."""
    try:
        # Ladda upp credentials
        creds = service_account.Credentials.from_service_account_file(
            CREDENTIALS_FILE,
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
        )

        # Anslut till Google Sheets API
        service = build("sheets", "v4", credentials=creds)
        sheet = service.spreadsheets()

        # Hämta data
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        rows = result.get("values", [])

        if not rows:
            print("Inga data hittades.")
            return []

        # Skriv ut data
        print("Metadata hämtat från Google Sheets:")
        for row in rows:
            print(row)

        return rows
    except Exception as e:
        print(f"Fel vid hämtning av metadata: {e}")
        return []

# Testa att hämta metadata
if __name__ == "__main__":
    fetch_metadata()
