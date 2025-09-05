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

def log_message(message):
    print(message)


def get_ffmpeg_path():
    if getattr(sys, 'frozen', False):
        # Om programmet körs som en paketerad app
        app_path = os.path.dirname(sys.executable)
        ffplay_path = os.path.join(app_path, 'bin', 'ffplay')
        ffprobe_path = os.path.join(app_path, 'bin', 'ffprobe')
    else:
        # Om programmet körs från terminalen (under utveckling)
        ffplay_path = '/Users/stefanbackas/Documents/000_EYRA/Kod/bin/ffplay'
        ffprobe_path = '/Users/stefanbackas/Documents/000_EYRA/Kod/bin/ffprobe'

    log_message(f"Sökväg till ffplay: {ffplay_path}")  # Logga sökvägen
    log_message(f"Sökväg till ffprobe: {ffprobe_path}")  # Logga sökvägen    
    
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
        with self.lock:

            ffplay_path, _ = get_ffmpeg_path()  # Hämta ffplay sökvägen
            print(f"Använder ffplay från: {ffplay_path}")  # Temporär utskrift

            file_info = self.file_processes.get(filename, None)

            if file_info and not file_info['paused']:
                return  # If the file is already playing and not paused, do nothing
            
            file_path = self.file_paths[filename]
            print(f"Spelar upp fil från: {file_path}")  # Temporär utskrift

            duration = self.get_audio_duration(file_path)

            if duration is None:
                print(f"Kunde inte hämta längden för fil: {filename}")
                return

            start_position = file_info['position'] if file_info and file_info['paused'] else 0
            log_message(f"Spelar upp fil: {filename} från {start_position} sekunder")

            def play():
                try:
                    process = subprocess.Popen([ffplay_path, '-nodisp', '-autoexit', '-loglevel', 'quiet', '-ss', str(start_position), file_path],
                                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    self.file_processes[filename]['process'] = process  # Spara subprocessen i process-informationen
                    stdout, stderr = process.communicate()

                    if stderr:
                        print(f"Fel vid uppspelning av fil {filename}: {stderr.decode('utf-8')}")
                except Exception as e:
                    print(f"Ett fel inträffade vid uppspelning av fil {filename}: {e}")
            
            # Spara subprocess-info med ett tomt process-värde tills processen startar
            self.file_processes[filename] = {
                'process': None,
                'duration': duration,
                'position': start_position,
                'paused': False
            }

            # Starta uppspelningen i en separat tråd
            thread = threading.Thread(target=play)
            thread.start()

            print(f"Spelar upp fil: {filename} från {start_position} sekunder")  # Temporär utskrift

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
        ffplay_path, ffprobe_path = get_ffmpeg_path()  # Hämta sökvägarna

        try:
            result = subprocess.run([ffprobe_path, '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', file_path],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            duration = float(result.stdout.strip())
            return int(duration)
        except Exception as e:
            print(f"Error getting duration: {e}")
            return None
                
    def seek_audio(self, filename, position, from_slider):
        with self.lock:
            if filename in self.file_processes:
                try:
                    # Stäng den nuvarande processen innan vi söker
                    if self.file_processes[filename]['process'] is not None:
                        self.file_processes[filename]['process'].terminate()
                        self.file_processes[filename]['process'].wait()  # Vänta på att processen avslutas

                    file_path = self.file_paths[filename]
                    print(f"Söker i {filename} till {position} sekunder.")

                    if from_slider and self.file_processes[filename]['paused']:
                        self.file_processes[filename]['position'] = position
                        print(f"Söker i fil: {filename} till {position} sekunder men spelar ej.")
                    else:
                        # Starta om uppspelningen från den nya positionen
                        process = subprocess.Popen(['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet', '-ss', str(position), file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                        # Uppdatera processinformationen
                        self.file_processes[filename] = {
                            'process': process,
                            'duration': self.file_processes[filename]['duration'],
                            'position': position,
                            'paused': False
                        }
                        print(f"Söker i {filename} till {position} sekunder och spelar.")
                except Exception as e:
                    print(f"Ett fel inträffade vid sökning i {filename}: {e}")
    
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

def seek_audio(self, filename, position, from_slider):
    with self.lock:
        if filename in self.file_processes:
            try:
                # Försök att alltid stänga den nuvarande processen innan vi söker
                if self.file_processes[filename]['process'] is not None:
                    self.file_processes[filename]['process'].terminate()
                    self.file_processes[filename]['process'].wait()  # Vänta på att processen avslutas helt

                # Logga innan vi söker
                log_message(f"Söker i {filename} till {position} sekunder.")

                # Om slidern flyttas, sök men spela inte upp om pausat
                if from_slider and self.file_processes[filename]['paused']:
                    self.file_processes[filename]['position'] = position
                    print(f"Söker i fil: {filename} till {position} sekunder men spelar ej.")
                else:
                    # Starta om uppspelningen från den nya positionen
                    file_path = self.file_paths[filename]
                    process = subprocess.Popen(['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet', '-ss', str(position), file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                    # Logga och uppdatera processinformation
                    log_message(f"Söker i {filename} till {position} sekunder och spelar.")
                    self.file_processes[filename] = {
                        'process': process,
                        'duration': self.file_processes[filename]['duration'],
                        'position': position,
                        'paused': False
                    }
                    print(f"Söker i {filename} till {position} sekunder och spelar.")
            except Exception as e:
                print(f"Ett fel inträffade vid uppspelning av {filename}: {e}")



    def remove_file(self, filename):
        # Remove file from playback_controls and file_processes
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
