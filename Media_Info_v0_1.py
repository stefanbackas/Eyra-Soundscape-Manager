import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QWidget, QTextEdit
from pymediainfo import MediaInfo

class MediaInfoApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set window title
        self.setWindowTitle("Media Info Viewer")

        # Set layout
        self.layout = QVBoxLayout()

        # Add a button to open a file dialog
        self.open_button = QPushButton("Open Media File")
        self.open_button.clicked.connect(self.open_file)
        self.layout.addWidget(self.open_button)

        # Add a text box to display media info
        self.info_box = QTextEdit()
        self.info_box.setReadOnly(True)
        self.layout.addWidget(self.info_box)

        # Set up the central widget
        central_widget = QWidget()
        central_widget.setLayout(self.layout)
        self.setCentralWidget(central_widget)

    def open_file(self):
        # Open file dialog to select media file
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Media File", "", "Media Files (*.mp3 *.mp4 *.mkv *.wav *.opus *.flac);;All Files (*)", options=options)
        
        if file_path:
            # Get media info using pymediainfo
            media_info = MediaInfo.parse(file_path)
            media_data = self.extract_media_info(media_info)

            # Display media info in the text box
            self.info_box.setText(media_data)

    def extract_media_info(self, media_info):
        # Extract relevant media info and format it as a string
        media_data = ""
        for track in media_info.tracks:
            media_data += f"Track Type: {track.track_type}\n"
            if track.track_type == "Video":
                media_data += f"Width: {track.width}\n"
                media_data += f"Height: {track.height}\n"
                media_data += f"Frame Rate: {track.frame_rate}\n"
                media_data += f"Duration: {self.convert_to_minutes(track.duration)} minutes\n"
            elif track.track_type == "Audio":
                media_data += f"Channels: {track.channel_s}\n"
                media_data += f"Sampling Rate: {track.sampling_rate} Hz\n"
                media_data += f"Bitrate: {self.convert_to_kilobits(track.bit_rate)} kbps\n"
                media_data += f"Duration: {self.convert_to_minutes(track.duration)} minutes\n"
            elif track.track_type == "General":
                media_data += f"File Size: {self.convert_to_megabytes(track.file_size)} MB\n"
                media_data += f"Overall Bitrate: {self.convert_to_kilobits(track.overall_bit_rate)} kbps\n"
                media_data += f"Duration: {self.convert_to_minutes(track.duration)} minutes\n"
            media_data += "\n"

        return media_data

    def convert_to_megabytes(self, bytes_size):
        # Convert file size from bytes to megabytes (1 MB = 1,000,000 bytes)
        if bytes_size:
            return round(int(bytes_size) / 1_000_000, 2)
        return "N/A"

    def convert_to_kilobits(self, bit_rate):
        # Convert bit rate from bits per second to kilobits per second (1 kbps = 1,000 bps)
        if bit_rate:
            return round(int(bit_rate) / 1_000, 2)
        return "N/A"

    def convert_to_minutes(self, milliseconds):
        # Convert duration from milliseconds to minutes (1 second = 1,000 milliseconds, 1 minute = 60 seconds)
        if milliseconds:
            return round(int(milliseconds) / 60_000, 2)
        return "N/A"

# Main function to run the application
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MediaInfoApp()
    window.show()
    sys.exit(app.exec_())
