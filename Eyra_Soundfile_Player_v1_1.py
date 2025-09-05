import sys
import os
import subprocess
import threading

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QFileDialog, QSlider, QLabel, QGridLayout, QSpacerItem, QSizePolicy
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt, QEvent, QTimer, QMimeData
from PyQt5.QtGui import QPalette, QColor, QDrag
from PyQt5.QtWidgets import QApplication, QListWidget
from PyQt5.QtGui import QClipboard, QKeySequence

import datetime

def log_message(message):
    # Skapa en loggfil på skrivbordet
    log_file_path = os.path.join(os.path.expanduser("~"), "Desktop", "eyra_log.txt")
    with open(log_file_path, "a") as log_file:
        log_entry = f"{datetime.datetime.now()}: {message}\n"
        log_file.write(log_entry)
    print(message)  # Skriv även till terminalen för utveckling
    print(f"Loggad meddelande: {message}")  # Lägg till denna rad för att bekräfta att funktionen anropas



import os

def get_ffmpeg_path():
    if getattr(sys, 'frozen', False):
        # När programmet är paketerat
        app_path = os.path.dirname(os.path.abspath(sys.executable))
        # Vi kliver upp en nivå från `Contents/MacOS` och går till `bin`
        ffplay_path = os.path.join(app_path, '..', 'bin', 'ffplay')
        ffprobe_path = os.path.join(app_path, '..', 'bin', 'ffprobe')
    else:
        # När vi kör i utvecklingsmiljö
        ffplay_path = '/Users/stefanbackas/Documents/000_EYRA/Kod/bin/ffplay'
        ffprobe_path = '/Users/stefanbackas/Documents/000_EYRA/Kod/bin/ffprobe'
    
    log_message(f"ffplay path: {ffplay_path}")
    log_message(f"ffprobe path: {ffprobe_path}")
    return ffplay_path, ffprobe_path





class DraggableListWidget(QListWidget):
    def __init__(self, parent=None):
        super(DraggableListWidget, self).__init__(parent)
        # Aktivera flerval med Cmd (Mac) eller Ctrl (Windows/Linux) och Shift för intervallval
        self.setSelectionMode(QListWidget.ExtendedSelection)

    def startDrag(self, dropActions):
        items = self.selectedItems()  # Hämta alla valda filer
        if items:
            mimeData = QMimeData()
            filenames = "\n".join([item.text() for item in items])  # Skapa en lista med filnamn separerad med ny rad
            mimeData.setText(filenames)
            print(f"startDrag: Drar filer {filenames}")

            drag = QDrag(self)
            drag.setMimeData(mimeData)
            drag.exec_(Qt.MoveAction)

class DropListWidget(QListWidget):
    def __init__(self, parent=None):
        super(DropListWidget, self).__init__(parent)
        self.setAcceptDrops(True)
        self.setSelectionMode(QListWidget.ExtendedSelection)  # Tillåt flerval

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            filenames = event.mimeData().text().split("\n")  # Hämta alla filnamn
            for filename in filenames:
                self.addItem(filename)
            event.acceptProposedAction()

    def keyPressEvent(self, event):
        try:
            # Kontrollera om Cmd+C eller Ctrl+C har tryckts
            if event.matches(QKeySequence.Copy):
                selected_items = self.selectedItems()
                if selected_items:
                    # Samla texten från de valda objekten
                    copied_text = "\n".join([item.text() for item in selected_items])
                    # Kopiera texten till urklipp
                    clipboard = QApplication.clipboard()
                    clipboard.setText(copied_text, QClipboard.Clipboard)
                    print(f"Kopierad text: {copied_text}")
            else:
                super().keyPressEvent(event)
        except Exception as e:
            print(f"Fel vid kopiering: {e}")



