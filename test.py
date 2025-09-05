from googleapiclient.discovery import build
from google.oauth2 import service_account
import pandas as pd

# Funktion för att hämta metadata från Google Sheets
def fetch_metadata_from_google_sheets(spreadsheet_id, range_name, credentials_file):
    """Hämtar metadata från Google Sheets och returnerar det som en DataFrame."""
    # Autentisering
    creds = service_account.Credentials.from_service_account_file(
        credentials_file,
        scopes=["1tFo867jOPKON5SrCmFUcaqKFdvLkpU6kTcY0i7QcDw8"],
    )
    service = build("sheets", "v4", credentials=creds)

    # Hämta data från Google Sheets
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    values = result.get("values", [])

    # Konvertera till DataFrame för enkel hantering
    if values:
        headers = values[0]
        data = values[1:]
        df = pd.DataFrame(data, columns=headers)
        return df
    else:
        raise ValueError("Inga data hittades i Google Sheets.")
