import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QMessageBox
from PyQt5.QtGui import QPixmap
from PIL import Image
import os

class ImageConverter(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()

        self.label = QLabel('Välj en bild att konvertera', self)
        self.layout.addWidget(self.label)

        self.openButton = QPushButton('Öppna bild', self)
        self.openButton.clicked.connect(self.openImage)
        self.layout.addWidget(self.openButton)

        self.convertButton = QPushButton('Konvertera till .icns', self)
        self.convertButton.clicked.connect(self.convertImage)
        self.convertButton.setEnabled(False)  # Disable until image is loaded
        self.layout.addWidget(self.convertButton)

        self.setLayout(self.layout)

    def openImage(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Välj en bildfil", "", "Bildfiler (*.png *.jpg *.jpeg *.pdf)", options=options)
        if fileName:
            self.label.setText(f'Vald fil: {fileName}')
            self.imagePath = fileName
            self.convertButton.setEnabled(True)

    def convertImage(self):
        try:
            # Läs in bilden med PIL
            img = Image.open(self.imagePath)

            # Bestäm output-filnamn och konvertera till .icns
            output_file = QFileDialog.getSaveFileName(self, "Spara som .icns", os.path.splitext(self.imagePath)[0], "Ikonfiler (*.icns)")[0]
            if output_file:
                if not output_file.endswith('.icns'):
                    output_file += '.icns'
                
                # Konvertera och spara till .icns
                img.save(output_file, format='ICNS')

                QMessageBox.information(self, "Framgång", f"Bilden har konverterats till {output_file}")
            else:
                QMessageBox.warning(self, "Avbryt", "Ingen fil sparades.")

        except Exception as e:
            QMessageBox.critical(self, "Fel", f"Det gick inte att konvertera bilden: {str(e)}")

def main():
    app = QApplication(sys.argv)
    converter = ImageConverter()
    converter.setWindowTitle('Bildkonverterare')
    converter.resize(400, 200)
    converter.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
