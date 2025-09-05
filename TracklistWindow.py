global_test_callback = lambda files: print(f"[TEST CALLBACK] Filer mottagna: {files}")
from PyQt5.QtCore import pyqtSignal


class TracklistWindow(QWidget):
    """Fönster för enskild tracklist med filer och inställningar."""
    closed = pyqtSignal(str)  # Signal som skickar tracklistens namn vid stängning

    def __init__(self, tracklist_name, tracklist_data, on_save, main_window=None):
        super().__init__()  # Lägg till för att stödja MainWindow
        self.setWindowTitle(f"Tracklist: {tracklist_name}")
        self.resize(500, 650)

        # Ställ in en grundläggande stil för fönstret
        self.setStyleSheet("background-color: #5C4033;")

        self.history = []


        print(f"[DEBUG] Tilldelar tracklist_data: {tracklist_data}")
        self.tracklist_name = tracklist_name
        self.tracklist_data = tracklist_data
        self.on_save = on_save
        self.main_window = main_window  # Spara referensen till MainWindow


        self.setFocusPolicy(Qt.StrongFocus)

        # Layout
        main_layout = QHBoxLayout(self)
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()
        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)

        # Vänster sektion (lista med filer)
        self.file_list = QListWidget()
        self.file_list.setStyleSheet("""
            background-color: dark grey;
            color: white;
        """)
        self.file_list.setAcceptDrops(True)
        self.file_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.file_list.dragEnterEvent = self.dragEnterEvent
        self.file_list.dropEvent = self.dropEvent
        left_layout.addWidget(self.file_list)

        self.add_button = QPushButton("Lägg till Fil(er)")
        #self.add_button.setStyleSheet("background-color: #A67B5B; color: white;")
        self.add_button.clicked.connect(self.add_files)
        right_layout.addWidget(self.add_button)

        self.remove_button = QPushButton("Ta bort Fil(er)")
        #self.remove_button.setStyleSheet("background-color: #A67B5B; color: white;")
        self.remove_button.clicked.connect(self.remove_file)
        right_layout.addWidget(self.remove_button)

        # Höger: Klistra in filer från text
        self.paste_files_textedit = QTextEdit()
        self.paste_files_textedit.setPlaceholderText("Klistra in en lista på filer här")
        self.paste_files_textedit.setStyleSheet("""
            background-color: dark grey;
            color: white;
        """)
        right_layout.addWidget(self.paste_files_textedit)


        paste_files_button = QPushButton("Lägg till filer från inklistrad text")
        #paste_files_button.setStyleSheet("background-color: #A67B5B; color: white;")
        paste_files_button.clicked.connect(self.paste_files)
        right_layout.addWidget(paste_files_button)

        # Höger: Sortera filer
        sort_files_button = QPushButton("Sortera filer alfabetiskt")
        #sort_files_button.setStyleSheet("background-color: #A67B5B; color: white;")
        sort_files_button.clicked.connect(self.sort_files)
        right_layout.addWidget(sort_files_button)

        # Höger: Ändra filformat
        self.format_combo = QComboBox()
        self.format_combo.addItems([".mp3", ".opus"])
        self.format_combo.setStyleSheet("""
            QComboBox {
                background-color: dark grey;
                color: white;
            }
            QComboBox QAbstractItemView {
                background-color: dark grey;
                color: white;
                selection-background-color: darkgray;  /* För valda objekt */
                selection-color: white;
            }
        """)
        right_layout.addWidget(self.format_combo)



        change_format_button = QPushButton("Ändra alla filer till valt format")
        change_format_button.clicked.connect(self.change_file_format)
        right_layout.addWidget(change_format_button)

        # Knapp för att ta bort dubbletter
        self.remove_duplicates_button = QPushButton("Rensa dubbletter")
        #self.remove_duplicates_button.setStyleSheet("background-color: #A67B5B; color: white;")
        self.remove_duplicates_button.clicked.connect(self.remove_duplicates)
        right_layout.addWidget(self.remove_duplicates_button)



        # Höger: Inställningar
        settings_layout = QFormLayout()

        self.fadetime_input = QSpinBox()
        self.fadetime_input.setRange(0, 100)
        self.fadetime_input.setStyleSheet("""
            background-color: dark grey;
            color: white;
            border: 1px solid gray;
        """)
        settings_layout.addRow("Fadetime (sek):", self.fadetime_input)

        self.slotfadetime_input = QSpinBox()
        self.slotfadetime_input.setRange(0, 100)
        self.slotfadetime_input.setStyleSheet("""
            background-color: dark grey;
            color: white;
            border: 1px solid gray;
        """)
        settings_layout.addRow("Slot Fadetime:", self.slotfadetime_input)


        # Volyminställningar
        volume_layout = QVBoxLayout()
        slider_layout = QVBoxLayout()  # Ändra till vertikal layout för att få texten ovanför slidern
        input_layout = QHBoxLayout()  # Layout för Volume Input och dess etikett

        # Hämta sparat volymvärde eller använd standard
        saved_volume = self.tracklist_data.get('volume', 0.1)  # JSON-format (0.00–0.15)

        # Skapa och konfigurera volymslider
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 150)
        self.volume_slider.setValue(int(saved_volume * 1000))  # Konvertera JSON-värdet till sliderns skala
        self.volume_slider.valueChanged.connect(self.update_volume_label)

        # Lägg till etikett för Tracklist Volume ovanför slidern
        slider_label = QLabel("Tracklist Volume:")
        slider_label.setAlignment(Qt.AlignCenter)

        # Lägg till volymslider i layouten
        slider_layout.addWidget(slider_label)
        slider_layout.addWidget(self.volume_slider)

        # Skapa och konfigurera värdeetikett för slidern
        self.volume_value_label = QLabel(str(int(saved_volume * 1000)))  # För att visa värdet
        self.volume_value_label.setFixedWidth(40)
        self.volume_value_label.setAlignment(Qt.AlignCenter)

        # Skapa och konfigurera textrutan för volyminmatning
        input_label = QLabel("Volume Input:")
        self.volume_input = QLineEdit()
        self.volume_input.setValidator(QIntValidator(0, 150))
        self.volume_input.setText(str(int(saved_volume * 1000)))
        self.volume_input.setStyleSheet("""
            background-color: black;
            color: white;
            border: 1px solid gray;
        """)
        self.volume_input.returnPressed.connect(self.update_volume_from_input)

        # Lägg till Volume Input och dess etikett i layouten
        input_layout.addWidget(input_label)
        input_layout.addWidget(self.volume_input)

        # Lägg till allting i huvudvolymlayouten
        volume_layout.addLayout(slider_layout)  # Slidern och dess etikett
        volume_layout.addLayout(input_layout)  # Volume Input och dess etikett
        right_layout.addLayout(volume_layout)


        # Knapp för att sätta volymen som originalvolym
        self.set_original_button = QPushButton("Sätt denna volym som original")
        self.set_original_button.clicked.connect(self.set_as_original_volume)
        right_layout.addWidget(self.set_original_button)


        self.loop_checkbox = QCheckBox("Loop")
        settings_layout.addRow(self.loop_checkbox)

        self.randomize_checkbox = QCheckBox("Randomize")
        settings_layout.addRow(self.randomize_checkbox)

        

        

        right_layout.addLayout(settings_layout)

        self.undo_button = QPushButton("Ångra")
        #self.undo_button.setStyleSheet("background-color: #A67B5B; color: white;")
        self.undo_button.clicked.connect(self.undo)
        right_layout.addWidget(self.undo_button)


        
        # Metadata-knapp
        self.metadata_button = QPushButton("Öppna Metadatafönster")
        self.metadata_button.setStyleSheet("background-color: #556B2F; color: white;")
        self.metadata_button.clicked.connect(self.open_metadata_window)
        right_layout.addWidget(self.metadata_button)

        # Knapp för att öppna File Organizer
        self.file_organizer_button = QPushButton("Open File Organizer")
        self.file_organizer_button.setStyleSheet("background-color: #556B2F; color: white;")
        self.file_organizer_button.clicked.connect(self.open_file_organizer)
        right_layout.addWidget(self.file_organizer_button)

        # Höger: Spara och stäng
        save_button = QPushButton("Spara och Stäng")
        save_button.setStyleSheet("background-color: #109090; color: white;")
        save_button.clicked.connect(self.save_and_close)
        right_layout.addWidget(save_button)

        # Ladda tidigare inställningar och filer
        self.load_files()
        self.load_settings()


    def load_files(self):
        """Ladda filer från tracklist_data."""
        for file_name in self.tracklist_data.get('files', []):
            item = QListWidgetItem(file_name)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.file_list.addItem(item)

    def load_settings(self):
        """Ladda tidigare sparade inställningar."""
        self.fadetime_input.setValue(self.tracklist_data.get('fadetime', 0))
        self.slotfadetime_input.setValue(self.tracklist_data.get('slotfadetime', 0))

        # Använd senaste justerade volymen från gruppen
        volume = self.tracklist_data.get('volume', 0.1)
        self.volume_slider.setValue(int(volume * 1000))  # Konvertera till sliderns skala
        self.volume_input.setText(str(int(volume * 1000)))

        self.loop_checkbox.setChecked(self.tracklist_data.get('loop', False))
        self.randomize_checkbox.setChecked(self.tracklist_data.get('randomize', False))




    def add_files(self):
        """Lägg till filer via filväljare."""
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Välj filer", "", "Ljudfiler (*.mp3 *.wav *.opus)")
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            item = QListWidgetItem(file_name)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.file_list.addItem(item)

    def remove_file(self):
        """Ta bort markerade filer."""
        if self.file_list.selectedItems():
            self.save_history()  # Spara historik innan ändringar
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))


    def paste_files(self):
        """Klistra in filer från text."""
        pasted_text = self.paste_files_textedit.toPlainText().strip()
        if pasted_text:  # Kontrollera att det finns text att klistra in
            self.save_history()  # Spara historik innan ändringar
        for line in pasted_text.split('\n'):
            file_path = line.strip()
            file_name = os.path.basename(file_path)  # Extrahera endast filnamnet
            item = QListWidgetItem(file_name)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.file_list.addItem(item)
        self.paste_files_textedit.clear()



    def sort_files(self):
        """Sortera filer alfabetiskt."""
        if self.file_list.count() > 0:  # Kontrollera om det finns filer att sortera
            self.save_history()  # Spara historik innan ändringar
        items = [self.file_list.item(i).text() for i in range(self.file_list.count())]
        items.sort()
        self.file_list.clear()
        for file_name in items:
            item = QListWidgetItem(file_name)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.file_list.addItem(item)


    def change_file_format(self):
        """Ändra formatet på alla filer."""
        if self.file_list.count() > 0:  # Kontrollera om det finns filer att ändra
            self.save_history()  # Spara historik innan ändringar
        selected_format = self.format_combo.currentText()
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            file_name = item.text()
            name, _ = os.path.splitext(file_name)
            item.setText(f"{name}{selected_format}")


    def update_volume_label(self, value):
        """Uppdatera volymetiketten."""
        self.volume_value_label.setText(str(value))
        self.volume_input.setText(str(value))

    def update_volume_from_input(self):
        """Uppdatera slidern från textinmatning."""
        value = int(self.volume_input.text())
        self.volume_slider.setValue(value)    

    def dragEnterEvent(self, event):
        """Aktivera drag och släpp."""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """Hantera släppta filer."""
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            file_name = os.path.basename(file_path)
            if file_name.lower().endswith(('.mp3', '.wav', '.opus')):
                item = QListWidgetItem(file_name)
                item.setFlags(item.flags() | Qt.ItemIsEditable)
                self.file_list.addItem(item)

    

    def save_and_close(self):
        """Spara och stäng fönstret."""
        # Uppdatera Tracklist-data
        self.tracklist_data['files'] = [self.file_list.item(i).text() for i in range(self.file_list.count())]
        self.tracklist_data['fadetime'] = self.fadetime_input.value()
        self.tracklist_data['slotfadetime'] = self.slotfadetime_input.value()
        self.tracklist_data['volume'] = self.volume_slider.value() / 1000
        self.tracklist_data['loop'] = self.loop_checkbox.isChecked()
        self.tracklist_data['randomize'] = self.randomize_checkbox.isChecked()

        group_name = self.tracklist_data.get('primary_group')
        if group_name and group_name in self.main_window.group_data:
            self.main_window.group_data[group_name]['tracklists_data'][self.tracklist_name]['volume'] = self.tracklist_data['volume']

        self.on_save()
        self.close()





    def keyPressEvent(self, event):
        focused_widget = QApplication.focusWidget()
        print(f"Widget med tangentfokus: {focused_widget}")

        """Hantera tangenttryckningar."""
        if event.key() == Qt.Key_Up:  # Om upp-piltangenten trycks
            current_row = self.file_list.currentRow()
            if current_row > 0:  # Flytta upp om det inte är den första raden
                self.file_list.setCurrentRow(current_row - 1)
        elif event.key() == Qt.Key_Down:  # Om ner-piltangenten trycks
            current_row = self.file_list.currentRow()
            if current_row < self.file_list.count() - 1:  # Flytta ner om det inte är den sista raden
                self.file_list.setCurrentRow(current_row + 1)
        elif event.matches(QKeySequence.Copy):  # Cmd+C / Ctrl+C
            self.copy_selected_files()
        elif event.key() == Qt.Key_Space:  # Om mellanslag trycks
            self.play_selected_file()
        elif event.key() == Qt.Key_Delete or (event.modifiers() == Qt.MetaModifier and event.key() == Qt.Key_Backspace):
            self.delete_selected_tracklists()

    def delete_selected_tracklists(self):
        """Radera markerade Tracklists."""
        selected_items = self.tracklist_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Inget markerat", "Välj minst en Tracklist att radera.")
            return

        reply = QMessageBox.question(
            self,
            "Bekräfta borttagning",
            f"Är du säker på att du vill radera {len(selected_items)} Tracklist(s)?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            for item in selected_items:
                tracklist_name = item.text()
                self.tracklist_list.takeItem(self.tracklist_list.row(item))  # Ta bort från listan
                if tracklist_name in self.tracklist_data:  # Ta bort från datan
                    del self.tracklist_data[tracklist_name]

            print(f"Raderade Tracklists: {[item.text() for item in selected_items]}")        

    def copy_selected_files(self):
        """Kopiera markerade filer."""
        selected_items = self.file_list.selectedItems()
        if selected_items:
            copied_text = "\n".join(item.text() for item in selected_items)
            QApplication.clipboard().setText(copied_text)
            print(f"Kopierade filer: {copied_text}")

    def play_selected_file(self):
        """Spela upp den valda filen från den fördefinierade mappen."""
        selected_item = self.file_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Ingen fil vald", "Välj en fil för att spela upp.")
            return

        file_name = selected_item.text()
        predefined_folder = '/Users/stefanbackas/Documents/000_EYRA/Eyra Soundscapes/ALL EYRA TRACKS MP3'
        file_path = os.path.join(predefined_folder, file_name)

        if not os.path.exists(file_path):
            QMessageBox.warning(self, "Filen hittades inte", f"Filen '{file_name}' kunde inte hittas i:\n{predefined_folder}")
            return

        try:
            # Öppna filen med Finder på macOS
            subprocess.run(["open", file_path], check=True)
            print(f"Spelar upp: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Fel", f"Kunde inte spela upp filen.\nFel: {e}")
        

    def open_metadata_window(self):
        """Öppna metadatafönstret och lägg till filtrerade resultat."""
        try:
            # Hämta metadata från Google Sheets
            metadata = fetch_metadata("B2:M")
            if metadata is None or metadata.empty:
                QMessageBox.warning(self, "No Data", "No metadata available.")
                return

            # Definiera tidsperioder
            time_periods = {
                "Morning": ("06:00", "11:00"),
                "Day": ("11:00", "16:00"),
                "Afternoon": ("16:00", "18:00"),
                "Evening": ("18:00", "22:00"),
                "Night": ("22:00", "06:00"),
            }

            # Öppna MetadataFilterWindow med metadata och tidsperioder
            dialog = MetadataFilterWindow(metadata, time_periods)
            if dialog.exec_():  # Visa fönstret och vänta på input
                filtered_results = dialog.get_filtered_results()
                if filtered_results:
                    self.add_filtered_files(filtered_results)

        except Exception as e:
            print(f"Could not open metadata window: {e}")




    def open_time_settings_window(self):
        """Öppna tidsinställningsfönstret."""
        try:
            # Standardtidsperioder
            default_time_periods = {
                "Morning": ("06:00", "11:00"),
                "Day": ("11:00", "16:00"),
                "Afternoon": ("16:00", "18:00"),
                "Evening": ("18:00", "22:00"),
                "Night": ("22:00", "06:00"),
            }

            # Skapa tidsinställningsfönster
            time_window = TimeSettingsWindow(default_time_periods)
            if time_window.exec_() == QDialog.Accepted:
                new_time_periods = time_window.get_time_periods()  # Hämta ändrade tidsperioder
                # Vi sparar de uppdaterade tidsperioderna i MetadataFilterWindow
                MetadataFilterWindow.time_periods = new_time_periods
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open time settings window: {e}")


    def add_filtered_files(self, filtered_files):
        """Lägg till filtrerade filer till tracklistens lista utan att rensa bort befintliga filer."""
        if filtered_files:  # Kontrollera att det finns filer att lägga till
            self.save_history()  # Spara historik innan ändringar
        current_files = {self.file_list.item(i).text() for i in range(self.file_list.count())}
        new_files = set(filtered_files) - current_files  # Lägg bara till nya filer

        for file_name in sorted(new_files):  # Lägg till i alfabetisk ordning
            item = QListWidgetItem(file_name)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.file_list.addItem(item)


       


    def add_advanced_filter_results(self, filtered_files):
        """Lägg till filtrerade filer från Advanced Filters till file_list."""
        if not filtered_files:
            QMessageBox.information(self, "No Files", "Inga filer matchade filtren.")
            return

        self.file_list.clear()  # Rensa nuvarande filer
        for file_name in filtered_files:
            item = QListWidgetItem(file_name)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.file_list.addItem(item)

        # print(f"Advanced filter results added: {filtered_files}")  # Debug


        # Lägg till varje filtrerad fil till listan
        self.file_list.clear()
        for file_name in filtered_files:
            item = QListWidgetItem(file_name)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.file_list.addItem(item)
       

    
    def debug_callback_wrapper(self, files):
        """Logga och vidarebefordra filer till add_files_to_tracklist."""
        print(f"debug_callback_wrapper anropad med filer: {files}")
        self.add_files_to_tracklist(files)
    
    

    
    def open_file_organizer(self):
        try:
            base_folder = QDir.homePath()
            print("[DEBUG] Öppnar FileOrganizerWindow med korrekt callback")
            self.file_organizer = FileOrganizerWindow(base_folder, tracklist_callback=self.add_files_to_tracklist)
            print(f"[DEBUG] Instans-ID för FileOrganizerWindow: {id(self.file_organizer)}")
            self.file_organizer.exec_()
        except Exception as e:
            print(f"[ERROR] Exception i open_file_organizer: {e}")




    def add_files(self):
        """Lägg till filer via filväljare."""
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Välj filer", "", "Ljudfiler (*.mp3 *.wav *.opus)")
        if file_paths:
            self.save_history()  # Spara historik innan ändringar
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            item = QListWidgetItem(file_name)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.file_list.addItem(item)


    def add_files_to_tracklist(self, files):
        print(f"[DEBUG] add_files_to_tracklist anropad med filer: {files}")
        if not files:
            QMessageBox.warning(self, "Inga filer valda", "Inga filer har valts i File Organizer.")
            return
        if files:  # Kontrollera att det finns filer att lägga till
            self.save_history()  # Spara historik innan ändringar
        for file_name in files:
            item = QListWidgetItem(file_name)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.file_list.addItem(item)
            print(f"Lagt till fil: {file_name}")

        QMessageBox.information(self, "Filer tillagda", f"Lade till {len(files)} filer.")



    def adjust_volume_from_group(self, group_volume):
        """Justera volymen baserat på Gruppvolymen."""
        group_name = self.tracklist_data.get('primary_group')
        if group_name and group_name in self.main_window.group_data:
            original_volume = self.main_window.group_data[group_name]['tracklists_data'][self.tracklist_name]['original_volume']
        else:
            original_volume = self.tracklist_data.get('original_volume', 0.1)
        
        adjusted_volume = round(original_volume * group_volume, 3)
        self.volume_slider.setValue(int(adjusted_volume * 1000))
        self.volume_input.setText(str(int(adjusted_volume * 1000)))

        print(f"[DEBUG] Tracklist '{self.tracklist_name}' original volym: {original_volume}")
        print(f"[DEBUG] Tracklist '{self.tracklist_name}' justerad volym (från Gruppvolym): {adjusted_volume}")



    def set_as_original_volume(self):
        """Sätt aktuell volym som originalvolym."""
        if self.main_window:  # Kontrollera att huvudfönstret finns
            current_volume = self.volume_slider.value() / 1000  # Volym från slidern
            primary_group = self.tracklist_data.get('primary_group')  # Hämta huvudgruppen
            if primary_group:
                group_data = self.main_window.group_data.get(primary_group)
                if group_data and self.tracklist_name in group_data.get('tracklists', []):
                    group_data['tracklists_data'][self.tracklist_name]['original_volume'] = current_volume
                    print(f"[DEBUG] Originalvolym för Tracklist '{self.tracklist_name}' uppdaterad till: {current_volume}")
                    QMessageBox.information(
                        self, "Originalvolym Uppdaterad",
                        f"Originalvolym för '{self.tracklist_name}' har uppdaterats till {current_volume}."
                    )
                    return
            QMessageBox.warning(
                self, "Ingen Huvudgrupp",
                f"Tracklisten '{self.tracklist_name}' är inte tilldelad en huvudgrupp."
            )
        else:
            QMessageBox.critical(self, "Fel", "Huvudfönstret kunde inte hittas. Originalvolym uppdaterades inte.")

            

    def closeEvent(self, event):
        """Meddela MainWindow när fönstret stängs."""
        self.closed.emit(self.tracklist_name)  # Skicka tracklistens namn
        super().closeEvent(event)        

    def remove_duplicates(self):
        """Tar bort dubbletter från vänstra fönstret."""
        if self.file_list.count() > 0:  # Kontrollera att det finns filer i listan
            self.save_history()  # Spara historik innan ändringar

        # Hämta alla objekt i fil-listan
        items = [self.file_list.item(i).text() for i in range(self.file_list.count())]
        # Skapa en unik lista
        unique_items = list(set(items))
        # Rensa listan och lägg tillbaka unika objekt
        self.file_list.clear()
        self.file_list.addItems(unique_items)


    def save_history(self):
        """Spara nuvarande tillstånd i historiken."""
        items = [self.file_list.item(i).text() for i in range(self.file_list.count())]
        self.history.append(items)
        
    def undo(self):
        """Ångrar senaste ändring."""
        if self.history:  # Kontrollera om historiken innehåller data
            last_state = self.history.pop()  # Ta bort och hämta senaste tillståndet
            self.file_list.clear()  # Rensa listan
            self.file_list.addItems(last_state)  # Återställ till senaste tillståndet
        else:
            QMessageBox.information(self, "Ångra", "Inga ändringar att ångra.")
        

