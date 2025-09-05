from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QHBoxLayout, QFormLayout
from PyQt5.QtCore import pyqtSignal


class MetadataFilterWindow(QDialog):
    """Metadata filter window."""
    def __init__(self, metadata, time_periods):
        super().__init__()
        self.metadata = metadata
        self.time_periods = time_periods
        self.selected_filters = {}
        self.filtered_results = []

        # Tidsperioder i HH:MM-format
        self.time_periods = {
            "Morning": ("06:00", "11:00"),
            "Day": ("11:00", "16:00"),
            "Afternoon": ("16:00", "18:00"),
            "Evening": ("18:00", "22:00"),
            "Night": ("22:00", "06:00")
        }

        self.setWindowTitle("Filter Metadata")
        self.resize(600, 500)

        # Anropa init_ui för att sätta upp layout och widgets
        self.init_ui()

    def init_ui(self):
        """Initiera användargränssnittet."""
        layout = QVBoxLayout()

        # GridLayout för filtermenyer
        filters_layout = QGridLayout()

        # Lägg till dropdowns för metadata-filter i ett rutnät
        self.filters = {}
        row, col = 0, 0
        for column in self.metadata.columns:
            if column not in ["File Name", "Time Start", "Time Stop"]:
                dropdown = QComboBox()
                dropdown.addItems(["All"] + sorted(self.metadata[column].dropna().unique()))
                
                label = QLabel(f"Filter by {column}:")
                filters_layout.addWidget(label, row, col)  # Lägg till etikett
                filters_layout.addWidget(dropdown, row + 1, col)  # Lägg till dropdown
                self.filters[column] = dropdown

                # Gå till nästa kolumn, eller rad om två kolumner är fyllda
                col += 1
                if col > 1:  # Max två kolumner
                    col = 0
                    row += 2

        layout.addLayout(filters_layout)

        # Time period dropdown
        self.period_dropdown = QComboBox()
        self.period_dropdown.addItems(["All"] + list(self.time_periods.keys()))
        layout.addWidget(QLabel("Filter by Time Period:"))
        layout.addWidget(self.period_dropdown)

        # Knapp för att applicera filter
        apply_button = QPushButton("Apply Filters")
        apply_button.clicked.connect(self.apply_filters)
        layout.addWidget(apply_button)

        # Knapp för att definiera tidsperioder
        time_periods_button = QPushButton("Define Time Periods")
        time_periods_button.clicked.connect(self.open_time_settings)
        layout.addWidget(time_periods_button)

        # Knapp för avancerade filter
        advanced_filters_button = QPushButton("Advanced Filters")
        advanced_filters_button.clicked.connect(self.open_advanced_filters)
        layout.addWidget(advanced_filters_button)

        self.setLayout(layout)




    def apply_filters(self):
        """Hämta valda avancerade filter."""
        selected_filters = {}
        for column, dropdown in self.filters.items():
            selected_value = dropdown.currentText()
            if selected_value != "All":
                selected_filters[column] = selected_value

        self.selected_filters = selected_filters
        self.accept()

    def get_selected_filters(self):
        """Returnera valda filter."""
        return self.selected_filters


    def apply_filters(self):
        """Använd valda filter för att filtrera metadata."""
        filtered_metadata = self.metadata.copy()

        # Filtrera baserat på valda dropdown-menyer
        for filter_name, dropdown in self.filters.items():
            selected_value = dropdown.currentText()
            if selected_value != "All":
                filtered_metadata = filtered_metadata[filtered_metadata[filter_name] == selected_value]

        # Filtrera baserat på vald tidsperiod
        selected_period = self.period_dropdown.currentText()
        if selected_period != "All":
            filtered_metadata = filter_by_time_period(filtered_metadata, selected_period, self.time_periods)

        # Spara filtrerade resultat
        self.filtered_results = filtered_metadata["File Name"].tolist()
        self.accept()


    
    #def open_advanced_filters(self):
    #    """Öppna fönster för avancerade filter."""
    #    advanced_metadata = fetch_advanced_metadata()  # Hämta avancerad metadata
    #    if advanced_metadata is not None:
    #        dialog = AdvancedFilterWindow(advanced_metadata)
    #        if dialog.exec_():  # Om användaren klickar på Apply
    #            selected_filters = dialog.get_selected_filters()  # Hämta filtrerade resultat
    #            if selected_filters:
    #                # Sätt resultaten i TracklistWindow
    #                self.file_list_widget.clear()  # Töm nuvarande lista
    #                self.file_list_widget.addItems(selected_filters)  # Lägg till nya filer
    #                print("Filtered files added to TracklistWindow.")  # Debug
    #            else:
    #                print("No files matched the filters.")  # Debug
    




    def open_time_settings(self):
        """Open time settings window."""
        time_window = TimeSettingsWindow(self.time_periods)
        if time_window.exec_() == QDialog.Accepted:
            self.time_periods.update(time_window.get_time_periods())

    def get_filtered_results(self):
        """Return the filtered results."""
        return self.filtered_results
    
    def is_time_in_period(self, time_str, period_name):
        """
        Kontrollera om en given tid ligger inom en specificerad tidsperiod.
        :param time_str: Sträng i formatet HH:MM (exempel: "07:30").
        :param period_name: Namnet på tidsperioden (exempel: "Morning").
        :return: True om tiden ligger inom perioden, annars False.
        """
        try:
            # Konvertera tider till datetime-objekt
            time_to_check = datetime.strptime(time_str, "%H:%M")
            start_time_str, end_time_str = self.time_periods[period_name]
            start_time = datetime.strptime(start_time_str, "%H:%M")
            end_time = datetime.strptime(end_time_str, "%H:%M")

            # Hantera om perioden går över midnatt
            if start_time <= end_time:
                return start_time <= time_to_check < end_time
            else:
                return time_to_check >= start_time or time_to_check < end_time
        except Exception as e:
            print(f"Fel vid kontroll av tid: {e}")
            return False 

        



