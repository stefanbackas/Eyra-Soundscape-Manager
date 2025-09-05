from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QHBoxLayout, QFormLayout, QGridLayout, QCheckBox, QMessageBox
)
from PyQt5.QtCore import pyqtSignal
import logging    


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
        layout = QVBoxLayout()

        # Skapa en grid layout för filtren
        filter_layout = QGridLayout()

        # Dropdowns för metadatafilter
        self.filters = {}
        self.exclusion_checkboxes = {}  # För att hålla exkluderingsstatus
        row, col = 0, 0
        for column in self.metadata.columns:
            if column not in ["File Name", "Time Start", "Time Stop"]:
                dropdown = QComboBox()
                dropdown.addItems(["All"] + sorted(self.metadata[column].dropna().unique()))

                # Lägg till etikett och dropdown i gridlayout
                filter_layout.addWidget(QLabel(f"Filter by {column}:"), row, col)
                filter_layout.addWidget(dropdown, row, col + 1)

                # Lägg till en checkbox för exkludering
                exclusion_checkbox = QCheckBox("Exkludera")
                filter_layout.addWidget(exclusion_checkbox, row, col + 2)

                col += 3
                if col >= 6:  # Max 2 filter per rad (justera vid behov)
                    col = 0
                    row += 1

                self.filters[column] = dropdown
                self.exclusion_checkboxes[column] = exclusion_checkbox

        # Lägg till filter-layout i huvudlayouten
        layout.addLayout(filter_layout)

        # Time period dropdown
        self.period_dropdown = QComboBox()
        self.period_dropdown.addItems(["All"] + list(self.time_periods.keys()))
        layout.addWidget(QLabel("Filter by Time Period:"))
        layout.addWidget(self.period_dropdown)

        # Knappar
        apply_button = QPushButton("Apply Filters")
        apply_button.clicked.connect(self.apply_filters)
        layout.addWidget(apply_button)

        time_periods_button = QPushButton("Define Time Periods")
        time_periods_button.clicked.connect(self.open_time_settings)
        layout.addWidget(time_periods_button)

        # Knapp för att öppna AdvancedFilterWindow
        advanced_filters_button = QPushButton("Open Advanced Filters")
        advanced_filters_button.clicked.connect(self.open_advanced_filters)
        layout.addWidget(advanced_filters_button)

        self.setLayout(layout)

    def apply_filters(self):
        """Filtrera och exkludera filer baserat på valda filter."""
        if not isinstance(self.metadata, pd.DataFrame) or self.metadata.empty:
            QMessageBox.warning(self, "Error", "Metadata är inte korrekt inläst.")
            return

        print("[DEBUG] Metadata i början av apply_filters:")
        print(self.metadata)

        file_name_column = next(
            (col for col in self.metadata.columns if col.strip().lower() == "file name"),
            None
        )
        if file_name_column is None:
            QMessageBox.warning(self, "Error", "'File Name' saknas i metadata.")
            return

        filtered_metadata = self.metadata.copy()

        # Förbered data: Rensa strängar och konvertera NaN till None
        filtered_metadata = filtered_metadata.applymap(
            lambda x: x.strip() if isinstance(x, str) else x
        )

        # **Steg 1: Inkludera filer**
        for filter_name, dropdown in self.filters.items():
            selected_value = dropdown.currentText()
            if selected_value != "All":
                if filter_name not in filtered_metadata.columns:
                    QMessageBox.warning(self, "Error", f"Kolumn '{filter_name}' saknas i metadata.")
                    return
                filtered_metadata = filtered_metadata[
                    filtered_metadata[filter_name].fillna("").str.casefold() == selected_value.casefold()
                ]
                print(f"[DEBUG] Efter inkludering för {filter_name} - {selected_value}: {len(filtered_metadata)} rader kvar")

        if filtered_metadata.empty:
            QMessageBox.warning(self, "No Results", "Inga rader matchade de valda filtren.")
            self.filtered_results = []
            return

        print("[DEBUG] Metadata innan exkludering:")
        print(filtered_metadata)

        # **Steg 2: Exkludera filer**
        for filter_name, dropdown in self.filters.items():
            selected_value = dropdown.currentText()
            is_exclusion = self.exclusion_checkboxes[filter_name].isChecked()
            if is_exclusion:
                if filter_name not in filtered_metadata.columns:
                    QMessageBox.warning(self, "Error", f"Kolumn '{filter_name}' saknas i metadata.")
                    return

                rows_before = len(filtered_metadata)

                if selected_value == "All":
                    # Exkludera alla rader med något värde i kolumnen
                    filtered_metadata = filtered_metadata[
                        filtered_metadata[filter_name].isnull()
                    ]
                else:
                    # Exkludera rader med exakt valt värde
                    filtered_metadata = filtered_metadata[
                        filtered_metadata[filter_name].fillna("").str.casefold() != selected_value.casefold()
                    ]

                rows_after = len(filtered_metadata)
                print(f"[DEBUG] Exkluderade {rows_before - rows_after} rader för {filter_name} - {selected_value}")

        if filtered_metadata.empty:
            QMessageBox.warning(self, "No Results", "Inga rader kvar efter exkluderingen.")
            self.filtered_results = []
            return

        print("[DEBUG] Slutgiltiga resultat:")
        print(filtered_metadata)

        # Spara resultat
        self.filtered_results = filtered_metadata[file_name_column].tolist()

        QMessageBox.information(
            self, "Filtrering klar",
            f"Totalt {len(self.filtered_results)} filer matchade de valda kriterierna."
        )

        self.accept()

































    def open_advanced_filters(self):
        """Öppna fönstret för avancerade filter."""
        try:
            # Skicka den metadata som redan är laddad och referensen till TracklistWindow
            dialog = AdvancedFilterWindow(self.metadata, self.parent())
            if dialog.exec_():  # Vänta på användarens input
                filtered_results = dialog.get_selected_filters()
                if filtered_results:
                    self.filtered_results = filtered_results
                    QMessageBox.information(self, "Filter Applied", f"{len(filtered_results)} filer matchade filtren.")
                else:
                    QMessageBox.information(self, "No Results", "Inga resultat hittades för avancerade filter.")
        except Exception as e:
            print(f"Error opening AdvancedFilterWindow: {e}")



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
        
    def get_selected_filters(self):
        """Hämta filtrerade resultat."""
        return self.filtered_results  # Returnera resultatlistan    

        










