import sys
import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt
import simpleaudio as sa
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QHBoxLayout
from PyQt6.QtCore import Qt

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtCore import Qt
from pydub import AudioSegment
from pydub.playback import play
import subprocess

class SoundEditor(QMainWindow):
    def __init__(self):
        super().__init__()

        self.audio_file_path = None  # Definiera variabeln från start
        self.audio_data = None
        self.sr = None
        self.play_obj = None
        self.playback_position = 0  # Startposition i ljudet
        self.is_playing = False

        self.setWindowTitle("Eyra Sound Editor")
        self.setGeometry(100, 100, 800, 500)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.load_button = QPushButton("Ladda Ljudfil")
        self.load_button.clicked.connect(self.load_audio)
        self.layout.addWidget(self.load_button)

        self.figure, self.ax = plt.subplots(figsize=(8, 3))
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)
        self.canvas.mpl_connect("button_press_event", self.on_waveform_click)

        self.button_layout = QHBoxLayout()
        self.layout.addLayout(self.button_layout)

        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.play_audio)
        self.button_layout.addWidget(self.play_button)

        self.pause_button = QPushButton("Paus")
        self.pause_button.clicked.connect(self.pause_audio)
        self.button_layout.addWidget(self.pause_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_audio)
        self.button_layout.addWidget(self.stop_button)

        self.rewind_button = QPushButton("⏪ Till början")
        self.rewind_button.clicked.connect(self.rewind_audio)
        self.button_layout.addWidget(self.rewind_button)

        self.forward_button = QPushButton("⏩ Till slutet")
        self.forward_button.clicked.connect(self.forward_audio)
        self.button_layout.addWidget(self.forward_button)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # Tillåter keyPressEvent att fungera


        self.audio_data = None
        self.sr = None
        self.play_obj = None
        self.playback_position = 0  # Startposition i ljudet
        self.is_playing = False

    def load_audio(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Välj en ljudfil", "", "Ljudfiler (*.wav *.mp3 *.flac)")
        
        if file_path:
            print(f"Laddar ljudfil: {file_path}")  # Debug
            self.audio_file_path = file_path  # Spara sökvägen till ljudfilen
            print(f"Fil laddad och sökväg sparad: {self.audio_file_path}")  # Debug
            self.audio_data, self.sr = librosa.load(file_path, sr=None)
            self.plot_waveform()
            self.playback_position = 0
        else:
            print("❌ Ingen fil valdes.")  # Debug om användaren stänger dialogen


    def play_audio(self):
        print(f"🟢 Försöker spela upp. audio_file_path: {self.audio_file_path}")  # Debug
        
        if self.audio_file_path is None:
            print("❌ Ingen ljudfil laddad! Kan inte spela upp.")  # Debug
            return

        if self.audio_data is not None:
            self.is_playing = True
            audio_wave = (self.audio_data * 32767).astype(np.int16)  # Konvertera till 16-bit PCM
            self.play_obj = sa.play_buffer(audio_wave, 1, 2, self.sr)  # Spela upp ljudet






    def plot_waveform(self):
        self.ax.clear()
        self.ax.plot(np.linspace(0, len(self.audio_data) / self.sr, num=len(self.audio_data)), self.audio_data)
        self.ax.set_xlabel("Tid (sekunder)")
        self.ax.set_ylabel("Amplitude")
        self.ax.set_title("Ljudvåg")
        self.canvas.draw()

    


    def pause_audio(self):
        if self.is_playing and self.play_obj is not None:
            self.play_obj.stop()
            self.is_playing = False

    def stop_audio(self):
        if self.play_obj is not None:
            self.play_obj.stop()
            self.playback_position = 0
            self.is_playing = False

    def rewind_audio(self):
        self.playback_position = 0
        self.play_audio()

    def forward_audio(self):
        self.playback_position = len(self.audio_data) / self.sr
        self.play_audio()

    def on_waveform_click(self, event):
        if event.xdata is not None and self.audio_data is not None:
            self.playback_position = event.xdata
            self.play_audio()

    def on_waveform_click(self, event):
        if event.xdata is not None and self.audio_data is not None:
            self.playback_position = int(event.xdata * self.sr)  # Omvandla tid till samplingsindex
            self.play_audio()
        

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            if self.is_playing:
                self.pause_audio()
            else:
                self.play_audio()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SoundEditor()
    window.show()
    sys.exit(app.exec())
