import sys
import os
import subprocess
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QLabel, QVBoxLayout, QWidget, QProgressBar, QLineEdit
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class ConversionThread(QThread):
    progress = pyqtSignal(int)
    stopped = pyqtSignal()

    def __init__(self, input_dir, output_dir, bitrate):
        super().__init__()
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.bitrate = bitrate
        self._is_running = True

    def run(self):
        wav_files = [f for f in os.listdir(self.input_dir) if f.endswith('.wav')]
        total_files = len(wav_files)

        # Hitta sökvägen till ffmpeg i den fristående appen
        ffmpeg_path = "ffmpeg"
        if getattr(sys, 'frozen', False):  # Kontrollera om appen körs fristående
            ffmpeg_path = os.path.join(sys._MEIPASS, "ffmpeg")

        # Logga sökvägen till ffmpeg
        print(f"Using ffmpeg at: {ffmpeg_path}")

        # Kör ett enkelt testkommando för att kontrollera om ffmpeg fungerar
        try:
            subprocess.run([ffmpeg_path, "-version"], check=True)
        except Exception as e:
            print(f"Error running ffmpeg: {e}")
            self.stopped.emit()
            return

        for i, wav_file in enumerate(wav_files):
            if not self._is_running:
                self.stopped.emit()
                return

            input_path = os.path.join(self.input_dir, wav_file)
            output_file = os.path.splitext(wav_file)[0] + '.opus'
            output_path = os.path.join(self.output_dir, output_file)

            # Kör ffmpeg med den dynamiska sökvägen
            command = [
                ffmpeg_path, "-i", input_path, "-b:a", f"{self.bitrate}k", output_path
            ]
            try:
                subprocess.run(command, check=True)
            except Exception as e:
                print(f"Error during conversion: {e}")
                self.stopped.emit()
                return

            self.progress.emit(int((i + 1) / total_files * 100))

    def stop(self):
        self._is_running = False


class ConverterApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('WAV to OPUS Converter')
        self.setGeometry(200, 200, 400, 200)

        # Set the background color to dark brown and other widgets to dark gray (night mode style)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #5C4033;  /* Mörkbrun bakgrund för huvudfönstret */
            }
            QPushButton {
                background-color: #2C2C2C;  /* Mörkgrå färg liknande night mode för knappar */
                color: white;               /* Vit text på knappar */
                border: 1px solid #555555;  /* Lägg till en tunn kantlinje för kontrast */
            }
            QLineEdit {
                background-color: #2C2C2C;  /* Mörkgrå färg liknande night mode för inmatningsruta */
                color: white;               /* Vit text i inmatningsfältet */
                border: 1px solid #555555;  /* Lägg till en tunn kantlinje för kontrast */
            }
        """)

        # Layout
        layout = QVBoxLayout()

        # Source folder selection
        self.source_label = QLabel("Välj källmapp:")
        layout.addWidget(self.source_label)

        self.source_button = QPushButton("Bläddra...")
        self.source_button.clicked.connect(self.select_source_folder)
        layout.addWidget(self.source_button)

        # Output folder selection
        self.output_label = QLabel("Välj mål-mapp:")
        layout.addWidget(self.output_label)

        self.output_button = QPushButton("Bläddra...")
        self.output_button.clicked.connect(self.select_output_folder)
        layout.addWidget(self.output_button)

        # Bitrate setting
        self.bitrate_label = QLabel("Bitrate (kbps):")
        layout.addWidget(self.bitrate_label)

        self.bitrate_input = QLineEdit("88")
        layout.addWidget(self.bitrate_input)

        # Start conversion button
        self.convert_button = QPushButton("Starta konvertering")
        self.convert_button.clicked.connect(self.start_conversion)
        layout.addWidget(self.convert_button)

        # Progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # Cancel button
        self.cancel_button = QPushButton("Avbryt")
        self.cancel_button.clicked.connect(self.cancel_conversion)
        layout.addWidget(self.cancel_button)

        # Set main widget
        main_widget = QWidget()
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

        # Initialize paths and conversion thread
        self.input_dir = None
        self.output_dir = None
        self.conversion_thread = None

    def select_source_folder(self):
        self.input_dir = QFileDialog.getExistingDirectory(self, "Välj källmapp")
        self.source_label.setText(f"Källmapp: {self.input_dir}")

    def select_output_folder(self):
        self.output_dir = QFileDialog.getExistingDirectory(self, "Välj mål-mapp")
        self.output_label.setText(f"Mål-mapp: {self.output_dir}")

    def start_conversion(self):
        if self.input_dir and self.output_dir:
            bitrate = self.bitrate_input.text()
            self.conversion_thread = ConversionThread(self.input_dir, self.output_dir, bitrate)
            self.conversion_thread.progress.connect(self.update_progress)
            self.conversion_thread.stopped.connect(self.conversion_stopped)
            self.conversion_thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def cancel_conversion(self):
        if self.conversion_thread:
            self.conversion_thread.stop()

    def conversion_stopped(self):
        self.progress_bar.setValue(0)
        self.source_label.setText("Konvertering stoppad.")


# Main execution
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ConverterApp()
    window.show()
    sys.exit(app.exec_())