from PyQt5.QtCore import QTime

class TimeSettingsWindow(QDialog):
    def __init__(self, time_periods):
        super().__init__()
        self.setWindowTitle("Define Time Periods")
        self.time_periods = time_periods
        self.updated_periods = {}
        self.init_ui()

    def init_ui(self):
        """Skapa gränssnittet för att definiera tidsperioder."""
        layout = QVBoxLayout()
        self.time_inputs = {}

        for period, (start_time, end_time) in self.time_periods.items():
            period_layout = QHBoxLayout()
            period_label = QLabel(f"{period}:")
            start_input = QTimeEdit()
            end_input = QTimeEdit()

            # Sätt standardvärden för tidsperioder
            start_input.setTime(QTime.fromString(start_time, "HH:mm"))
            end_input.setTime(QTime.fromString(end_time, "HH:mm"))

            # Spara referenser till inputs för senare användning
            self.time_inputs[period] = (start_input, end_input)

            # Lägg till widgets i layouten
            period_layout.addWidget(period_label)
            period_layout.addWidget(QLabel("Start:"))
            period_layout.addWidget(start_input)
            period_layout.addWidget(QLabel("End:"))
            period_layout.addWidget(end_input)
            layout.addLayout(period_layout)

        # Lägg till OK och Avbryt-knappar
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)

        ok_button.clicked.connect(self.save_and_close)
        cancel_button.clicked.connect(self.reject)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def save_and_close(self):
        """Spara ändringar och stäng fönstret."""
        for period, (start_input, end_input) in self.time_inputs.items():
            start_time = start_input.time().toString("HH:mm")
            end_time = end_input.time().toString("HH:mm")
            self.updated_periods[period] = (start_time, end_time)
        self.accept()

    def get_time_periods(self):
        """Returnera de uppdaterade tidsperioderna."""
        return self.updated_periods

