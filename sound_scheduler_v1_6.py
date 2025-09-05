import sys
import random
import logging
import os

from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QTextEdit, QSlider, QSpinBox, QGridLayout, QMessageBox, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor, QPixmap

# Global variabler för schemagenerering
schedule = {}
ratio_factor = 1.0  # Standardvärde för ratio-faktor
is_generating = False  # För att undvika flera samtidiga genereringar

from PyQt5.QtCore import QThread, pyqtSignal

# Skapa en ny trådklass för schemagenerering
class GenerateThread(QThread):
    # Signal för att uppdatera schematext i huvudtråden
    schedule_generated = pyqtSignal(str, str)

    def __init__(self, start_time_str, end_time_str, min_play, max_play, min_pause, max_pause, pool_count, ratio_factor):
        super().__init__()
        self.start_time_str = start_time_str
        self.end_time_str = end_time_str
        self.min_play = min_play
        self.max_play = max_play
        self.min_pause = min_pause
        self.max_pause = max_pause
        self.pool_count = pool_count
        self.ratio_factor = ratio_factor

    def run(self):
        # Här görs schemagenereringen (samma logik som i generate-metoden tidigare)
        schedule = {pool: [] for pool in range(self.pool_count)}
        start_time = datetime.strptime(self.start_time_str, "%H:%M")
        end_time = datetime.strptime(self.end_time_str, "%H:%M")
        current_time = start_time
        
        while current_time < end_time:
            for pool in range(self.pool_count):
                play_duration = random.randint(self.min_play, self.max_play)
                play_time = timedelta(minutes=play_duration)
                
                if current_time + play_time > end_time:
                    break

                end_play_time = current_time + play_time
                pause_duration = random.randint(self.min_pause, self.max_pause)
                adjusted_pause_duration = int(pause_duration * self.ratio_factor)
                pause_time = timedelta(minutes=adjusted_pause_duration)

                schedule[pool].append({
                    "start_time": current_time,
                    "end_time": end_play_time,
                    "play_duration": play_duration,
                    "pause_duration": adjusted_pause_duration
                })

                current_time += play_time + pause_time
                if current_time >= end_time:
                    break
        
        # Formatera och skicka signaler till huvudtråden för att uppdatera UI
        schedule_output = self.print_schedule(schedule)
        combined_output = self.print_combined_schedule_with_pauses(schedule)
        self.schedule_generated.emit(schedule_output, combined_output)

    def print_schedule(self, schedule):
        output = ""
        for pool, times in schedule.items():
            output += f"Pool {pool + 1}:\n"
            for t in times:
                output += f"{t['start_time'].strftime('%H:%M:%S')}-{t['end_time'].strftime('%H:%M:%S')}\n"
            output += "\n"
        return output

    def print_combined_schedule_with_pauses(self, schedule):
        intervals = []
        for pool, times in schedule.items():
            for t in times:
                intervals.append((t['start_time'], t['end_time'], t['play_duration'], t['pause_duration']))
        intervals.sort(key=lambda x: x[0])
        combined_output = ""
        for i, (start, end, play_duration, pause_duration) in enumerate(intervals):
            combined_output += f"{start.strftime('%H:%M')}-{end.strftime('%H:%M')} ({play_duration} min)"
            if i < len(intervals) - 1:
                combined_output += f" | Paus: {pause_duration} min\n"
            else:
                combined_output += "\n"
        return combined_output


