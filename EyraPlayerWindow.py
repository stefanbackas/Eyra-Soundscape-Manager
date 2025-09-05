import os
import json
import subprocess
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox

class EyraPlayerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Eyra Player")
        self.setMinimumSize(300, 150)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.soundscape_combo = QComboBox()
        layout.addWidget(self.soundscape_combo)

        # Mappen där soundscape-filerna ligger
        self.soundscape_folder = "/Users/stefanbackas/Documents/000_EYRA/Eyra_Soundscapes/Designed_Soundscapes/"

        self.load_soundscapes()

        self.status_label = QLabel("Välj soundscape och starta Eyra Player.")
        layout.addWidget(self.status_label)

        self.start_button = QPushButton("Starta Eyra Player")
        self.start_button.clicked.connect(self.start_eyra_player)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stoppa Eyra Player")
        self.stop_button.clicked.connect(self.stop_eyra_player)
        self.stop_button.setEnabled(False)
        layout.addWidget(self.stop_button)

        # Sökväg till Eyra Player-skriptet och configfilen
        self.eyra_player_path = "/Users/stefanbackas/Documents/000_EYRA/Kod/EyraPlayer_v0_565.py"
        self.config_path = "/Users/stefanbackas/Documents/000_EYRA/Kod/EyraConfig.json"
        self.process = None

    def load_soundscapes(self):
        try:
            files = [f for f in os.listdir(self.soundscape_folder) if f.endswith(".json")]
            files.sort()
        except Exception as e:
            self.status_label.setText(f"Fel vid inläsning av soundscape-filer: {e}")
            files = []
        self.soundscape_combo.clear()
        self.soundscape_combo.addItems(files)

    def update_active_soundscape_in_config(self, selected_file):
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            self.status_label.setText(f"Fel vid läsning av configfil: {e}")
            return False

        # Uppdatera ActiveSoundscape med BARA filnamnet, inte sökväg
        if "GeneralSettings" in config and len(config["GeneralSettings"]) > 0:
            config["GeneralSettings"][0]["ActiveSoundscape"] = selected_file
        else:
            self.status_label.setText("Felaktigt format i configfil.")
            return False

        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            self.status_label.setText(f"Fel vid sparning av configfil: {e}")
            return False

        self.status_label.setText(f"ActiveSoundscape uppdaterad till: {selected_file}")
        return True

    def start_eyra_player(self):
        selected_file = self.soundscape_combo.currentText()
        if not selected_file:
            self.status_label.setText("❌ Välj ett soundscape först.")
            return

        if not self.update_active_soundscape_in_config(selected_file):
            return

        if self.process is None:
            try:
                self.process = subprocess.Popen(
                    ["python3", self.eyra_player_path, self.config_path],
                    cwd="/Users/stefanbackas/Documents/000_EYRA/Kod"  # rätt arbetskatalog
                )
                self.status_label.setText("🎧 Eyra Player har startat.")
                self.start_button.setEnabled(False)
                self.stop_button.setEnabled(True)
            except Exception as e:
                self.status_label.setText(f"❌ Fel: {e}")
        else:
            self.status_label.setText("Eyra Player är redan igång.")


    def stop_eyra_player(self):
        if self.process:
            self.process.terminate()
            self.process = None
            self.status_label.setText("🛑 Eyra Player har stoppats.")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
        else:
            self.status_label.setText("Ingen Eyra Player är igång.")
