from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton
from PyQt5.QtCore import QTimer, QTime

class ProgressWindow(QDialog):
    """Fönster för att visa vilka ljudfiler/pooler som spelas just nu, uppdateras mjukt."""
    
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aktiva ljud")
        self.resize(400, 300)
        self.setStyleSheet("background-color: #333333; color: white;")

        self.main_window = main_window  # Spara referens till MainWindow
        self.active_slots = {}  # Håller koll på aktiva slots: slot_name -> (label, progress_bar)

        # Layout
        self.layout = QVBoxLayout(self)

        # Titel
        self.title_label = QLabel("Aktiva Slots:")
        self.title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.layout.addWidget(self.title_label)

        # Ny etikett för nedräkning till nästa Slot
        self.next_slot_label = QLabel("Beräknar nästa Slot...")
        self.next_slot_label.setStyleSheet("font-size: 12px; color: #AAAAAA;")
        self.layout.addWidget(self.next_slot_label)


        # Layout för alla aktiva slots
        self.progress_layout = QVBoxLayout()
        self.layout.addLayout(self.progress_layout)

        # Stäng-knapp
        self.close_button = QPushButton("Stäng")
        self.close_button.setStyleSheet("background-color: #555; color: white;")
        self.close_button.clicked.connect(self.close)
        self.layout.addWidget(self.close_button)

        # Timer som uppdaterar varje sekund
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self.update_progress_bars)
        self.progress_timer.start(1000)

        self.update_progress_bars()  # Direkt vid start

    def update_progress_bars(self):
        """Uppdatera progress bars mjukt utan att rensa allt, och visa tid till nästa Slot."""
        current_time = QTime.currentTime()
        still_active = set()
        next_start_times = []  # Samla framtida starttider här

        # Kontrollera att MainWindow har slot_data
        if not hasattr(self.main_window, "slot_data"):
            print("[ERROR] MainWindow saknar 'slot_data'!")
            return

        for slot_name, slot_data in self.main_window.slot_data.items():
            if not isinstance(slot_data, dict):
                continue

            intervals = slot_data.get('intervals', [])
            tracklist = slot_data.get("tracklist", "Ingen")
            pool = slot_data.get("pool", "Ingen")

            for interval in intervals:
                try:
                    interval = interval.replace(">", "-")
                    start_str, end_str = interval.split("-")
                    start_time = QTime.fromString(start_str, "HH:mm:ss")
                    end_time = QTime.fromString(end_str, "HH:mm:ss")
                except ValueError:
                    continue

                # Lägg till framtida starttider
                if start_time > current_time:
                    next_start_times.append(start_time)

                # Om nuvarande tid ligger inom ett intervall
                if start_time <= current_time <= end_time:
                    still_active.add(slot_name)

                    if slot_name not in self.active_slots:
                        # Skapa ny label och progress bar
                        label = QLabel(f"{slot_name}: {tracklist if tracklist != 'Ingen' else pool} ({start_time.toString('HH:mm:ss')} - {end_time.toString('HH:mm:ss')})")
                        label.setStyleSheet("font-size: 12px;")

                        progress_bar = QProgressBar()
                        progress_bar.setStyleSheet("""
                            QProgressBar {
                                border: 2px solid grey;
                                border-radius: 5px;
                                text-align: center;
                                background: #444;
                            }
                            QProgressBar::chunk {
                                background-color: #76c7c0;
                            }
                        """)

                        duration = start_time.secsTo(end_time)
                        elapsed = start_time.secsTo(current_time)

                        progress_bar.setMaximum(duration)
                        progress_bar.setValue(elapsed)

                        self.progress_layout.addWidget(label)
                        self.progress_layout.addWidget(progress_bar)

                        self.active_slots[slot_name] = (label, progress_bar)

                    else:
                        # Uppdatera befintlig progress bar
                        label, progress_bar = self.active_slots[slot_name]
                        duration = start_time.secsTo(end_time)
                        elapsed = start_time.secsTo(current_time)

                        progress_bar.setMaximum(duration)
                        progress_bar.setValue(elapsed)

        # Ta bort inaktiva slots
        slots_to_remove = set(self.active_slots.keys()) - still_active
        for slot_name in slots_to_remove:
            label, progress_bar = self.active_slots.pop(slot_name)
            label.deleteLater()
            progress_bar.deleteLater()

        # Om inga aktiva slots, visa meddelande
        if not self.active_slots:
            if not hasattr(self, 'no_active_label'):
                self.no_active_label = QLabel("Inga aktiva Slots just nu.")
                self.no_active_label.setStyleSheet("color: gray; font-style: italic;")
                self.progress_layout.addWidget(self.no_active_label)
        else:
            if hasattr(self, 'no_active_label'):
                self.no_active_label.deleteLater()
                del self.no_active_label

        # 🔵 Beräkna och visa tid till nästa Slot
        if next_start_times:
            next_start = min(next_start_times)
            seconds_to_next = current_time.secsTo(next_start)

            minutes = seconds_to_next // 60
            seconds = seconds_to_next % 60

            if minutes > 0:
                self.next_slot_label.setText(f"Nästa Slot om {minutes} min {seconds} sek")
            else:
                self.next_slot_label.setText(f"Nästa Slot om {seconds} sekunder")
        else:
            self.next_slot_label.setText("Inga fler byten planerade idag")

