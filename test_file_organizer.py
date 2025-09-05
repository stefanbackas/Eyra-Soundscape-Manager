from PyQt5.QtWidgets import QApplication
from FileOrganizerWindow import FileOrganizerWindow

def mock_callback(files):
    print(f"Callback-funktion anropad med filer: {files}")

if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    # Skapa FileOrganizerWindow med mock_callback som callback
    base_folder = "/"
    window = FileOrganizerWindow(base_folder, tracklist_callback=mock_callback)

    # Utskrift av attribut direkt efter skapandet
    print("DEBUG: Attribut i window direkt efter instansiering:")
    for attr, value in window.__dict__.items():
        print(f"  {attr}: {value}")

    # Visa fönstret
    window.show()

    sys.exit(app.exec_())