import os
import json
from PyQt5.QtCore import QTime
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTimeEdit, QPushButton

class TimeSettingsWindow(QDialog):
    SETTINGS_FILE = "time_settings.json"  # Fil för att spara och läsa tider

    def __init__(self, default_time_periods):
        super().__init__()
        self.setWindowTitle("Define Time Periods")

        self.setStyleSheet("""
            QMainWindow { background-color: #5C4033; }  /* Mörkbrun bakgrundsfärg för huvudfönstret */
            """)
        
        self.default_time_periods = default_time_periods
        self.time_periods = self.load_saved_periods() or self.default_time_periods
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

            # Sätt start- och sluttider
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

        # Lägg till Default Times-knappen
        default_button = QPushButton("Default Times")
        default_button.clicked.connect(self.reset_to_default_times)
        layout.addWidget(default_button)

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
        """Spara ändringar till fil och stäng fönstret."""
        for period, (start_input, end_input) in self.time_inputs.items():
            start_time = start_input.time().toString("HH:mm")
            end_time = end_input.time().toString("HH:mm")
            self.updated_periods[period] = (start_time, end_time)

        self.save_periods_to_file(self.updated_periods)
        self.accept()

    def get_time_periods(self):
        """Returnera de uppdaterade tidsperioderna."""
        return self.updated_periods

    def reset_to_default_times(self):
        """Återställ alla tidsperioder till standardvärden."""
        for period, (start_input, end_input) in self.time_inputs.items():
            start_time, end_time = self.default_time_periods[period]
            start_input.setTime(QTime.fromString(start_time, "HH:mm"))
            end_input.setTime(QTime.fromString(end_time, "HH:mm"))

    def save_periods_to_file(self, periods):
        """Spara tidsperioder till en JSON-fil."""
        try:
            with open(self.SETTINGS_FILE, "w") as file:
                json.dump(periods, file, indent=4)
            print("Tidsperioder sparade.")
        except Exception as e:
            print(f"Fel vid sparning av tidsperioder: {e}")

    def load_saved_periods(self):
        """Läs sparade tidsperioder från en JSON-fil."""
        if os.path.exists(self.SETTINGS_FILE):
            try:
                with open(self.SETTINGS_FILE, "r") as file:
                    return json.load(file)
            except Exception as e:
                print(f"Fel vid läsning av tidsperioder: {e}")
        return None






















from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QCheckBox, QGridLayout, QMessageBox
)
import pandas as pd