class SchedulerApp(QWidget):
    def __init__(self, send_schedule_callback=None):
        """
        Schemageneratorns huvudfönster.
        :param send_schedule_callback: Callback-funktion för att skicka schema till SlotWindow.
        """
        super().__init__()

        # Callback för att skicka schema till SlotWindow
        self.send_schedule_callback = send_schedule_callback

        # Logging
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scheduler.log')
        logging.basicConfig(filename=log_path, level=logging.DEBUG,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        print(f"Loggar sparas till: {log_path}")

        # Initiera UI
        self.init_ui()

    def init_ui(self):
        # Layout för schemageneratorn
        self.setWindowTitle('Ljudpool Schemagenerator')
        self.setGeometry(300, 300, 700, 600)  # Fönstret är 50% högre

        from PyQt5.QtGui import QIcon  # Lägg till detta i toppen av din fil, om det inte redan finns

        # Inuti init_ui-metoden:
        self.setWindowIcon(QIcon("/Users/stefanbackas/Documents/000_EYRA/Kod/Sound_and_Time_Icon.icns"))

        # Sätt en mörkbrun bakgrund
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(92, 64, 51))  # Mörkbrun färg
        self.setPalette(palette)

        main_layout = QHBoxLayout()  # Huvudlayout, två kolumner med lika bredd

        # Vänstra kolumnen
        left_layout = QVBoxLayout()

        # Textfält för att visa schema
        self.text_output = QTextEdit(self)
        self.text_output.setReadOnly(True)

        # Textfält för att visa kombinerat schema med paustider
        self.combined_output_text = QTextEdit(self)
        self.combined_output_text.setReadOnly(True)

        left_layout.addWidget(QLabel("Genererat schema:"))
        left_layout.addWidget(self.text_output)

        left_layout.addWidget(QLabel("Sammanlagt schema med pauser:"))
        left_layout.addWidget(self.combined_output_text)

        # Högra kolumnen
        right_layout = QVBoxLayout()

        # Lägg till en knapp för att skicka schema till SlotWindow
        self.send_button = QPushButton("Skicka schema till SlotWindow")
        self.send_button.clicked.connect(self.send_schedule_to_slotwindow)
        right_layout.addWidget(self.send_button)


        # GridLayout för att placera textetiketter till vänster och inmatningsrutor till höger
        grid_layout = QGridLayout()

        self.label_start_time = QLabel("Starttid (HH:MM):")
        self.entry_start_time = QLineEdit()
        self.entry_start_time.setText("07:00")  # Default starttid

        self.label_end_time = QLabel("Sluttid (HH:MM):")
        self.entry_end_time = QLineEdit()
        self.entry_end_time.setText("23:00")  # Default sluttid

        self.label_min_play = QLabel("Minsta spellängd (min):")
        self.entry_min_play = QLineEdit()
        self.entry_min_play.setText("10")  # Default minsta spellängd

        self.label_max_play = QLabel("Största spellängd (min):")
        self.entry_max_play = QLineEdit()
        self.entry_max_play.setText("20")  # Default största spellängd

        self.label_min_pause = QLabel("Minsta paustid (min):")
        self.entry_min_pause = QLineEdit()
        self.entry_min_pause.setText("10")  # Default minsta paustid

        self.label_max_pause = QLabel("Största paustid (min):")
        self.entry_max_pause = QLineEdit()
        self.entry_max_pause.setText("20")  # Default största paustid

        self.label_pool_count = QLabel("Antal ljudpooler:")
        self.entry_pool_count = QLineEdit()
        self.entry_pool_count.setText("1")  # Default antal ljudpooler

        # Lägg till alla textetiketter och inmatningsrutor i GridLayout
        grid_layout.addWidget(self.label_start_time, 0, 0)
        grid_layout.addWidget(self.entry_start_time, 0, 1)

        grid_layout.addWidget(self.label_end_time, 1, 0)
        grid_layout.addWidget(self.entry_end_time, 1, 1)

        grid_layout.addWidget(self.label_min_play, 2, 0)
        grid_layout.addWidget(self.entry_min_play, 2, 1)

        grid_layout.addWidget(self.label_max_play, 3, 0)
        grid_layout.addWidget(self.entry_max_play, 3, 1)

        grid_layout.addWidget(self.label_min_pause, 4, 0)
        grid_layout.addWidget(self.entry_min_pause, 4, 1)

        grid_layout.addWidget(self.label_max_pause, 5, 0)
        grid_layout.addWidget(self.entry_max_pause, 5, 1)

        grid_layout.addWidget(self.label_pool_count, 6, 0)
        grid_layout.addWidget(self.entry_pool_count, 6, 1)

        right_layout.addLayout(grid_layout)

        # Fader och knappar placerade tätt ihop som en vertikal sekvens
        self.label_ratio = QLabel("Justera förhållandet mellan ljud och tystnad:")
        right_layout.addWidget(self.label_ratio)

        self.scale_ratio = QSlider(Qt.Horizontal)
        self.scale_ratio.setMinimum(50)
        self.scale_ratio.setMaximum(150)
        self.scale_ratio.setValue(100)
        self.scale_ratio.valueChanged.connect(self.update_ratio_factor)
        right_layout.addWidget(self.scale_ratio)

        self.ratio_value_display = QSpinBox()
        self.ratio_value_display.setRange(50, 150)
        self.ratio_value_display.setValue(100)
        self.ratio_value_display.valueChanged.connect(self.update_slider_from_spinbox)
        right_layout.addWidget(self.ratio_value_display)

        # Knappar under fadern, i samma layout
        self.button_generate = QPushButton("Generera schema", self)
        self.button_generate.clicked.connect(self.generate)
        right_layout.addWidget(self.button_generate)

        self.button_clear = QPushButton("Töm", self)
        self.button_clear.clicked.connect(self.clear_fields)
        right_layout.addWidget(self.button_clear)

        self.exit_button = QPushButton("Avsluta schemagenerator")
        self.exit_button.setStyleSheet("background-color: #B22222; color: white;")
        self.exit_button.clicked.connect(self.close)
        right_layout.addWidget(self.exit_button)


        # Spacer för att fylla upp tomrum innan loggan längst ner
        right_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Lägga till logotypen och centrera den
        self.logo_label = QLabel(self)
        pixmap = QPixmap("Eyra Logo Leaf Text Large Green-White-Transp.png")  # Ladda bilden
        self.logo_label.setPixmap(pixmap)

        # Ställ in storlek på loggan så den passar rutan utan att ändra fönstrets storlek
        self.logo_label.setFixedSize(150, 150)  # Anpassa storleken här
        self.logo_label.setScaledContents(True)  # Skalera innehållet till att passa labeln

        # Skapa en layout för att centrera logotypen
        logo_layout = QVBoxLayout()
        logo_layout.addStretch()  # Spacer för att centrera vertikalt
        logo_layout.addWidget(self.logo_label, alignment=Qt.AlignCenter)  # Centrera logotypen
        logo_layout.addStretch()  # Spacer för att centrera vertikalt

        right_layout.addLayout(logo_layout)  # Lägg till layouten till höger-layouten


        # Lägg till båda kolumnerna i huvudlayouten
        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)

        self.setLayout(main_layout)

    def generate_random_time(self, min_time, max_time):
        return random.randint(min_time, max_time)

    # Minska antalet loggningar i schemagenereringen
    def generate(self):
        print("Genererar schema...")
        # Läs in alla nödvändiga indata från UI-komponenterna
        start_time_str = self.entry_start_time.text()
        end_time_str = self.entry_end_time.text()
        min_play = int(self.entry_min_play.text())
        max_play = int(self.entry_max_play.text())
        min_pause = int(self.entry_min_pause.text())
        max_pause = int(self.entry_max_pause.text())
        pool_count = int(self.entry_pool_count.text())
        
        # Skapa och starta tråden
        self.thread = GenerateThread(start_time_str, end_time_str, min_play, max_play, min_pause, max_pause, pool_count, ratio_factor)
        
        # Koppla signalen från tråden till metoden som uppdaterar UI
        self.thread.schedule_generated.connect(self.update_schedule_output)
        
        self.thread.start()
        print("Schemagenerering startad.")

    def update_schedule_output(self, schedule_output, combined_output):
        # Uppdatera UI-komponenter med resultat från schemagenereringen
        self.text_output.setText(schedule_output)
        self.combined_output_text.setText(combined_output)    

    def update_ratio_factor(self, value):
        global ratio_factor
        ratio_factor = float(value) / 100  # Uppdatera endast ratio-faktorn
        self.ratio_value_display.setValue(value)

    def update_slider_from_spinbox(self, value):
        self.scale_ratio.setValue(value)

    

    def clear_fields(self):
        self.entry_start_time.clear()
        self.entry_end_time.clear()
        self.entry_min_play.clear()
        self.entry_max_play.clear()
        self.entry_min_pause.clear()
        self.entry_max_pause.clear()
        self.entry_pool_count.clear()
        self.text_output.clear()
        self.combined_output_text.clear()

    # Inuti SchedulerApp
    def send_schedule_to_slotwindow(self):
        """Skicka det genererade schemat till SlotWindow."""
        if self.send_schedule_callback:
            generated_schedule = self.text_output.toPlainText()  # Rätt textkälla
            print(f"[DEBUG] Skickar följande till SlotWindow: {generated_schedule}")
            self.send_schedule_callback(generated_schedule)
            QMessageBox.information(self, "Schema skickat", "Schemat har skickats till SlotWindow.")
        else:
            print("[DEBUG] Ingen callback kopplad till SchedulerApp")



    # def get_combined_schedule(self):
    #     """Returnera schematext från 'combined_output_text'."""
    #     return self.combined_output_text.toPlainText()
    
    # def get_generated_schedule(self):
    #     """Returnera schematext från 'text_output'."""
    #     return self.text_output.toPlainText()


    

    
    

# Kör applikationen
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SchedulerApp()
    ex.show()
    sys.exit(app.exec_())
