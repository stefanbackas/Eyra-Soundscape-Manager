import sys
from PyQt5.QtWidgets import QApplication, QDialog  # Lägg till QDialog
from metadata_window import MetadataFilterWindow

# Exempeldatan från Google Sheets
metadata = [
    ["Environment", "Season", "Time of Day"],  # Rubriker
    ["Forest", "Spring", "Morning"],
    ["Sea", "Summer", "Afternoon"],
    ["Forest", "Autumn", "Evening"],
    ["Archipelago", "Winter", "Morning"]
]

app = QApplication(sys.argv)
window = MetadataFilterWindow(metadata)
if window.exec_() == QDialog.Accepted:
    selected_filters = window.get_selected_filters()
    print("Valda filter:", selected_filters)