class AdvancedFilterWindow(QDialog):
    """Fönster för att hantera avancerade filter."""

    def __init__(self, metadata):
        super().__init__()
        self.metadata = metadata
        self.filters = {}
        self.filtered_results = []

        print("Initializing Advanced Filter Window...")  # Debug
        print(f"Metadata columns passed: {self.metadata.columns}")  # Debug

        self.setWindowTitle("Advanced Filters")
        self.resize(800, 600)  # Öka storleken på Advanced-fönstret
        self.init_ui()

    def init_ui(self):
        """Skapa UI för Advanced Filter-fönstret."""
        print("Building Advanced Filter UI...")  # Debug

        # Skapa huvudlayout
        main_layout = QVBoxLayout()

        # Skapa en QScrollArea för att lägga till scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # Gör så att layouten anpassar sig till fönsterstorleken

        # Skapa en widget och layout för scrollområdet
        scroll_widget = QWidget()
        layout = QGridLayout(scroll_widget)  # Använd QGridLayout för att organisera elementen i ett rutnät

        # Rubrik
        layout.addWidget(QLabel("Advanced Filters"), 0, 0, 1, 3)

        # Dropdowns för avancerade kolumner
        advanced_columns = self.metadata.columns[13:]  # Kolumner N till BM
        print(f"Advanced Columns to filter: {advanced_columns}")  # Debug

        if advanced_columns.empty:
            print("No advanced columns found. Aborting initialization.")  # Debug
            QMessageBox.warning(self, "Error", "No advanced metadata available.")
            return

        column_count = 3  # Antal kolumner i rutnätet
        row = 1
        col = 0

        for column in advanced_columns:
            print(f"Adding filter for column: {column}")  # Debug
            label = QLabel(f"Filter by {column}:")
            dropdown = QComboBox()
            dropdown.addItems(["All"] + sorted(self.metadata[column].dropna().unique()))
            self.filters[column] = dropdown

            layout.addWidget(label, row, col)
            layout.addWidget(dropdown, row + 1, col)

            col += 1
            if col >= column_count:  # Byt rad efter angivet antal kolumner
                col = 0
                row += 2

        # Lägg till Apply-knappen längst ner
        apply_button = QPushButton("Apply Advanced Filters")
        apply_button.clicked.connect(self.apply_advanced_filters)
        layout.addWidget(apply_button, row + 1, 0, 1, column_count)

        # Ställ in layouten för scroll-widgeten
        scroll_widget.setLayout(layout)
        scroll_area.setWidget(scroll_widget)

        # Lägg scroll_area till huvudlayouten
        main_layout.addWidget(scroll_area)

        self.setLayout(main_layout)
        print("Advanced Filter UI built successfully with scroll.")  # Debug


    def apply_advanced_filters(self):
        """Använd avancerade filter för att filtrera metadata."""
        filtered_metadata = self.metadata.copy()  # Skapa en kopia av metadata för filtrering

        # Filtrera baserat på val i dropdown-menyer
        for filter_name, dropdown in self.filters.items():
            selected_value = dropdown.currentText()
            print(f"Filtering by {filter_name}: {selected_value}")  # Debug
            if selected_value != "All":  # Hoppa över 'All'
                filtered_metadata = filtered_metadata[filtered_metadata[filter_name] == selected_value]

        # Kontrollera om några resultat finns
        if filtered_metadata.empty:
            print("No results match the selected filters.")  # Debug
            self.filtered_results = []  # Töm listan om inget matchar
        else:
            # Hämta endast 'File Name' för de matchade raderna
            if "File Name" in filtered_metadata.columns:
                self.filtered_results = filtered_metadata["File Name"].tolist()
                print("Filtered Results:", self.filtered_results)  # Debug-utskrift
            else:
                print("'File Name' column is missing in the filtered data.")  # Debug
                self.filtered_results = []  # Säkerställ att ingen lista skickas om data saknas

        self.accept()  # Stäng dialogrutan


    def get_selected_filters(self):
        """Hämta filtrerade resultat."""
        return self.filtered_results  # Returnera resultatlistan