class AdvancedFilterWindow(QDialog):
    """Advanced filter window for extended metadata options."""
    def __init__(self, metadata, base_filters=None):
        super().__init__()

        self.metadata = metadata
        self.base_filters = base_filters if base_filters else {}
        self.filtered_results = []

        self.setWindowTitle("Advanced Filters")
        self.resize(700, 600)
        
        # Normalize metadata columns for consistent comparisons
        self.metadata.columns = [col.strip().lower() for col in self.metadata.columns]

        # Debugging: Validate column mappings
        print("[DEBUG] All metadata columns:", self.metadata.columns.tolist())
        
        # Column mapping
        self.column_mapping = {
            "english": "english",  # Map "English" to actual column name "english"
            "latin": "latin",  # Map "Latin" to actual column name "latin"
            "swedish": "swedish"  # Map "Swedish" to actual column name "swedish"
        }

        missing_columns = []
        for label, column_key in self.column_mapping.items():
            if column_key not in self.metadata.columns:
                print(f"[ERROR] Column key '{column_key}' ({label}) saknas i metadata!")
                missing_columns.append(label)

        if missing_columns:
            QMessageBox.warning(self, "Missing Columns", f"The following columns are missing: {', '.join(missing_columns)}")

        # Debugging: Print raw metadata details
        print("[DEBUG] Metadata column headers:", self.metadata.columns.tolist())
        print("[DEBUG] Metadata preview:\n", self.metadata.head())

        # Initialize UI
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Instructions
        layout.addWidget(QLabel("Select additional filters:"))

        # Grid layout for dropdowns
        dropdown_layout = QGridLayout()

        # Dropdowns for additional filters
        self.english_dropdown = QComboBox()
        self.latin_dropdown = QComboBox()
        self.swedish_dropdown = QComboBox()

        self.setup_dropdown(self.english_dropdown, "english", "English")
        self.setup_dropdown(self.latin_dropdown, "latin", "Latin")
        self.setup_dropdown(self.swedish_dropdown, "swedish", "Swedish")

        dropdown_layout.addWidget(QLabel("English:"), 0, 0)
        dropdown_layout.addWidget(self.english_dropdown, 0, 1)
        dropdown_layout.addWidget(QLabel("Latin:"), 1, 0)
        dropdown_layout.addWidget(self.latin_dropdown, 1, 1)
        dropdown_layout.addWidget(QLabel("Swedish:"), 2, 0)
        dropdown_layout.addWidget(self.swedish_dropdown, 2, 1)

        layout.addLayout(dropdown_layout)

        # Checkbox to include/exclude base filters
        self.include_base_filters_checkbox = QCheckBox("Include filters from standard Metadata")
        layout.addWidget(self.include_base_filters_checkbox)

        # Apply button
        apply_button = QPushButton("Apply Filters")
        apply_button.clicked.connect(self.apply_filters)
        layout.addWidget(apply_button)

        self.setLayout(layout)

    def setup_dropdown(self, dropdown, expected_column, label):
        """Set up a dropdown with unique values from a specific column."""
        print(f"[DEBUG] Setting up dropdown for column '{label}'")
        print(f"[DEBUG] Available metadata columns: {self.metadata.columns.tolist()}")
        
        # Check for the mapped column name
        column_key = self.column_mapping.get(expected_column)
        if column_key and column_key in self.metadata.columns:
            unique_values = ["All"] + sorted(self.metadata[column_key].dropna().unique())
            print(f"[DEBUG] Unique values for column '{label}': {unique_values}")
            dropdown.addItems(unique_values)
        else:
            print(f"[ERROR] Column '{label}' is missing from metadata.")
            dropdown.addItem("Not Available")

    def apply_filters(self):
        """Apply advanced filters based on selected criteria."""
        print("[DEBUG] Applying filters...")
        filtered_metadata = self.metadata.copy()

        # Apply filters
        for dropdown, column, label in [
            (self.english_dropdown, "english", "English"),
            (self.latin_dropdown, "latin", "Latin"),
            (self.swedish_dropdown, "swedish", "Swedish")
        ]:
            selected_value = dropdown.currentText()
            print(f"[DEBUG] Selected value for '{label}': {selected_value}")
            if selected_value != "All":
                filtered_metadata = self.filter_bird_names(filtered_metadata, self.column_mapping[column], selected_value, label)

        # Optionally combine with base filters
        if self.include_base_filters_checkbox.isChecked() and self.base_filters:
            print("[DEBUG] Combining with base filters...")
            filtered_metadata = self.combine_with_base_filters(filtered_metadata)

        # Extract file names from column B
        if "file name" not in filtered_metadata.columns:
            QMessageBox.warning(self, "Error", "Column 'File Name' is missing from metadata.")
            self.filtered_results = []
        else:
            self.filtered_results = filtered_metadata["file name"].tolist()

        # Notify the user
        if self.filtered_results:
            QMessageBox.information(self, "Filter Applied", f"{len(self.filtered_results)} files matched the criteria.")
        else:
            QMessageBox.warning(self, "No Results", "No files matched the selected criteria.")

        self.accept()

    def filter_bird_names(self, metadata, column, selected_value, label):
        """Filter metadata for bird names in a given column."""
        try:
            bird_column = metadata[column]
            matches = bird_column == selected_value
            print(f"[DEBUG] Rows matching '{label}' for value '{selected_value}': {matches.sum()} matches found.")
            return metadata[matches]
        except KeyError as e:
            QMessageBox.warning(self, "Error", f"Column '{label}' is missing.")
            return metadata

    def combine_with_base_filters(self, filtered_metadata):
        """Combine current filters with base filters from MetadataFilterWindow."""
        for column, value in self.base_filters.items():
            if column in filtered_metadata.columns:
                print(f"[DEBUG] Applying base filter: {column} == {value}")
                filtered_metadata = filtered_metadata[filtered_metadata[column] == value]
        return filtered_metadata

    def get_filtered_results(self):
        """Return the filtered results."""
        return self.filtered_results

