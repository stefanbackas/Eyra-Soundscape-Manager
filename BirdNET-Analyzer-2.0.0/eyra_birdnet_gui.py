import sys
import json
import subprocess
import os
import shutil
import tempfile
from PyQt5.QtWidgets import QTextEdit, QTextBrowser, QTableWidget, QTableWidgetItem, QLabel

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QFileDialog
    
)

SETTINGS_FILE = "settings.json"

from PyQt5.QtCore import QThread, pyqtSignal

class AnalysisThread(QThread):
    analysis_done = pyqtSignal(bool, str)

    def __init__(self, command, temp_wav_path=None, output_rename_path=None):
        super().__init__()
        self.command = command
        self.temp_wav_path = temp_wav_path
        self.output_rename_path = output_rename_path

    def run(self):
        import subprocess
        import shutil
        import os

        success = False
        try:
            subprocess.run(self.command, check=True)

            # Radera analys-parametern (onödig)
            params_csv = os.path.join("output", "BirdNET_analysis_params.csv")
            if os.path.exists(params_csv):
                os.remove(params_csv)

            # Byt namn på rätt outputfil (CombinedTable)
            combined_csv = os.path.join("output", "BirdNET_CombinedTable.csv")
            if self.output_rename_path and os.path.exists(combined_csv):
                if os.path.exists(self.output_rename_path):
                    os.remove(self.output_rename_path)
                os.rename(combined_csv, self.output_rename_path)

            success = True
        except subprocess.CalledProcessError:
            success = False

        # Radera tillfälliga filer om de finns
        if self.temp_wav_path and os.path.exists(self.temp_wav_path):
            shutil.rmtree(os.path.dirname(self.temp_wav_path))

        self.analysis_done.emit(success, self.output_rename_path if success else "")

# --- I din EyraBirdNETGUI-klass ---

class EyraBirdNETGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Eyra BirdNET Analyzer")

        # Ställ in fönstrets bakgrundsfärg och storlek
        self.setStyleSheet("background-color: #5C4033;")  # Eyra ljusbrun bakgrund
        self.resize(700, 800)

        layout = QVBoxLayout()

        # Välj ljudfil eller mapp
        self.file_path_input = QLineEdit()
        self.file_path_input.setReadOnly(True)
        self.file_path_input.setStyleSheet("background-color: #222222; color: #ffffff; border: none;")
        choose_file_button = QPushButton("Välj ljudfil eller mapp")
        choose_file_button.clicked.connect(self.choose_file_or_folder)
        layout.addWidget(QLabel("Välj ljudfil eller mapp:"))
        layout.addWidget(self.file_path_input)
        layout.addWidget(choose_file_button)
        choose_file_button.setStyleSheet("""
            QPushButton {
                background-color: #3B2F2F;
                color: white;
                border: none;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4E3C3C;
            }
        """)


        # Skapa fält för latitud, longitud, vecka och känslighet
        self.lat_input = QLineEdit()
        self.lat_input.setStyleSheet("background-color: #222222; color: #ffffff; border: none;")
        self.lon_input = QLineEdit()
        self.lon_input.setStyleSheet("background-color: #222222; color: #ffffff; border: none;")
        self.week_input = QLineEdit()
        self.week_input.setStyleSheet("background-color: #222222; color: #ffffff; border: none;")
        self.sensitivity_input = QLineEdit()
        self.sensitivity_input.setStyleSheet("background-color: #222222; color: #ffffff; border: none;")

        layout.addWidget(QLabel("Latitud:"))
        layout.addWidget(self.lat_input)
        layout.addWidget(QLabel("Longitud:"))
        layout.addWidget(self.lon_input)
        layout.addWidget(QLabel("Vecka:"))
        layout.addWidget(self.week_input)
        layout.addWidget(QLabel("Känslighet (0-1):"))
        layout.addWidget(self.sensitivity_input)

        # Knapp för att spara inställningar
        save_button = QPushButton("Spara inställningar")
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #3B2F2F;
                color: white;
                border: none;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4E3C3C;
            }
        """)


        # Knapp för att starta analys
        analyze_button = QPushButton("Starta analys")
        analyze_button.clicked.connect(self.start_analysis)
        layout.addWidget(analyze_button)
        analyze_button.setStyleSheet("""
            QPushButton {
                background-color: #3B2F2F;
                color: white;
                border: none;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4E3C3C;
            }
        """)


        # Lägg till resultatvisning (för analysresultatet)
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setLineWrapMode(QTextEdit.NoWrap)
        self.result_text.setFontFamily("Courier New")
        self.result_text.setFontPointSize(10)
        self.result_text.setStyleSheet("background-color: #222222; color: #ffffff; border: none;")
        layout.addWidget(QLabel("Analysresultat:"))
        layout.addWidget(self.result_text)

        # Lägg till visning av unika fågelarter
        self.unique_species_text = QTextBrowser()
        self.unique_species_text.setReadOnly(True)
        self.unique_species_text.setMaximumHeight(150)
        self.unique_species_text.setStyleSheet("background-color: #222222; color: #ffffff; font-family: Courier; font-size: 10pt; border: none;")
        layout.addWidget(QLabel("Fåglar i ljudfilen (unika namn i ordning):"))
        layout.addWidget(self.unique_species_text)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: white; font-weight: bold;")
        layout.addWidget(self.status_label)


        self.setLayout(layout)

        # Läs in inställningar om de finns
        self.load_settings()


    def save_settings(self):
        settings = {
            "latitude": self.lat_input.text(),
            "longitude": self.lon_input.text(),
            "week": self.week_input.text(),
            "sensitivity": self.sensitivity_input.text(),
            "input_path": self.file_path_input.text()
        }
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f)
        print("Inställningar sparade.")

    def load_settings(self):
        try:
            with open(SETTINGS_FILE, "r") as f:
                settings = json.load(f)
                self.lat_input.setText(str(settings.get("latitude", "")))
                self.lon_input.setText(str(settings.get("longitude", "")))
                self.week_input.setText(str(settings.get("week", "")))
                self.sensitivity_input.setText(str(settings.get("sensitivity", "")))
                self.file_path_input.setText(str(settings.get("input_path", "")))
        except FileNotFoundError:
            pass

    def choose_file_or_folder(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.AnyFile)
        if file_dialog.exec_():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                self.file_path_input.setText(selected_files[0])



    def start_analysis(self):
        input_path = self.file_path_input.text()
        if not input_path:
            print("Ingen fil eller mapp vald!")
            return

        import os
        temp_wav_path = None

        # Om filen är MP3, konvertera till WAV först
        if input_path.lower().endswith(".mp3"):
            print("MP3-fil vald, konverterar till WAV...")
            import tempfile
            temp_dir = tempfile.mkdtemp()
            temp_wav_path = os.path.join(temp_dir, "converted.wav")
            ffmpeg_command = [
                "ffmpeg",
                "-i", input_path,
                "-ar", "48000",
                "-ac", "1",
                temp_wav_path
            ]

            try:
                subprocess.run(ffmpeg_command, check=True)
                input_path = temp_wav_path
                print("Konvertering klar.")
            except subprocess.CalledProcessError:
                print("Fel vid konvertering av MP3 till WAV.")
                self.status_label.setText("❌ Fel vid konvertering!")
                return

        # Skapa filnamn baserat på ljudfilen
        original_name = os.path.basename(self.file_path_input.text())
        base_filename = os.path.splitext(original_name)[0]
        output_folder = "output"
        os.makedirs(output_folder, exist_ok=True)
        output_target = os.path.join(output_folder, f"{base_filename}_BirdNET.results.csv")

        # Skapa kommandot för BirdNET-analys
        latitude = self.lat_input.text() or "0.0"
        longitude = self.lon_input.text() or "0.0"
        week = self.week_input.text() or "0"
        sensitivity = self.sensitivity_input.text() or "0.5"

        command = [
            "/Library/Frameworks/Python.framework/Versions/3.10/bin/python3",
            "-m", "birdnet_analyzer.analyze",
            input_path,
            "-o", output_folder,
            "--lat", latitude,
            "--lon", longitude,
            "--week", week,
            "--sensitivity", sensitivity,
            "--min_conf", sensitivity,
            "--sf_thresh", "0.5",
            "--fmin", "200",
            "--fmax", "13000",
            "--overlap", "0",
            "--rtype", "csv",
            "--combine_results"
        ]

        self.status_label.setText("⏳ Analyserar...")

        self.analysis_thread = AnalysisThread(command, temp_wav_path, output_target)
        self.analysis_thread.analysis_done.connect(self.on_analysis_done)
        self.analysis_thread.start()

    def on_analysis_done(self, success, saved_path):
        if success:
            filename = os.path.basename(saved_path)
            self.status_label.setText(f"✅ Analys klar!\nFil sparad som: {filename}")
            self.load_results()
        else:
            self.status_label.setText("❌ Fel vid analysen!")


    def load_results(self):
        import glob
        import os
        import csv

        result_files = glob.glob(os.path.join("output", "*.BirdNET.results.csv"))
        if result_files:
            latest_result = max(result_files, key=os.path.getctime)
            lines = []
            unique_species = []

            with open(latest_result, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader)
                new_header = header[:5]  # Skippa File-kolumnen
                lines.append("\t".join(new_header))

                for row in reader:
                    new_row = row[:5]
                    lines.append("\t".join(new_row))

                    common_name = row[3]
                    if common_name not in unique_species:
                        unique_species.append(common_name)

            self.result_text.setText("\n".join(lines))
            self.unique_species_text.setText("\n".join(unique_species))
        else:
            self.result_text.setText("Inga analysresultat hittades.")
            self.unique_species_text.setText("")


                

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EyraBirdNETGUI()
    window.show()
    sys.exit(app.exec_())
