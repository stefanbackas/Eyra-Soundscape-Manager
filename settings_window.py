import json
import os
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QFileDialog, QHBoxLayout

class SettingsWindow(QDialog):
    CONFIG_FILE = "settings.json"  # Fil för att spara inställningar
    DEFAULT_FOLDER = "SavedBank"  # Standardmapp

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inställningar")
        self.resize(400, 300)  # Gör fönstret större

        # Huvudlayout
        main_layout = QVBoxLayout()

        # Etikett för att visa vald mapp
        self.folder_label = QLabel("Ingen mapp vald.")
        main_layout.addWidget(self.folder_label)

        # Knapp för att välja mapp
        self.select_folder_button = QPushButton("Välj mapp")
        self.select_folder_button.clicked.connect(self.select_folder)
        main_layout.addWidget(self.select_folder_button)

        # Layout för "Spara och Stäng"-knappen längst ner
        button_layout = QHBoxLayout()
        button_layout.addStretch()  # Skjut knappen till höger
        self.save_button = QPushButton("Spara och Stäng")
        self.save_button.clicked.connect(self.save_and_close)
        button_layout.addWidget(self.save_button)

        # Lägg till knapplayouten i huvudlayouten
        main_layout.addStretch()  # Skjut innehållet uppåt
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        # Ladda tidigare inställningar eller använd standardmapp
        self.load_settings()

    def select_folder(self):
        """Öppnar en dialog för att välja en mapp och visar sökvägen."""
        folder = QFileDialog.getExistingDirectory(self, "Välj en mapp")
        if folder:
            self.folder_label.setText(f"Vald mapp: {folder}")

    def save_and_close(self):
        """Spara inställningar och stäng fönstret."""
        folder = self.folder_label.text().replace("Vald mapp: ", "")
        if folder and folder != "Ingen mapp vald.":
            settings = {"save_folder": folder}
            with open(self.CONFIG_FILE, "w") as file:
                json.dump(settings, file)
            print(f"Inställningar sparade: {settings}")
        else:
            print("Ingen giltig mapp vald.")

        self.accept()  # Stänger dialogen

    def load_settings(self):
        """Ladda inställningar från JSON-fil eller använd standardmapp."""
        if os.path.exists(self.CONFIG_FILE):
            with open(self.CONFIG_FILE, "r") as file:
                settings = json.load(file)
                folder = settings.get("save_folder", self.DEFAULT_FOLDER)
        else:
            folder = self.DEFAULT_FOLDER

        self.folder_label.setText(f"Vald mapp: {folder}")
        print(f"Inställningar laddade: {folder}")