class AudioPlayer(QWidget):
    def __init__(self):
        super().__init__()
        log_message("AudioPlayer initieras.") 
        self.setWindowTitle("Eyra Soundfile Player")
        self.lock = threading.Lock()

        self.setGeometry(100, 100, 1000, 600)  # Ökat bredden för tre kolumner

        # Set a dark brown background color for the entire program
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(87, 59, 12))  # Mörkbrun färg
        self.setPalette(palette)

        # Layouts
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # Left column - Drag-and-drop list
        self.left_list = DropListWidget()
        self.left_list.setAcceptDrops(True)
        self.left_list.setDragDropMode(QListWidget.DropOnly)  # Drop only
        self.left_list.setFixedWidth(250)  # Fixa bredden för vänstra kolumnen

        main_layout.addWidget(self.left_list)

        # Middle column - Folder content and controls
        middle_layout = QVBoxLayout()
        self.folder_list = DraggableListWidget()
        middle_layout.addWidget(self.folder_list)
        self.folder_list.setDragEnabled(True)
        self.folder_list.setFixedWidth(250)  # Fixa bredden för mittenkolumnen


        # Button to open folder
        self.open_folder_button = QPushButton("Öppna mapp")
        middle_layout.addWidget(self.open_folder_button)
        self.open_folder_button.clicked.connect(self.open_folder)
        
        # Play button (Pause button removed)
        self.play_button = QPushButton("Play")
        middle_layout.addWidget(self.play_button)
        self.play_button.clicked.connect(self.handle_play_button)

        main_layout.addLayout(middle_layout)

        # Right column - Playback controls for active files
        self.right_layout = QVBoxLayout()

        # Add a spacer at the bottom to always show the right column
        self.right_grid = QGridLayout()  # Grid layout for files and controls
        self.right_layout.addLayout(self.right_grid)

        # Lägg till en dummy-widget som placeholder för att hålla kolumnen synlig även när inga filer finns
        placeholder_label = QLabel()
        self.right_grid.addWidget(placeholder_label, 0, 0, 1, 4)

        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.right_layout.addSpacerItem(spacer)

        self.playback_controls = {}  # Store controls for each file
        self.file_rows = {}  # Keep track of file rows to maintain order

        main_layout.addLayout(self.right_layout)
        
        # Store the file paths and processes for each file
        self.file_paths = {}
        self.file_processes = {}  # Each file gets its own process
        self.selected_filename = None
        
        # Timer for updating sliders
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_sliders)

        # Enable spacebar play/pause function for the middle column
        self.folder_list.itemSelectionChanged.connect(self.on_file_selected)
        
        # Install event filter for keypress events
        self.installEventFilter(self)
        self.setFocusPolicy(Qt.StrongFocus)  # Explicitly set focus policy

        ffplay_path, ffprobe_path = get_ffmpeg_path()  # Hämta både ffplay och ffprobe sökvägar


    # Dra och släpp-funktionerna
    def dragEnterEvent(self, event):
        # Tillåt drag om källan är mittenkolumnen
        if event.source() == self.folder_list:
            event.acceptProposedAction()

    def dropEvent(self, event):
        # Hämta den valda filen från mittenkolumnen och lägg till den i vänsterkolumnen
        selected_item = self.folder_list.currentItem()
        if selected_item:
            filename = selected_item.text()
            # Lägg till endast filnamnet i vänsterkolumnen
            self.left_list.addItem(filename)
        event.acceptProposedAction()

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Öppna mapp", "")
        if folder:
            self.load_folder(folder)

    def load_folder(self, folder):
        self.folder_list.clear()
        self.file_paths.clear()  # Reset file path storage
        # Load supported audio files
        for filename in os.listdir(folder):
            if filename.lower().endswith(('.mp3', '.wav', '.opus')):
                full_path = os.path.join(folder, filename)
                self.file_paths[filename] = full_path  # Store full path by filename
                self.folder_list.addItem(filename)  # Only display the filename

    def on_file_selected(self):
        selected_item = self.folder_list.currentItem()
        if selected_item:
            self.selected_filename = selected_item.text()
            self.play_button.setEnabled(True)  # Enable play button when a file is selected

    def eventFilter(self, source, event):
        if event.type() == QEvent.KeyPress:
            print(f"Tangenttryck: {event.key()}")
            
            # Handle spacebar for play/pause in middle column
            if event.key() == Qt.Key_Space and self.selected_filename:
                print("Spacebar tryckt")
                if self.selected_filename in self.file_processes:
                    self.toggle_play_pause(self.selected_filename)
                else:
                    self.play_audio(self.selected_filename)
                return True  # Prevent default spacebar behavior

            # Handle arrow keys for navigating list
            if event.key() == Qt.Key_Up:
                current_row = self.folder_list.currentRow()
                if current_row > 0:
                    self.folder_list.setCurrentRow(current_row - 1)
                return True  # Prevent default behavior

            if event.key() == Qt.Key_Down:
                current_row = self.folder_list.currentRow()
                if current_row < self.folder_list.count() - 1:
                    self.folder_list.setCurrentRow(current_row + 1)
                return True  # Prevent default behavior

        return super().eventFilter(source, event)

    def handle_play_button(self):
        self.play_audio(self.selected_filename)

    def play_audio(self, filename):
        log_message(f"play_audio anropad med fil: {filename}")  # Lägg till denna rad
        with self.lock:
            ffplay_path, ffprobe_path = get_ffmpeg_path()  # Hämta både ffplay och ffprobe sökvägar
            log_message(f"Använder ffplay från: {ffplay_path}")  # Utskrift här



            file_info = self.file_processes.get(filename, None)

            if file_info and not file_info['paused']:
                log_message(f"Filen {filename} spelas redan.")  # Logga att filen redan spelas
                return  # Om filen redan spelas och inte är pausad, gör inget
            
            file_path = self.file_paths[filename]
            log_message(f"Spelar upp fil från: {file_path}")  # Logga filens sökväg

            duration = self.get_audio_duration(file_path)

            if duration is None:
                log_message(f"Kunde inte hämta längden för fil: {filename}")  # Logga om vi misslyckas med att hämta längden
                return

            start_position = file_info['position'] if file_info and file_info['paused'] else 0
            log_message(f"Spelar upp fil: {filename} från {start_position} sekunder")

            if not os.path.exists(file_path):
                log_message(f"Filen finns inte: {file_path}")
                return


            def play():
                try:
                    # Startar subprocess och spelar upp ljudfilen med ffplay
                    process = subprocess.Popen([ffplay_path, '-nodisp', '-autoexit', '-loglevel', 'quiet', '-ss', str(start_position), file_path],
                                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    self.file_processes[filename]['process'] = process  # Spara subprocessen i process-informationen
                    stdout, stderr = process.communicate()

                    # Logga både stdout och stderr för mer detaljer
                    log_message(f"stdout: {stdout.decode('utf-8')}")
                    log_message(f"stderr: {stderr.decode('utf-8')}")

                    if stderr:
                        log_message(f"Fel vid uppspelning av fil {filename}: {stderr.decode('utf-8')}")

                    # Kontrollera om subprocess körde korrekt
                    if process.returncode == 0:
                        log_message(f"Uppspelningen av {filename} avslutades framgångsrikt.")
                    else:
                        log_message(f"Uppspelningen av {filename} misslyckades med returncode: {process.returncode}")
                except Exception as e:
                    log_message(f"Ett fel inträffade vid uppspelning av fil {filename}: {e}")


            # Spara subprocess-info med ett tomt process-värde tills processen startar
            self.file_processes[filename] = {
                'process': None,  # Subprocess kommer att sparas när den startar
                'duration': duration,
                'position': start_position,
                'paused': False
            }

            # Starta uppspelningen i en separat tråd
            thread = threading.Thread(target=play)
            thread.start()

            log_message(f"Spelar upp fil: {filename} från {start_position} sekunder")  # Logga uppspelning
            # Lägg till kontroller för den här filen i gränssnittet
            self.add_controls_for_file(filename, duration)





    def pause_audio(self, filename):
        with self.lock:

            if filename in self.file_processes:
                process_info = self.file_processes[filename]
                if process_info['process'] is not None:  # Kontrollera att processen existerar
                    process_info['process'].terminate()  # Stop playback
                    log_message(f"Pauserar fil: {filename} vid {process_info['position']} sekunder")

                    process_info['paused'] = True  # Mark the file as paused
                    print(f"Pauserar fil: {filename} vid {process_info['position']} sekunder")
                else:
                    print(f"Ingen aktiv process att pausa för filen {filename}")


    def add_controls_for_file(self, filename, duration):
        # Check if controls already exist for this file
        if filename in self.playback_controls:
            return  # Don't add controls again

        # Determine the row for this file based on the current number of files
        row = len(self.playback_controls)
        
        # Add the filename label, slider, play/pause button, rewind and remove buttons in the same row
        name_label = QLabel(filename)
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(0)
        slider.setMaximum(duration)  # Set maximum to the duration of the file
        play_pause_button = QPushButton("Pause")  # Start as "Pause" since file is playing
        
        # Rewind button
        rewind_button = QPushButton("⟲")
        rewind_button.setFixedSize(20, 20)
        rewind_button.setToolTip("Spela från början")
        
        # Remove button (X)
        remove_button = QPushButton("✖")
        remove_button.setFixedSize(20, 20)
        remove_button.setToolTip("Ta bort fil")
        
        # Add to the grid layout (name above slider and buttons)
        self.right_grid.addWidget(name_label, row * 2, 0, 1, 4)  # Spans across the whole row
        self.right_grid.addWidget(slider, row * 2 + 1, 0)
        self.right_grid.addWidget(play_pause_button, row * 2 + 1, 1)
        self.right_grid.addWidget(rewind_button, row * 2 + 1, 2)
        self.right_grid.addWidget(remove_button, row * 2 + 1, 3)

        # Disable keypresses for these buttons (UI only)
        play_pause_button.setFocusPolicy(Qt.NoFocus)
        rewind_button.setFocusPolicy(Qt.NoFocus)
        remove_button.setFocusPolicy(Qt.NoFocus)
        slider.setFocusPolicy(Qt.NoFocus)

        # Connect button and slider functionality
        play_pause_button.clicked.connect(lambda: self.toggle_play_pause(filename))
        rewind_button.clicked.connect(lambda: self.reset_to_start(filename))
        remove_button.clicked.connect(lambda: self.remove_file(filename))
        slider.sliderReleased.connect(lambda: self.seek_audio(filename, slider.value(), True))

        # Save controls
        self.playback_controls[filename] = {
            'label': name_label,
            'slider': slider,
            'play_pause_button': play_pause_button,
            'rewind_button': rewind_button,
            'remove_button': remove_button
        }

        # Start the timer to update the slider
        self.timer.start(1000)

    def toggle_play_pause(self, filename):
        if filename in self.file_processes and not self.file_processes[filename]['paused']:
            self.pause_audio(filename)
            self.playback_controls[filename]['play_pause_button'].setText("Play")
        else:
            self.play_audio(filename)
            self.playback_controls[filename]['play_pause_button'].setText("Pause")

    def reset_to_start(self, filename):
        # Reset the slider and playback position to the start
        if filename in self.file_processes:
            self.file_processes[filename]['position'] = 0
            self.playback_controls[filename]['slider'].setValue(0)
            print(f"Återställer filen {filename} till början")

    def update_sliders(self):
        # Gå igenom varje fil och uppdatera slidern baserat på dess nuvarande position
        for filename, controls in self.playback_controls.items():
            if filename in self.file_processes:
                process_info = self.file_processes[filename]
                if not process_info['paused']:  # Endast uppdatera om den inte är pausad
                    slider = controls['slider']
                    current_position = process_info['position']
                    slider.setValue(min(current_position + 1, process_info['duration']))  # Uppdatera slidern
                    process_info['position'] += 1  # Öka positionen med 1 sekund

    def get_audio_duration(self, file_path):
        _, ffprobe_path = get_ffmpeg_path()

        try:
            # Kontrollera om ffprobe finns genom att köra subprocess med en enkel version-check
            process = subprocess.Popen([ffprobe_path, '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            log_message(f"ffprobe version output: {stdout.decode('utf-8')}")
            log_message(f"ffprobe error output: {stderr.decode('utf-8')}")

            # Verklig duration-hämtning
            result = subprocess.run([ffprobe_path, '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', file_path],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            duration = float(result.stdout.strip())
            log_message(f"Hämtad längd för {file_path}: {duration} sekunder")
            return int(duration)
        except Exception as e:
            log_message(f"Error getting duration: {e}")
            return None


    def seek_audio(self, filename, position, from_slider):
        with self.lock:
            if filename in self.file_processes:
                try:
                    # Pausa uppspelningen om filen inte är pausad redan
                    if not self.file_processes[filename]['paused']:
                        log_message(f"Pausar fil {filename} automatiskt innan sökning.")
                        self.pause_audio(filename)  # Pausar uppspelningen

                    # Uppdatera position och logga
                    log_message(f"Söker i {filename} till {position} sekunder.")
                    self.file_processes[filename]['position'] = position  # Uppdaterar positionen

                    # Om vi söker från slidern, starta inte om uppspelningen förrän play-knappen trycks
                    if from_slider:
                        log_message(f"Söker från slider i {filename}, filen spelas ej upp.")
                    else:
                        # Återstarta uppspelningen från den nya positionen om sökningen inte är från slider
                        log_message(f"Återupptar uppspelningen av {filename} från {position} sekunder.")
                        self.play_audio(filename)

                except Exception as e:
                    log_message(f"Ett fel inträffade vid sökning i {filename}: {e}")


    
    def remove_file(self, filename):
        # Ta bort fil från playback_controls och file_processes
        if filename in self.playback_controls:
            controls = self.playback_controls[filename]
            controls['label'].deleteLater()
            controls['slider'].deleteLater()
            controls['play_pause_button'].deleteLater()
            controls['rewind_button'].deleteLater()
            controls['remove_button'].deleteLater()
            del self.playback_controls[filename]
            log_message(f"Fil {filename} borttagen från listan.")

        if filename in self.file_processes:
            self.file_processes[filename]['process'].terminate()
            del self.file_processes[filename]

        print(f"Fil {filename} borttagen från listan.")

    def update_sliders(self):
        with self.lock:
            # Update sliders for each playing file based on its playback time
            for filename, controls in self.playback_controls.items():
                if filename in self.file_processes:
                    process_info = self.file_processes[filename]
                    if not process_info['paused']:  # Only update if not paused
                        slider = controls['slider']
                        current_position = process_info['position']
                        slider.setValue(min(current_position + 1, process_info['duration']))  # Update slider based on time passed
                        process_info['position'] += 1  # Increment position by 1 second

    def get_audio_duration(self, file_path):
        _, ffprobe_path = get_ffmpeg_path()  # Hämta ffprobe sökvägen

        try:
            result = subprocess.run([ffprobe_path, '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', file_path],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            duration = float(result.stdout.strip())
            return int(duration)
        except Exception as e:
            print(f"Error getting duration: {e}")
            return None

if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = AudioPlayer()
    player.show()
    sys.exit(app.exec_())
