from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QMessageBox

class MetadataFilterWindow(QDialog):
    """Fönster för att filtrera metadata från Google Sheets."""
    
    def __init__(self, metadata, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Metadata Filter")
        self.resize(400, 300)

        self.metadata = metadata  # Metadata från Google Sheets
        self.selected_filters = {}  # Användarens valda filter

        # Layout
        self.layout = QVBoxLayout(self)

        # Lägga till widgets för varje kolumn i metadata
        self.filter_widgets = {}
        for column in metadata[0]:  # Första raden är rubriker
            label = QLabel(f"Filter för {column}:")
            self.layout.addWidget(label)

            combo = QComboBox()
            combo.addItem("Alla")  # Första valet är "Alla"
            combo.addItems(sorted(set(row[metadata[0].index(column)] for row in metadata[1:])))
            self.layout.addWidget(combo)

            self.filter_widgets[column] = combo

        # OK-knapp
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.apply_filters)
        self.layout.addWidget(self.ok_button)

    def apply_filters(self):
        """Samla användarens valda filter."""
        self.selected_filters = {
            column: combo.currentText()
            for column, combo in self.filter_widgets.items()
            if combo.currentText() != "Alla"
        }
        self.accept()  # Stäng fönstret och returnera med QDialog.Accepted

    def get_selected_filters(self):
        """Returnera valda filter."""
        return self.selected_filters
