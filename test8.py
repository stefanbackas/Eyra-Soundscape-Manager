from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QListWidget, QAbstractItemView
import sys

# Skapa ett testfönster för att verifiera funktionen
class TestTracklistWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Tracklist Reordering")
        self.resize(400, 300)

        # Huvudlayout
        layout = QVBoxLayout(self)

        # Skapa en QListWidget för att simulera fil-listan
        self.file_list_widget = QListWidget()
        self.file_list_widget.addItems(["Track 1", "Track 2", "Track 3", "Track 4"])
        self.file_list_widget.setDragDropMode(QAbstractItemView.InternalMove)  # Aktivera omordning

        # Lägg till list-widgeten i layouten
        layout.addWidget(self.file_list_widget)

# Kör testapplikationen
app = QApplication(sys.argv)
window = TestTracklistWindow()
window.show()
app.exec_()
