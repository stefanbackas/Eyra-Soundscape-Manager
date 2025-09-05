import os
import sys
import json
import logging
from datetime import datetime, time

# Google Sheets and metadata-related imports
from google_sheets_test import fetch_metadata
from metadata_window import MetadataFilterWindow


# PyQt5 imports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QPushButton, QLineEdit, QSlider, QSpinBox, QFormLayout,
    QCheckBox, QFileDialog, QDialog, QComboBox, QTimeEdit, QListWidgetItem,
    QAbstractItemView, QColorDialog, QGridLayout
)
from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtGui import QColor
from FileOrganizerWindow import FileOrganizerWindow
from sound_scheduler_v1_6 import SchedulerApp
from PyQt5.QtGui import QIntValidator

from PyQt5.QtCore import QDir
from PyQt5.QtWidgets import QPushButton, QVBoxLayout, QLabel, QProgressBar, QDialog
import traceback  # Lägg till denna rad överst i din Python-fil

from ProjectValidator import ProjectValidator
from ProjectValidator import ProjectValidator, validate_exported_project_structure
from EyraPlayerWindow import EyraPlayerWindow





print("STARTING Eyra_UI_v1.938.py")


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def log_filter_results(filters, matching_rows, total_rows, period=None):
    """
    Log relevant details about metadata filtering.
    :param filters: The filters applied to the metadata.
    :param matching_rows: Number of rows matching the filters.
    :param total_rows: Total number of rows before filtering.
    :param period: (Optional) Time period filter applied.
    """
    logging.info(f"Applied filters: {filters}")
    if period:
        logging.info(f"Time period: {period}")
    logging.info(f"Matching rows: {matching_rows} out of {total_rows}")


# Set environment variable for macOS if necessary
os.environ['QT_MAC_WANTS_LAYER'] = '1'








# Skapa mappstrukturen om den inte finns
def ensure_bank_structure():
    root_folder = "SavedBank"
    subfolders = ["Tracklists", "Groups", "Pools", "Slots"]

    if not os.path.exists(root_folder):
        os.makedirs(root_folder)  # Skapa rotmappen SavedBank
        print(f"Skapade rotmappen: {root_folder}")

    for subfolder in subfolders:
        subfolder_path = os.path.join(root_folder, subfolder)
        if not os.path.exists(subfolder_path):
            os.makedirs(subfolder_path)  # Skapa underkategorierna
            print(f"Skapade undermappen: {subfolder_path}")




def get_absolute_path(relative_path):
    """Returnerar absolut sökväg baserat på appens katalog."""
    if getattr(sys, 'frozen', False):  # Kontrollera om appen är fristående
        base_path = sys._MEIPASS  # PyInstaller-specifik mapp
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)




def is_name_unique(self, name):
    """Kontrollera om ett namn är unikt över alla kategorier."""
    all_names = (
        set(self.tracklist_data.keys())
        | set(self.group_data.keys())
        | set(self.pool_data.keys())
        | set(self.slot_data.keys())
    )
    return name not in all_names

def generate_unique_name(self, base_name):
    """Generera ett unikt namn baserat på ett grundnamn."""
    counter = 1
    unique_name = base_name
    while not self.is_name_unique(unique_name):
        unique_name = f"{base_name}_{counter}"
        counter += 1
    return unique_name





from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QAbstractItemView, QPushButton, QMessageBox, QInputDialog
)
from PyQt5.QtCore import Qt


class GroupWindow(QWidget):
    """Fönster för enskild grupp med tilldelade tracklists och grupper."""

    def __init__(self, group_name, group_data, available_tracklists, available_groups, on_save, main_window):
        super().__init__()
        self.setWindowTitle(f"Group: {group_name}")
        self.resize(300, 600)

        # Ställ in en grundläggande stil för fönstret
        self.setStyleSheet("background-color: #5C4033;")

        
        self.group_name = group_name
        self.group_data = group_data  # Dictionary med 'tracklists' och 'groups'
        self.available_items = available_tracklists + available_groups  # Kombinera tillgängliga tracklists och groups
        self.on_save = on_save
        self.main_window = main_window  # Referens till MainWindow

        # Filtrera tillgängliga Tracklists
        self.available_tracklists = [
            tl_name for tl_name in available_tracklists
            if self.main_window.tracklist_data.get(tl_name, {}).get('primary_group') not in (self.group_name, None)
        ]

        # Layout för fönstret
        layout = QVBoxLayout(self)

        # Titel och "Sätt som Huvudgrupp"-knapp i en horisontell layout
        header_layout = QHBoxLayout()

        # Titel för fönstret
        self.label = QLabel(f"Group: {group_name}")
        header_layout.addWidget(self.label)

        # "Sätt som Huvudgrupp"-knapp
        self.set_primary_button = QPushButton("Huvudgrupp")
        self.set_primary_button.setFixedSize(100, 30)  # Gör knappen liten
        self.set_primary_button.clicked.connect(self.set_primary_group)
        header_layout.addStretch()  # Flytta knappen längst till höger
        header_layout.addWidget(self.set_primary_button)

        # Lägg till header_layout överst i huvudlayouten
        layout.addLayout(header_layout)

        # Lista för att visa tilldelade tracklists och grupper
        layout.addWidget(QLabel("Tilldelade Tracklists och Grupper"))
        self.assigned_list = QListWidget()
        self.assigned_list.setStyleSheet("background-color: dark grey; color: white;")

        self.assigned_list.setSelectionMode(QAbstractItemView.ExtendedSelection)  # Aktivera multi-val
        self.assigned_list.setDragDropMode(QAbstractItemView.InternalMove)  # Aktivera drag och släpp
        self.assigned_list.setDefaultDropAction(Qt.MoveAction)
        layout.addWidget(self.assigned_list)
        self.assigned_list.addItems(group_data.get('tracklists', []) + group_data.get('groups', []))

       

        # Lista för att visa tillgängliga tracklists och grupper
        layout.addWidget(QLabel("Tillgängliga Tracklists och Grupper"))
        self.available_list = QListWidget()
        self.available_list.setStyleSheet("background-color: dark grey; color: white;")

        self.available_list.setSelectionMode(QAbstractItemView.ExtendedSelection)  # Aktivera multi-val
        layout.addWidget(self.available_list)
        for item in self.available_items:
            if item not in self.group_data.get('tracklists', []) and item not in self.group_data.get('groups', []):
                self.available_list.addItem(item)

        # Uppdatera listan vid initiering
        self.update_assigned_list()

        # Lägg till och ta bort-knappar
        self.add_button = QPushButton("Lägg till Valda")
        self.add_button.clicked.connect(self.add_selected_items)
        layout.addWidget(self.add_button)

        self.remove_button = QPushButton("Ta bort Valda")
        self.remove_button.clicked.connect(self.remove_selected_items)
        layout.addWidget(self.remove_button)

        # Lägg till huvudlayout för volymsektionen
        volume_layout = QVBoxLayout()

        # Skapa horisontell layout för slidern och dess värde
        slider_layout = QHBoxLayout()

        # Skapa och konfigurera volymslider
        self.group_volume_slider = QSlider(Qt.Horizontal)  # Skapa slidern
        self.group_volume_slider.setRange(0, 150)  # Maxvolym 150

        saved_volume = int(self.group_data.get('volume', 1.0) * 100)  # Hämta volym som procent
        self.group_volume_slider.setValue(saved_volume)  # Använd sparat värde

        # Lägg till anslutningar och uppdateringar
        self.group_volume_slider.valueChanged.connect(self.update_group_volume_label)
        self.group_volume_slider.valueChanged.connect(self.adjust_tracklist_volumes)

        # Skapa och konfigurera volymetikett
        self.group_volume_label = QLabel(str(saved_volume))  # Skapa etiketten
        self.group_volume_label.setFixedWidth(40)  # Ge etiketten en fast bredd för konsekvent placering
        self.group_volume_label.setAlignment(Qt.AlignCenter)

        # Skapa och konfigurera textruta för volyminmatning
        self.group_volume_input = QLineEdit()
        self.group_volume_input.setStyleSheet("background-color: dark grey; color: white;")
        self.group_volume_input.setValidator(QIntValidator(0, 150))  # Endast siffror mellan 0 och 150
        self.group_volume_input.setText(str(saved_volume))  # Använd sparat värde
        self.group_volume_input.returnPressed.connect(self.update_volume_from_input)

        # Layout för volymslider, etikett och textruta
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(QLabel("Group Volume:"))  # Lägg till en textetikett
        slider_layout.addWidget(self.group_volume_slider)
        slider_layout.addWidget(self.group_volume_label)

        volume_layout = QVBoxLayout()
        volume_layout.addLayout(slider_layout)
        volume_layout.addWidget(QLabel("Volume Input:"))
        volume_layout.addWidget(self.group_volume_input)

        # Lägg till volymlayouten i huvudlayouten
        layout.addLayout(volume_layout)



        # Spara-knapp
        save_button = QPushButton("Spara och Stäng")
        save_button.setStyleSheet("background-color: #109090; color: white;")
        save_button.clicked.connect(self.save_and_close)
        layout.addWidget(save_button)

                # Navigeringsknappar (föregående och nästa grupp)
        navigation_layout = QHBoxLayout()

        self.prev_group_button = QPushButton("←")
        self.prev_group_button.setStyleSheet("background-color: #444488; color: white; font-size: 16px;")
        self.prev_group_button.clicked.connect(self.open_previous_group)
        navigation_layout.addWidget(self.prev_group_button)

        self.next_group_button = QPushButton("→")
        self.next_group_button.setStyleSheet("background-color: #444488; color: white; font-size: 16px;")
        self.next_group_button.clicked.connect(self.open_next_group)
        navigation_layout.addWidget(self.next_group_button)

        layout.addLayout(navigation_layout)



    def update_group_volume_label(self, value):
        """Uppdatera etiketten för gruppvolymen."""
        self.group_volume_label.setText(str(value))
        self.group_volume_input.setText(str(value))

    def update_volume_from_input(self):
        """Uppdatera slidern från textinmatning."""
        value = int(self.group_volume_input.text())
        self.group_volume_slider.setValue(value)

    def add_selected_items(self):
        """Lägg till markerade tracklists och grupper från tillgängliga listan."""
        selected_items = self.available_list.selectedItems()
        for item in selected_items:
            name = item.text()

            if name == self.group_name:
                continue

            if name in self.group_data.get('tracklists', []) or name in self.group_data.get('groups', []):
                continue

            if name in self.main_window.tracklist_data:
                self.group_data['tracklists'].append(name)

                if 'tracklists_data' not in self.group_data:
                    self.group_data['tracklists_data'] = {}

                if name not in self.group_data['tracklists_data']:
                    self.group_data['tracklists_data'][name] = {
                        'original_volume': self.main_window.tracklist_data.get(name, {}).get('volume', 0.1),
                        'volume': self.main_window.tracklist_data.get(name, {}).get('volume', 0.1)
                    }

                self.assigned_list.addItem(name)

            elif name in self.main_window.group_data:
                self.group_data['groups'].append(name)
                self.assigned_list.addItem(name)  # ⬅️ Ingen "(Grupp)" längre

            self.available_list.takeItem(self.available_list.row(item))






    def remove_selected_items(self):
        """Ta bort markerade tracklists och grupper från tilldelade listan."""
        selected_items = self.assigned_list.selectedItems()
        for item in selected_items:
            item_name = item.text()

            # Ta bort "(Huvudgrupp)"-text om den finns
            if item_name.endswith(" (Huvudgrupp)"):
                item_name = item_name.replace(" (Huvudgrupp)", "")

            # Hantera borttagning av tracklists
            if item_name in self.group_data.get('tracklists', []):
                self.group_data['tracklists'].remove(item_name)

                # Ta bort "Huvudgrupp"-markeringen om det är denna grupp
                tracklist_data = self.main_window.tracklist_data.get(item_name, {})
                if tracklist_data.get('primary_group') == self.group_name:
                    tracklist_data['primary_group'] = None
                    print(f"[DEBUG] Huvudgrupp för Tracklist '{item_name}' har tagits bort.")

            # Hantera borttagning av grupper
            if item_name in self.group_data.get('groups', []):
                self.group_data['groups'].remove(item_name)

            # Ta bort från GUI
            self.assigned_list.takeItem(self.assigned_list.row(item))

            # Skapa ett nytt objekt med ren text för tillgängliga listan
            clean_item = QListWidgetItem(item_name)
            self.available_list.addItem(clean_item)




    def save_and_close(self):
        """Spara gruppens data och stäng fönstret."""
        self.group_data['tracklists'] = []
        self.group_data['groups'] = []
        self.group_data['volume'] = self.group_volume_slider.value() / 100  # Spara volym som faktor

        for i in range(self.assigned_list.count()):
            item_text = self.assigned_list.item(i).text()
            print(f"[DEBUG] Läser item_text: {item_text}")  # 👈 NYTT
            is_primary = " (Huvudgrupp)" in item_text

            # Rensa bort suffixer
            name = item_text.replace(" (Huvudgrupp)", "").replace(" (Grupp)", "")
            print(f"[DEBUG] Namn utan suffix: {name}")  # 👈 NYTT

            # Lägg till Tracklist
            if name in self.main_window.tracklist_data:
                self.group_data['tracklists'].append(name)

                if is_primary:
                    self.main_window.tracklist_data[name]['primary_group'] = self.group_name

                groups = self.main_window.tracklist_data[name].setdefault('groups', [])
                if self.group_name not in groups:
                    groups.append(self.group_name)

            # Lägg till undergrupp
            elif name in self.main_window.group_data and name != self.group_name:
                self.group_data['groups'].append(name)
                print(f"[DEBUG] Lagt till grupp: {name}")  # 👈 NYTT

        self.main_window.group_data[self.group_name] = self.group_data
        print(f"[DEBUG] Grupp '{self.group_name}' sparad med data: {self.group_data}")

        self.on_save()
        self.close()






    def open_previous_group(self):
        """Öppna föregående grupp i listan."""
        if self.main_window:
            group_names = list(self.main_window.group_data.keys())  # Hämta alla gruppnamn
            current_index = group_names.index(self.group_name) if self.group_name in group_names else -1
            
            if current_index > 0:  # Finns en föregående grupp?
                prev_group_name = group_names[current_index - 1]
                self.switch_to_group(prev_group_name)

    def open_next_group(self):
        """Öppna nästa grupp i listan."""
        if self.main_window:
            group_names = list(self.main_window.group_data.keys())  # Hämta alla gruppnamn
            current_index = group_names.index(self.group_name) if self.group_name in group_names else -1
            
            if current_index < len(group_names) - 1:  # Finns en nästa grupp?
                next_group_name = group_names[current_index + 1]
                self.switch_to_group(next_group_name)

    def switch_to_group(self, new_group_name):
        """Stäng aktuell grupp och öppna en ny."""
        if self.main_window and new_group_name in self.main_window.group_data:
            self.save_and_close()  # Spara och stäng nuvarande grupp
            self.main_window.open_group_window(new_group_name)  # Öppna ny grupp
        



    def sync_group_data(self):
        """Synkronisera group_data med den aktuella ordningen i assigned_list."""
        self.group_data['tracklists'] = []
        self.group_data['groups'] = []

        for i in range(self.assigned_list.count()):
            item_name = self.assigned_list.item(i).text()
            if item_name in self.available_items:
                if item_name in self.group_data['groups']:
                    self.group_data['groups'].append(item_name)
                else:
                    self.group_data['tracklists'].append(item_name)

    def keyPressEvent(self, event):
        """Hantera tangenttryckningar för borttagning."""
        if event.matches(QKeySequence.Delete) or (event.modifiers() == Qt.MetaModifier and event.key() == Qt.Key_Backspace):
            self.remove_selected_items()
        else:
            super().keyPressEvent(event)



    def adjust_tracklist_volumes(self):
        """Justera volymen för alla tracklists i gruppen baserat på gruppvolymen."""
        group_volume = self.group_volume_slider.value() / 100  # Gruppvolym som en faktor
        print(f"[DEBUG] Gruppvolym justerad till: {group_volume}")
        
        for tracklist_name in self.group_data.get('tracklists', []):
            # Kontrollera om denna grupp är huvudgrupp för tracklisten
            if self.main_window.tracklist_data.get(tracklist_name, {}).get('primary_group') != self.group_name:
                continue  # Hoppa över om det inte är huvudgruppen

            tracklist_data = self.group_data['tracklists_data'].get(tracklist_name, {})
            original_volume = tracklist_data.get('original_volume', 0.1)
            new_volume = round(original_volume * group_volume, 3)
            tracklist_data['volume'] = new_volume

            # Uppdatera datan i MainWindow också
            if tracklist_name in self.main_window.tracklist_data:
                self.main_window.tracklist_data[tracklist_name]['volume'] = new_volume

            print(f"[DEBUG] Tracklist '{tracklist_name}' original volym: {original_volume}")
            print(f"[DEBUG] Tracklist '{tracklist_name}' ny volym: {new_volume}")

            # Uppdatera öppet TracklistWindow
            if tracklist_name in self.main_window.tracklist_windows:
                print(f"[DEBUG] Uppdaterar TracklistWindow för '{tracklist_name}'")
                window = self.main_window.tracklist_windows[tracklist_name]
                window.adjust_volume_from_group(group_volume)
                window.update()  # Tvinga gränssnittet att rita om




    def set_primary_group(self):
        """Sätt de aktuella valda objekten som huvudgrupp."""
        selected_items = self.assigned_list.selectedItems()  # Hämta alla valda objekt
        if not selected_items:
            QMessageBox.warning(self, "Inga Tracklists valda", "Välj en eller flera Tracklists för att ange huvudgrupp.")
            return

        for item in selected_items:
            tracklist_name = item.text()
            if tracklist_name.endswith(" (Huvudgrupp)"):
                tracklist_name = tracklist_name.replace(" (Huvudgrupp)", "")

            # Uppdatera huvudgruppen i MainWindow
            if tracklist_name in self.main_window.tracklist_data:
                self.main_window.tracklist_data[tracklist_name]['primary_group'] = self.group_name
                # Uppdatera visningen i listan
                item.setText(f"{tracklist_name} (Huvudgrupp)")
                print(f"[DEBUG] Huvudgrupp för Tracklist '{tracklist_name}' är nu '{self.group_name}'.")


    def update_assigned_list(self):
        """Uppdatera listan med tilldelade Tracklists och Grupper för att visa korrekt etikett."""
        self.assigned_list.clear()

        # Visa alla tilldelade tracklists
        for tracklist_name in self.group_data.get('tracklists', []):
            item = QListWidgetItem(tracklist_name)
            primary_group = self.main_window.tracklist_data.get(tracklist_name, {}).get('primary_group')
            if primary_group == self.group_name:
                item.setText(f"{tracklist_name} (Huvudgrupp)")
            self.assigned_list.addItem(item)

        # Visa alla tilldelade grupper med mycket mörkgrå bakgrund
        for group_name in self.group_data.get('groups', []):
            if group_name != self.group_name:
                item = QListWidgetItem(f"{group_name} (Grupp)")
                item.setBackground(QColor(40, 40, 40))        # Mörk bakgrund
                item.setForeground(QColor(220, 220, 220))     # Ljus text
                self.assigned_list.addItem(item)

            
            












            



            

        





import os
import subprocess
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QTextEdit, QComboBox,
    QFormLayout, QSpinBox, QSlider, QCheckBox, QLabel, QFileDialog, QMessageBox,
    QListWidgetItem, QApplication, QDialog, QMainWindow
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QKeySequence
import pandas as pd


import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from PyQt5.QtWidgets import QScrollArea


import gspread
from oauth2client.service_account import ServiceAccountCredentials

import gspread
from oauth2client.service_account import ServiceAccountCredentials

def fetch_metadata(range_name):
    """Hämta metadata från Google Sheets."""
    try:
        # Ange Google Sheets ID
        SPREADSHEET_ID = "1tFo867jOPKON5SrCmFUcaqKFdvLkpU6kTcY0i7QcDw8"

        # Sökvägen till din credentials-fil
        SERVICE_ACCOUNT_FILE = "credentials.json"

        # Ange nödvändiga scopes
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

        # Bygg Google Sheets API-klienten
        service = build('sheets', 'v4', credentials=creds)

        # Hämta data från Google Sheets
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=range_name).execute()
        values = result.get('values', [])

        if not values:
            print("No data found in Google Sheet.")
            return None

        # Omvandla till DataFrame
        headers = values[0]
        data = values[1:]
        metadata = pd.DataFrame(data, columns=headers)
        metadata.columns = metadata.columns.str.strip()  # Ta bort osynliga mellanslag
        metadata.columns = metadata.columns.str.lower()  # Omvandla till små bokstäver

        print("Cleaned metadata columns:", metadata.columns.tolist())  # Debug

        print(f"Metadata fetched successfully for range {range_name}:")
        print(metadata.head())  # Visa de första raderna för verifiering
        return metadata

    except Exception as e:
        print(f"Error fetching metadata: {e}")
        return None





















def fetch_advanced_metadata():
    """Fetch advanced metadata including English, Latin, and Swedish bird names."""
    try:
        SPREADSHEET_ID = "1tFo867jOPKON5SrCmFUcaqKFdvLkpU6kTcY0i7QcDw8"
        SERVICE_ACCOUNT_FILE = "credentials.json"
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds)

        # Fetch data
        range_advanced = "BP2:BR"
        result_advanced = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID, range=range_advanced).execute()
        values_advanced = result_advanced.get('values', [])

        if not values_advanced:
            print("[ERROR] No data found in the advanced metadata range.")
            return pd.DataFrame()

        # Parse headers and data
        headers_advanced = values_advanced[0]
        data_advanced = values_advanced[1:]
        print("[DEBUG] Headers fetched from BP:BR:", headers_advanced)
        print("[DEBUG] First 5 rows fetched:", data_advanced[:5])

        # Normalize headers
        advanced_df = pd.DataFrame(data_advanced, columns=headers_advanced)
        advanced_df.columns = advanced_df.columns.str.strip().str.lower()

        # Debug: Validate the processed DataFrame
        print("[DEBUG] Final advanced metadata columns:", advanced_df.columns.tolist())
        print("[DEBUG] Advanced metadata preview:")
        print(advanced_df.head())

        return advanced_df

    except Exception as e:
        print(f"[ERROR] Error fetching advanced metadata: {e}")
        return pd.DataFrame()


































    
        #print("Columns fetched from Google Sheets:")
        #print(metadata.columns.tolist())  # Detta skriver ut alla kolumnnamn
        #print(metadata.head())  # Detta visar några rader av datan

def filter_by_time_period(metadata, selected_period, time_periods):
        """Filtrera metadata baserat på vald tidsperiod."""
        if selected_period == "All":
            return metadata

        start_period, end_period = time_periods[selected_period]
        start_period = datetime.strptime(start_period, "%H:%M").time()
        end_period = datetime.strptime(end_period, "%H:%M").time()

        def is_within_period(row):
            start_time = datetime.strptime(row["time start"], "%H:%M:%S").time()

            # Hantera tidsperioder som går över midnatt (t.ex. Night)
            if start_period < end_period:  # Normal period
                return start_period <= start_time < end_period
            else:  # Period som går över midnatt
                return start_time >= start_period or start_time < end_period

        return metadata[metadata.apply(is_within_period, axis=1)]


















global_test_callback = lambda files: print(f"[TEST CALLBACK] Filer mottagna: {files}")
from PyQt5.QtCore import pyqtSignal


class TracklistWindow(QWidget):
    """Fönster för enskild tracklist med filer och inställningar."""
    closed = pyqtSignal(str)  # Signal som skickar tracklistens namn vid stängning

    def __init__(self, tracklist_name, tracklist_data, on_save, main_window=None):
        super().__init__()  # Lägg till för att stödja MainWindow
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()  # Sätter fokus direkt på fönstret
        QTimer.singleShot(100, self.ensure_focus)  # Försena fokusförändring för att säkerställa att det fungerar
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
        self.file_list.keyPressEvent = self.file_list_keyPressEvent

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

                # Navigationsknappar (föregående och nästa tracklist)
        navigation_layout = QHBoxLayout()

        self.prev_button = QPushButton("←")
        self.prev_button.setStyleSheet("background-color: #444488; color: white; font-size: 16px;")
        self.prev_button.clicked.connect(self.open_previous_tracklist)
        navigation_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("→")
        self.next_button.setStyleSheet("background-color: #444488; color: white; font-size: 16px;")
        self.next_button.clicked.connect(self.open_next_tracklist)
        navigation_layout.addWidget(self.next_button)

        right_layout.addLayout(navigation_layout)

        print(f"TracklistWindow har fått fokus: {self.hasFocus()}")

        


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



    def open_previous_tracklist(self):
        """Öppna föregående Tracklist i listan."""
        if self.main_window:
            tracklist_names = list(self.main_window.tracklist_data.keys())  # Hämta alla tracklist-namn
            current_index = tracklist_names.index(self.tracklist_name) if self.tracklist_name in tracklist_names else -1
            
            if current_index > 0:  # Finns en föregående tracklist?
                prev_tracklist_name = tracklist_names[current_index - 1]
                self.switch_to_tracklist(prev_tracklist_name)

    def open_next_tracklist(self):
        """Öppna nästa Tracklist i listan."""
        if self.main_window:
            tracklist_names = list(self.main_window.tracklist_data.keys())  # Hämta alla tracklist-namn
            current_index = tracklist_names.index(self.tracklist_name) if self.tracklist_name in tracklist_names else -1
                
            if current_index < len(tracklist_names) - 1:  # Finns en nästa tracklist?
                next_tracklist_name = tracklist_names[current_index + 1]
                self.switch_to_tracklist(next_tracklist_name)

    def switch_to_tracklist(self, new_tracklist_name):
        """Stäng aktuell Tracklist och öppna en ny."""
        if self.main_window and new_tracklist_name in self.main_window.tracklist_data:
            self.save_and_close()  # Spara och stäng nuvarande Tracklist
            self.main_window.open_tracklist_window(new_tracklist_name)  # Öppna ny Tracklist






    def keyPressEvent(self, event):
        print(f"Tangent tryckt: {event.key()}")  # Debug-utskrift
        
        focused_widget = QApplication.focusWidget()
        print(f"Widget med tangentfokus: {focused_widget}")

        """Hantera tangenttryckningar."""
        if event.key() == Qt.Key_Up:
            current_row = self.file_list.currentRow()
            if current_row > 0:
                self.file_list.setCurrentRow(current_row - 1)
        elif event.key() == Qt.Key_Down:
            current_row = self.file_list.currentRow()
            if current_row < self.file_list.count() - 1:
                self.file_list.setCurrentRow(current_row + 1)
        elif event.matches(QKeySequence.Copy):  
            self.copy_selected_files()
        elif event.key() == Qt.Key_Space:
            print("Space tryckt!")  # Debug-utskrift
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
        print("play_selected_file() anropades")  # Lägg till denna rad
        
        selected_item = self.file_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Ingen fil vald", "Välj en fil för att spela upp.")
            return

        file_name = selected_item.text()
        predefined_folder = '/Users/stefanbackas/Documents/000_EYRA/Eyra_Soundscapes/ALL_EYRA_TRACKS_MP3'
        file_path = os.path.join(predefined_folder, file_name)

        if not os.path.exists(file_path):
            QMessageBox.warning(self, "Filen hittades inte", f"Filen '{file_name}' kunde inte hittas i:\n{predefined_folder}")
            return

        try:
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

            def on_dialog_closed():
                """Körs när metadatafönstret stängs"""
                filtered_results = dialog.get_filtered_results()
                if filtered_results:
                    self.add_filtered_files(filtered_results)

            dialog.finished.connect(on_dialog_closed)  # Kör on_dialog_closed() när fönstret stängs
            dialog.show()  # Visa fönstret

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


    from PyQt5.QtCore import QTimer
    from PyQt5.QtWidgets import QMessageBox

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

        # 🟢 Skapa och visa en bekräftelseruta som stänger sig själv efter 2 sekunder
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Filer tillagda")
        msg_box.setText(f"Lade till {len(files)} filer.")
        msg_box.setIcon(QMessageBox.Information)

        # Starta en timer som stänger rutan efter 2 sekunder
        QTimer.singleShot(2000, msg_box.close)

        msg_box.exec_()  # Visa rutan




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

    def ensure_focus(self):
        """Säkerställ att TracklistWindow har tangentfokus efter att det öppnats."""
        self.setFocus()
        print(f"TracklistWindow efter fokusfix: {self.hasFocus()}")

    def file_list_keyPressEvent(self, event):
        """Fångar tangenttryckningar direkt i file_list."""
        print(f"file_list - Tangent tryckt: {event.key()}")  # Debug

        if event.key() == Qt.Key_Space:
            print("Space tryckt i file_list!")  # Debug
            self.play_selected_file()
        else:
            QListWidget.keyPressEvent(self.file_list, event)  # Skicka vidare eventet
        
        
        


        


    





       

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QListWidget, QPushButton, QGridLayout, QMessageBox, QScrollArea
)
from PyQt5.QtCore import QTime
import pandas as pd
from datetime import datetime


class MetadataFilterWindow(QDialog):
    """Metadata filter window."""

    def __init__(self, metadata, time_periods=None):
        super().__init__()
        self.metadata = metadata
        self.time_periods = time_periods if time_periods else self.load_saved_time_periods()
        self.filtered_results = []
        self.init_ui()

    def init_ui(self):
        """Skapa UI för att hantera inklusion och exklusion av flera underkategorier samtidigt."""
        self.setWindowTitle("Metadata Filter")
        self.resize(700, 500)  # Justerad storlek

        self.setStyleSheet("""
            QDialog {
                background-color: #5C4033;  /* Mörkbrun bakgrund */
            }
            QListWidget {
                background-color: #1A1A1A;  /* Mörkare grå bakgrund */
                color: white;
                border: 1px solid #444;
            }
            QLabel {
                color: white;
                font-weight: bold;
            }
            QPushButton {
                background-color: #556B2F; /* Blåa knappar */
                color: white;
                border-radius: 5px;
                padding: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0056b3; /* Mörkare blå vid hover */
            }
        """)

        # **Skapa en scrollarea så att fönstret aldrig blir för stort**
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        main_widget = QDialog(self)
        scroll_area.setWidget(main_widget)

        layout = QVBoxLayout(main_widget)

        # **Grid layout för att hantera filter**
        filter_layout = QGridLayout()
        self.include_filters = {}
        self.exclude_filters = {}

        row = 0
        for column in self.metadata.columns:
            if column.lower() not in ["file name", "time start", "time stop"]:
                # Skapa listor för att välja flera underkategorier
                include_list = QListWidget()
                include_list.setSelectionMode(QListWidget.MultiSelection)
                include_values = sorted(value for value in self.metadata[column].dropna().unique() if str(value).strip())
                include_list.addItem("Select All")  # Lägger till "Select All" högst upp
                include_list.addItems(include_values)
                include_list.itemClicked.connect(lambda item, col=column: self.select_all_items(item, col, True))
                include_list.item(0).setFont(self.get_italic_font())
                
                exclude_list = QListWidget()
                exclude_list.setSelectionMode(QListWidget.MultiSelection)
                exclude_values = sorted(value for value in self.metadata[column].dropna().unique() if str(value).strip())
                exclude_list.addItem("Select All")  # Lägger till "Select All" högst upp
                exclude_list.addItems(exclude_values)
                exclude_list.itemClicked.connect(lambda item, col=column: self.select_all_items(item, col, False))
                exclude_list.item(0).setFont(self.get_italic_font())
                
                # Lägg till widgets i layout
                filter_layout.addWidget(QLabel(f"Include {column}:"), row, 0)
                filter_layout.addWidget(include_list, row, 1)
                filter_layout.addWidget(QLabel(f"Exclude {column}:"), row, 2)
                filter_layout.addWidget(exclude_list, row, 3)

                self.include_filters[column] = include_list
                self.exclude_filters[column] = exclude_list

                row += 1

        layout.addLayout(filter_layout)

        # **Time period filter**
        self.period_dropdown = QListWidget()
        self.period_dropdown.setSelectionMode(QListWidget.MultiSelection)
        self.period_dropdown.addItems(list(self.time_periods.keys()))
        layout.addWidget(QLabel("Filter by Time Period:"))
        layout.addWidget(self.period_dropdown)

        # **Knapp för att öppna tidsinställningar**
        time_periods_button = QPushButton("Define Time Periods")
        time_periods_button.clicked.connect(self.open_time_settings)
        layout.addWidget(time_periods_button)

        # **Apply-knappen (alltid synlig)**
        apply_button = QPushButton("Apply Filters")
        apply_button.clicked.connect(self.apply_filters)
        layout.addWidget(apply_button)

        # **Huvudlayout**
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)

        # Fast placerad knapp-layout längst ner
        button_layout = QHBoxLayout()
        #apply_button = QPushButton("Apply Filters")
        #apply_button.clicked.connect(self.apply_filters)
        button_layout.addWidget(apply_button)

        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    from PyQt5.QtCore import QTimer
    from PyQt5.QtWidgets import QMessageBox

    def apply_filters(self):
        """Filtrera metadata baserat på valda filter."""

        print("\n[DEBUG] apply_filters() anropades från följande kod:")
        traceback.print_stack()  # Skriver ut anropsstacken för att se varifrån funktionen körs

        # 🛑 Förhindra att funktionen körs två gånger samtidigt
        if hasattr(self, "_filtering_in_progress") and self._filtering_in_progress:
            print("[DEBUG] Filtrering pågår redan, stoppar dubbelanrop.")
            return
        self._filtering_in_progress = True  # Flagga: Filtrering pågår

        if not isinstance(self.metadata, pd.DataFrame) or self.metadata.empty:
            QMessageBox.warning(self, "Error", "Metadata är inte korrekt inläst.")
            self.filtered_results = []
            self._filtering_in_progress = False  # Återställ flaggan
            return

        filtered_metadata = self.metadata.copy()

        # **Filtrera på valda kategorier**
        for column, list_widget in self.include_filters.items():
            selected_values = [item.text() for item in list_widget.selectedItems()]
            if selected_values:
                filtered_metadata = filtered_metadata[
                    filtered_metadata[column].isin(selected_values)
                ]

        for column, list_widget in self.exclude_filters.items():
            selected_values = [item.text() for item in list_widget.selectedItems()]
            if selected_values:
                filtered_metadata = filtered_metadata[
                    ~filtered_metadata[column].isin(selected_values)
                ]

        # **Tidsfiltrering**
        selected_periods = [item.text() for item in self.period_dropdown.selectedItems()]
        if selected_periods:
            filtered_metadata = self.filter_by_time_period(filtered_metadata, selected_periods)

        if filtered_metadata.empty:
            QMessageBox.warning(self, "No Results", "Inga filer matchade filtren.")
            self.filtered_results = []
            self._filtering_in_progress = False  # Återställ flaggan
            return

        # **Spara resultat**
        self.filtered_results = filtered_metadata["file name"].tolist()

        print("[DEBUG] Antal filer som matchade filtren:", len(self.filtered_results))
        print("[DEBUG] Bekräftelseruta kommer nu att visas.")

        # 🟢 Skapa och visa en bekräftelseruta som stänger sig själv efter 2 sekunder
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Filtrering klar")
        msg_box.setText(f"{len(self.filtered_results)} filer matchade filtren och har skickats till tracklisten.")
        msg_box.setIcon(QMessageBox.Information)

        # Starta en timer som stänger rutan efter 2 sekunder
        QTimer.singleShot(2000, msg_box.close)

        msg_box.exec_()  # Visa rutan

        self._filtering_in_progress = False  # Återställ flaggan
        self.accept()





    def select_all_items(self, item, column, is_include):
        """Markerar eller avmarkerar alla underkategorier när "Select All" klickas."""
        list_widget = self.include_filters[column] if is_include else self.exclude_filters[column]
        if item.text() == "Select All":
            for i in range(1, list_widget.count()):  # Hoppa över "Select All"
                list_widget.item(i).setSelected(item.isSelected())


    def get_italic_font(self):
        """Returnerar en kursiv font."""
        from PyQt5.QtGui import QFont
        font = QFont()
        font.setItalic(True)
        return font
                

    


    def filter_by_time_period(self, metadata, selected_periods):
        """Filtrera metadata baserat på valda tidsperioder."""
        time_column = next(
            (col for col in metadata.columns if col.strip().lower() == "time start"),
            None
        )

        if time_column is None:
            QMessageBox.warning(self, "Error", "'Time Start' saknas i metadata.")
            return metadata  # Returnera metadata utan att filtrera

        # **Skapa en mask som börjar som False (ingen rad matchas)**
        combined_mask = pd.Series(False, index=metadata.index)

        for period in selected_periods:
            if period in self.time_periods:
                start_time, end_time = self.time_periods[period]
                mask = metadata[time_column].apply(self.is_time_in_period, args=(start_time, end_time))
                combined_mask |= mask  # Logisk OR för att inkludera fler tidsperioder

        # Använd den kombinerade masken för att filtrera metadata
        return metadata[combined_mask]




    def is_time_in_period(self, time_str, start_time, end_time):
        """Kontrollera om en given tid ligger inom en specificerad tidsperiod."""
        try:
            # **Säkerställ att vi har rätt tidsformat**
            time_str = time_str.strip()[:5]  # Tar endast HH:MM från HH:MM:SS
            time_to_check = datetime.strptime(time_str, "%H:%M")
            start = datetime.strptime(start_time, "%H:%M")
            end = datetime.strptime(end_time, "%H:%M")

            # Hantera om perioden går över midnatt
            if start <= end:
                result = start <= time_to_check < end
            else:
                result = time_to_check >= start or time_to_check < end

            # **Debugging**
            print(f"[DEBUG] Tid {time_to_check.strftime('%H:%M')} jämförs med {start.strftime('%H:%M')} - {end.strftime('%H:%M')}, Resultat: {result}")
            return result

        except Exception as e:
            print(f"[ERROR] Fel vid kontroll av tid: {e}, Problemvärde: {time_str}")
            return False







    def open_time_settings(self):
        """Öppna tidsinställningsfönstret."""
        time_window = TimeSettingsWindow(self.time_periods)
        if time_window.exec_() == QDialog.Accepted:
            self.time_periods.update(time_window.get_time_periods())
            self.save_time_periods(self.time_periods)  # Spara de valda tiderna

    def save_time_periods(self, periods):
        """Spara valda tidsperioder."""
        with open("time_settings.json", "w") as file:
            json.dump(periods, file, indent=4)

    def load_saved_time_periods(self):
        """Ladda senast använda tidsperioder."""
        try:
            with open("time_settings.json", "r") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "Morning": ("06:00", "11:00"),
                "Day": ("11:00", "16:00"),
                "Afternoon": ("16:00", "18:00"),
                "Evening": ("18:00", "22:00"),
                "Night": ("22:00", "06:00"),
            }















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


    def get_filtered_results(self):
        """Return the filtered results."""
        return self.filtered_results
    
    










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


























































from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QAbstractItemView, QCheckBox, QPushButton
)
from PyQt5.QtCore import Qt


class PoolWindow(QWidget):
    """Fönster för enskild pool med tilldelade tracklists och grupper."""
    def __init__(self, parent, pool_name, pool_data, on_save):
        super().__init__()
        self.setWindowTitle(f"Pool: {pool_name}")
        self.resize(400, 600)

        # Ställ in en grundläggande stil för fönstret
        self.setStyleSheet("background-color: #5C4033;")

        self.pool_data = pool_data
        self.on_save = on_save
        self.parent = parent  # Spara referens till huvudfönstret

        # Layout för fönstret
        layout = QVBoxLayout(self)

        # Label för fönstrets titel
        self.label = QLabel(f"Pool: {pool_name}")
        layout.addWidget(self.label)

        # Listwidget för att visa tilldelade tracklists och grupper
        self.pool_list = QListWidget()
        self.pool_list.setStyleSheet("background-color: dark grey; color: white;")

        self.pool_list.setSelectionMode(QAbstractItemView.ExtendedSelection)  # Aktivera multi-val
        self.pool_list.setDragDropMode(QAbstractItemView.InternalMove)  # Aktivera drag och släpp
        self.pool_list.setDefaultDropAction(Qt.MoveAction)
        layout.addWidget(QLabel("Tilldelade Tracklists och Groups"))
        layout.addWidget(self.pool_list)
        
        # Lägg till tracklists
        for tracklist_name in pool_data["tracklists"]:
            self.pool_list.addItem(QListWidgetItem(tracklist_name))

        # Lägg till grupper med mörkare färg
        for group_name in pool_data["groups"]:
            item = QListWidgetItem(group_name)
            item.setBackground(QColor(40, 40, 40))        # Mörkgrå bakgrund
            item.setForeground(QColor(220, 220, 220))     # Ljus text
            self.pool_list.addItem(item)


        # Listwidget för att visa alla tillgängliga tracklists
        self.tracklist_list = QListWidget()
        self.tracklist_list.setStyleSheet("background-color: dark grey; color: white;")

        self.tracklist_list.setSelectionMode(QAbstractItemView.ExtendedSelection)  # Aktivera multi-val
        layout.addWidget(QLabel("Tillgängliga Tracklists"))
        layout.addWidget(self.tracklist_list)
        self.tracklist_list.addItems(self.parent.tracklist_data.keys())  # Hämta data från parent

        # Listwidget för att visa alla tillgängliga grupper
        self.group_list = QListWidget()
        self.group_list.setStyleSheet("background-color: dark grey; color: white;")

        self.group_list.setSelectionMode(QAbstractItemView.ExtendedSelection)  # Aktivera multi-val
        layout.addWidget(QLabel("Tillgängliga Groups"))
        layout.addWidget(self.group_list)
        self.group_list.addItems(self.parent.group_data.keys())  # Hämta data från parent

        # Lägg till randomize-checkbox
        self.randomize_checkbox = QCheckBox("Randomize")
        self.randomize_checkbox.setChecked(pool_data["randomize"])
        layout.addWidget(self.randomize_checkbox)

        # Lägg till och ta bort-knappar
        self.add_button = QPushButton("Lägg till Valda Tracklists/Groups")
        self.add_button.clicked.connect(self.add_selected_items)
        layout.addWidget(self.add_button)

        self.remove_button = QPushButton("Ta bort Valda Tracklists/Groups")
        self.remove_button.clicked.connect(self.remove_selected_items)
        layout.addWidget(self.remove_button)

        # Spara-knapp
        save_button = QPushButton("Spara och Stäng")
        save_button.setStyleSheet("background-color: #109090; color: white;")
        save_button.clicked.connect(self.save_and_close)
        layout.addWidget(save_button)

                # Navigeringsknappar (föregående och nästa pool)
        navigation_layout = QHBoxLayout()

        self.prev_pool_button = QPushButton("←")
        self.prev_pool_button.setStyleSheet("background-color: #444488; color: white; font-size: 16px;")
        self.prev_pool_button.clicked.connect(self.open_previous_pool)
        navigation_layout.addWidget(self.prev_pool_button)

        self.next_pool_button = QPushButton("→")
        self.next_pool_button.setStyleSheet("background-color: #444488; color: white; font-size: 16px;")
        self.next_pool_button.clicked.connect(self.open_next_pool)
        navigation_layout.addWidget(self.next_pool_button)

        layout.addLayout(navigation_layout)


    def add_selected_items(self):
        """Lägg till markerade tracklists och grupper till poolen."""
        # Samla alla befintliga tracklists och groups från pool_list
        current_pool_items = [self.pool_list.item(i).text() for i in range(self.pool_list.count())]

        selected_tracklists = self.tracklist_list.selectedItems()
        for item in selected_tracklists:
            tracklist_name = item.text()
            if tracklist_name not in current_pool_items:  # Kontrollera om tracklisten redan är tillagd
                self.pool_data["tracklists"].append(tracklist_name)
                self.pool_list.addItem(tracklist_name)

        selected_groups = self.group_list.selectedItems()
        for item in selected_groups:
            group_name = item.text()
            if group_name not in current_pool_items:  # Kontrollera om gruppen redan är tillagd
                self.pool_data["groups"].append(group_name)
                self.pool_list.addItem(group_name)

        # Ta bort valda objekt från tillgängliga listor
        for item in selected_tracklists:
            self.tracklist_list.takeItem(self.tracklist_list.row(item))
        for item in selected_groups:
            self.group_list.takeItem(self.group_list.row(item))


    def remove_selected_items(self):
        """Ta bort markerade tracklists och grupper från poolen."""
        selected_items = self.pool_list.selectedItems()
        for item in selected_items:
            text = item.text()
            if text in self.pool_data["tracklists"]:
                self.pool_data["tracklists"].remove(text)
                self.tracklist_list.addItem(text)  # Lägg tillbaka till tillgängliga listor
            if text in self.pool_data["groups"]:
                self.pool_data["groups"].remove(text)
                self.group_list.addItem(text)  # Lägg tillbaka till tillgängliga listor
            self.pool_list.takeItem(self.pool_list.row(item))

    def save_and_close(self):
        """Spara poolens data och stäng fönstret."""
        self.sync_pool_data()
        self.pool_data["randomize"] = self.randomize_checkbox.isChecked()
        if callable(self.on_save):
            self.on_save()
        self.close()

    def sync_pool_data(self):
        """Synkronisera pool_data med den aktuella ordningen i pool_list."""
        new_order = []
        for i in range(self.pool_list.count()):
            item_text = self.pool_list.item(i).text()
            new_order.append(item_text)

        # Uppdatera data i rätt ordning
        self.pool_data["tracklists"] = [item for item in new_order if item in self.parent.tracklist_data.keys()]
        self.pool_data["groups"] = [item for item in new_order if item in self.parent.group_data.keys()]

    def keyPressEvent(self, event):
        """Hantera tangenttryckningar för borttagning."""
        if event.matches(QKeySequence.Delete) or (event.modifiers() == Qt.MetaModifier and event.key() == Qt.Key_Backspace):
            self.remove_selected_items()
        else:
            super().keyPressEvent(event)

    def open_previous_pool(self):
        """Öppna föregående pool i listan."""
        if self.parent:
            pool_names = list(self.parent.pool_data.keys())  # Hämta alla pool-namn
            current_index = pool_names.index(self.label.text().replace("Pool: ", "")) if self.label.text() else -1
            
            if current_index > 0:  # Finns en föregående pool?
                prev_pool_name = pool_names[current_index - 1]
                self.switch_to_pool(prev_pool_name)

    def open_next_pool(self):
        """Öppna nästa pool i listan."""
        if self.parent:
            pool_names = list(self.parent.pool_data.keys())  # Hämta alla pool-namn
            current_index = pool_names.index(self.label.text().replace("Pool: ", "")) if self.label.text() else -1
            
            if current_index < len(pool_names) - 1:  # Finns en nästa pool?
                next_pool_name = pool_names[current_index + 1]
                self.switch_to_pool(next_pool_name)

    def switch_to_pool(self, new_pool_name):
        """Stäng aktuell pool och öppna en ny."""
        if self.parent and new_pool_name in self.parent.pool_data:
            self.save_and_close()  # Spara och stäng nuvarande pool
            self.parent.open_pool_window(new_pool_name)  # Öppna ny pool
            














from PyQt5.QtWidgets import QComboBox, QMenu, QAction, QLineEdit
from PyQt5.QtCore import Qt

class MultiSelectComboBox(QComboBox):
    """En QComboBox där användaren kan välja flera alternativ med kryssrutor."""
    
    def __init__(self, options, label, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        self.lineEdit().setReadOnly(True)  # Förhindra manuell inmatning
        self.setPlaceholderText(f"Välj {label.lower()}...")
        
        self.options = options
        self.selected_items = set()
        
        self.menu = QMenu(self)
        self.actions = []

        for option in options:
            action = QAction(option, self)
            action.setCheckable(True)
            action.triggered.connect(self.preserve_menu_open)
            self.menu.addAction(action)
            self.actions.append(action)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_menu)
        self.mousePressEvent = self.open_menu  # Öppna menyn vid klick

    def open_menu(self, event=None):
        """Öppna menyn vid klick."""
        self.menu.exec_(self.mapToGlobal(self.rect().bottomLeft()))

    def preserve_menu_open(self):
        """Uppdatera valen men håll menyn öppen."""
        self.update_selection()
        self.open_menu()  # Håll menyn öppen efter val

    def update_selection(self):
        """Uppdatera valda alternativ och hantera specialval."""
        selected = {action.text() for action in self.actions if action.isChecked()}

        # Hantera specialvalen "Vardagar" och "Veckoslut"
        if "Vardagar (Mån-Fre)" in selected:
            selected.update(["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag"])
        if "Veckoslut (Lör-Sön)" in selected:
            selected.update(["Lördag", "Söndag"])

        selected.discard("Vardagar (Mån-Fre)")
        selected.discard("Veckoslut (Lör-Sön)")

        self.selected_items = selected
        self.update_display()

    def update_display(self):
        """Uppdatera visad text i fältet baserat på valda alternativ."""
        self.lineEdit().setText(", ".join(sorted(self.selected_items)) if self.selected_items else "Välj...")

    def get_selected(self):
        """Returnera de valda alternativen som en lista eller '*' om inget är valt."""
        return list(self.selected_items) if self.selected_items else ["*"]
    
    def set_selected(self, selected_items):
        """Återställ tidigare valda alternativ i dropdown-menyn."""
        self.selected_items = set(selected_items) if selected_items else set()
        
        for action in self.actions:
            action.setChecked(action.text() in self.selected_items)

        self.update_display()











        


import re
from PyQt5.QtWidgets import (
    QVBoxLayout, QPushButton, QLabel, QLineEdit, QTextEdit, QMessageBox,
    QDialog, QComboBox, QListWidget, QListWidgetItem, QFormLayout, QTimeEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QTimer  # Se till att denna import finns
from PyQt5.QtWidgets import QPushButton  # Flytta hit om det inte fungerar högst upp



class SlotWindow(QDialog):
    """Fönster för enskild Slot med tidsintervaller och tilldelningar."""

    def __init__(self, slot_name, slot_data, available_tracklists, available_groups, available_pools, on_save, main_window=None):
        self.main_window = main_window  # Spara en referens till MainWindow
        from PyQt5.QtWidgets import QPushButton  # Lägg till detta här
        super().__init__()
        self.setWindowTitle(f"Slot: {slot_name}")
        self.resize(500, 600)
        # Ställ in en grundläggande stil för fönstret
        self.setStyleSheet("background-color: #5C4033;")

        self.slot_data = slot_data
        self.on_save = on_save

        # Layout för fönstret
        layout = QVBoxLayout(self)

        # Label för fönstrets titel
        self.label = QLabel(f"Slot: {slot_name}")
        layout.addWidget(self.label)

        # Dropdown för att välja slot-typ
        self.slot_type_combo = QComboBox()
        self.slot_type_combo.addItems(["Timeslot", "Trigger"])  # Lägg till valen Timeslot och Trigger
        self.slot_type_combo.setStyleSheet("""
            QComboBox {
                background-color: dark grey;  /* Bakgrundsfärg för själva dropdownen */
                color: white;  /* Textfärg */
                border: 1px solid gray;  /* Kantlinje */
            }
            QComboBox QAbstractItemView {
                background-color: dark grey;  /* Bakgrundsfärg för dropdown-listan */
                color: white;  /* Textfärg för valda objekt */
                selection-background-color: gray;  /* Bakgrundsfärg vid val */
                selection-color: white;  /* Textfärg vid val */
            }
        """)
        layout.addWidget(QLabel("Välj Slot Typ:"))
        layout.addWidget(self.slot_type_combo)


        # Lista för att visa tidsintervaller med drag och släpp
        self.interval_list = QListWidget()
        self.interval_list.setStyleSheet("background-color: dark grey; color: white;")

        self.interval_list.setSelectionMode(QListWidget.ExtendedSelection)  # Tillåt multival
        self.interval_list.setDragDropMode(QListWidget.InternalMove)  # Aktivera drag och släpp
        self.interval_list.setDefaultDropAction(Qt.MoveAction)  # Flytta istället för att kopiera
        layout.addWidget(self.interval_list)

        # Knapp för att öppna popup-fönstret med tidsinställningar
        self.time_settings_button = QPushButton("Tidsinställningar")
        self.time_settings_button.setStyleSheet("background-color: #444488; color: white;")
        self.time_settings_button.clicked.connect(self.open_time_settings)
        layout.addWidget(self.time_settings_button)

        # Lägg till befintliga intervaller i listan
        for interval in slot_data.get('intervals', []):
            self.add_interval_to_list(interval)

        # Grid-layout för tid och dropdown-menyer
        time_selection_layout = QGridLayout()

        # Start- och sluttid
        time_selection_layout.addWidget(QLabel("Starttid:"), 0, 0)
        self.start_time_edit = QTimeEdit()
        self.start_time_edit.setDisplayFormat("HH:mm:ss")
        self.start_time_edit.setFixedWidth(100)  # Sätt fast bredd
        self.start_time_edit.setStyleSheet("background-color: dark grey; color: white; border: 1px solid gray;")
        time_selection_layout.addWidget(self.start_time_edit, 0, 1)

        time_selection_layout.addWidget(QLabel("Sluttid:"), 1, 0)
        self.end_time_edit = QTimeEdit()
        self.end_time_edit.setDisplayFormat("HH:mm:ss")
        self.end_time_edit.setFixedWidth(100)  # Sätt fast bredd
        self.end_time_edit.setStyleSheet("background-color: dark grey; color: white; border: 1px solid gray;")
        time_selection_layout.addWidget(self.end_time_edit, 1, 1)

        # 🟢 Justera knappen "Lägg till Tidsintervall" bredare åt vänster
        self.add_interval_button = QPushButton("Lägg till Tidsintervall")
        self.add_interval_button.setStyleSheet("background-color: #444488; color: white;")
        self.add_interval_button.clicked.connect(self.add_interval)

        # Gör knappen bredare så att den börjar vid starttidens vänsterkant
        self.add_interval_button.setFixedWidth(210)  # Justera vid behov

        # Lägg knappen under sluttid, men börja i kolumn 0 för att täcka mer av layouten
        time_selection_layout.addWidget(self.add_interval_button, 2, 0, 1, 2)  # Rad 2, Kolumner 0-1

        layout.addLayout(time_selection_layout)


    

        




        # Lägg till progress-ikonen under Sluttid, längst till vänster i högra halvan av fönstret
        from PyQt5.QtWidgets import QPushButton, QStyle

        self.progress_button = QPushButton()
        icon = self.style().standardIcon(QStyle.SP_MediaVolume)  # Använd en standardikon
        self.progress_button.setIcon(icon)
        self.progress_button.setFixedSize(32, 32)  # Gör ikonen liten
        self.progress_button.setStyleSheet("border: none;")  # Ingen kantlinje
        self.progress_button.clicked.connect(self.open_progress_window)

        # Lägg till progress-knappen i gridlayouten under "Sluttid"
        time_selection_layout.addWidget(self.progress_button, 3, 1, 1, 1)  # Rad 2, kolumn 1


        # Skapa en lista med individuella veckodagar samt de nya samlingsvalen
        weekdays_list = [
            "Vardagar (Mån-Fre)", "Veckoslut (Lör-Sön)",  # Nya samlingsval
            "Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag", "Lördag", "Söndag"
        ]

        self.weekday_combo = MultiSelectComboBox(weekdays_list, "Veckodagar")
        # self.weekday_combo.currentIndexChanged.connect(self.weekday_combo.handle_special_selections)  # 🟢 Anropa metoden när något väljs

        time_selection_layout.addWidget(QLabel("Veckodagar:"), 0, 2)
        time_selection_layout.addWidget(self.weekday_combo, 0, 3)


        # 🟢 Anpassa logik för att hantera val av samlingsval (läggs i MultiSelectComboBox-klassen)
        def handle_special_selections(self, selected_items):
            """Hantera specialvalen 'Vardagar' och 'Veckoslut' så att de väljer rätt dagar."""
            if "Vardagar (Mån-Fre)" in selected_items:
                selected_items.update(["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag"])
            if "Veckoslut (Lör-Sön)" in selected_items:
                selected_items.update(["Lördag", "Söndag"])

            # Ta bort samlingsvalen från den faktiska listan så att endast enskilda dagar skickas
            selected_items.discard("Vardagar (Mån-Fre)")
            selected_items.discard("Veckoslut (Lör-Sön)")

            return selected_items

        # 🟢 Använd funktionen i MultiSelectComboBox
        # self.weekday_combo.set_selection_handler(handle_special_selections)

        # 🟢 Ändra bakgrundsfärg till svart på dropdown-menyerna
        dropdown_style = """
            QComboBox {
                background-color: black;
                color: white;
                border: 1px solid gray;
            }
            QComboBox QAbstractItemView {
                background-color: black;
                color: white;
                selection-background-color: gray;
                selection-color: white;
            }
        """

        self.weekday_combo.setStyleSheet(dropdown_style)

        self.month_combo = MultiSelectComboBox(["Januari", "Februari", "Mars", "April", "Maj", "Juni",
                                                "Juli", "Augusti", "September", "Oktober", "November", "December"], "Månader")
        time_selection_layout.addWidget(QLabel("Månader:"), 1, 2)
        time_selection_layout.addWidget(self.month_combo, 1, 3)

        # 🟢 Ändra bakgrundsfärg till svart på dropdown-menyerna
        dropdown_style = """
            QComboBox {
                background-color: black;
                color: white;
                border: 1px solid gray;
            }
            QComboBox QAbstractItemView {
                background-color: black;
                color: white;
                selection-background-color: gray;
                selection-color: white;
            }
        """
        self.month_combo.setStyleSheet(dropdown_style)

        self.week_combo = MultiSelectComboBox([str(i) for i in range(1, 53)], "Veckor")
        time_selection_layout.addWidget(QLabel("Veckor:"), 2, 2)
        time_selection_layout.addWidget(self.week_combo, 2, 3)
        # 🟢 Ändra bakgrundsfärg till svart på dropdown-menyerna
        dropdown_style = """
            QComboBox {
                background-color: black;
                color: white;
                border: 1px solid gray;
            }
            QComboBox QAbstractItemView {
                background-color: black;
                color: white;
                selection-background-color: gray;
                selection-color: white;
            }
        """
        self.week_combo.setStyleSheet(dropdown_style)

        self.year_combo = MultiSelectComboBox([str(y) for y in range(2024, 2031)], "År")
        time_selection_layout.addWidget(QLabel("År:"), 3, 2)
        time_selection_layout.addWidget(self.year_combo, 3, 3)

        # 🟢 Ändra bakgrundsfärg till svart på dropdown-menyerna
        dropdown_style = """
            QComboBox {
                background-color: black;
                color: white;
                border: 1px solid gray;
            }
            QComboBox QAbstractItemView {
                background-color: black;
                color: white;
                selection-background-color: gray;
                selection-color: white;
            }
        """
        self.year_combo.setStyleSheet(dropdown_style)

       

        # Lägg till i huvudlayouten
        layout.addLayout(time_selection_layout)



       

        # Ta bort tidsintervall
        remove_interval_button = QPushButton("Ta bort Valda Tidsintervall")
        remove_interval_button.clicked.connect(self.remove_selected_intervals)
        layout.addWidget(remove_interval_button)

        # Knapp för att öppna schemageneratorn
        self.open_scheduler_button = QPushButton("Öppna schemagenerator")
        self.open_scheduler_button.setStyleSheet("background-color: #556B2F; color: white;")
        self.open_scheduler_button.clicked.connect(self.open_scheduler)
        layout.addWidget(self.open_scheduler_button)

                # Knapp för att exportera tidsintervaller
        export_button = QPushButton("Tidsfönster")
        export_button.setStyleSheet("background-color: #444488; color: white;")
        export_button.clicked.connect(self.export_intervals)
        layout.addWidget(export_button)


        # Välj Tracklist, Group eller Pool
        select_layout = QFormLayout()

        self.tracklist_combo = QComboBox()
        self.tracklist_combo.addItem("Ingen")
        self.tracklist_combo.addItems(available_tracklists)
        self.tracklist_combo.setStyleSheet("""
            background-color: dark grey;  /* Bakgrundsfärg */
            color: white;  /* Textfärg */
            border: 1px solid gray;  /* Kantlinje */
        """)
        select_layout.addRow("Tilldela Tracklist:", self.tracklist_combo)

        self.group_combo = QComboBox()
        self.group_combo.addItem("Ingen")
        self.group_combo.addItems(available_groups)
        self.group_combo.setStyleSheet("""
            background-color: dark grey;  /* Bakgrundsfärg */
            color: white;  /* Textfärg */
            border: 1px solid gray;  /* Kantlinje */
        """)
        select_layout.addRow("Tilldela Group:", self.group_combo)

        self.pool_combo = QComboBox()
        self.pool_combo.addItem("Ingen")
        self.pool_combo.addItems(available_pools)
        self.pool_combo.setStyleSheet("""
            background-color: dark grey;  /* Bakgrundsfärg */
            color: white;  /* Textfärg */
            border: 1px solid gray;  /* Kantlinje */
        """)
        select_layout.addRow("Tilldela Pool:", self.pool_combo)

        layout.addLayout(select_layout)

        


        



        # Spara och stäng-knapp
        save_button = QPushButton("Spara och Stäng")
        save_button.setStyleSheet("background-color: #109090; color: white;")
        save_button.clicked.connect(self.save_and_close)
        layout.addWidget(save_button)

                # Navigeringsknappar (föregående och nästa Slot)
        navigation_layout = QHBoxLayout()

        self.prev_slot_button = QPushButton("←")
        self.prev_slot_button.setStyleSheet("background-color: #444488; color: white; font-size: 16px;")
        self.prev_slot_button.clicked.connect(self.open_previous_slot)
        navigation_layout.addWidget(self.prev_slot_button)

        self.next_slot_button = QPushButton("→")
        self.next_slot_button.setStyleSheet("background-color: #444488; color: white; font-size: 16px;")
        self.next_slot_button.clicked.connect(self.open_next_slot)
        navigation_layout.addWidget(self.next_slot_button)

        layout.addLayout(navigation_layout)


        # Ladda inställningar
        self.load_settings()

    def open_scheduler(self):
        """Öppna schemageneratorn och säkerställ att SlotWindow förblir i fokus."""
        from sound_scheduler_v1_6 import SchedulerApp  # Importera schemageneratorn

        self.scheduler = SchedulerApp(send_schedule_callback=self.process_schedule)
        self.scheduler.setParent(None)  # Gör fönstret fristående
        self.scheduler.setWindowFlags(self.scheduler.windowFlags() | Qt.Window)  # Se till att det är ett eget fönster

        # Koppla signalen så att SlotWindow återaktiveras när SchedulerApp stängs
        self.scheduler.destroyed.connect(self.refocus_slotwindow)

        self.scheduler.show()
        self.scheduler.activateWindow()  # Se till att schemageneratorn blir aktiv


    def export_intervals(self):
        """Öppna ett nytt fönster för att redigera tidsintervaller direkt."""
        slot_name = self.label.text().replace("Slot: ", "")  # Hämta namnet på Slot
        intervals = [self.interval_list.item(i).text() for i in range(self.interval_list.count())]
        self.export_window = ExportWindow(slot_name, intervals, self)
        self.export_window.exec_()  # Öppna fönstret modalt


    



    def refocus_slotwindow(self):
        """Tvinga SlotWindow att ligga överst efter att SchedulerApp stängts."""
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)  # Temporärt alltid överst
        self.show()
        self.raise_()
        self.activateWindow()
        QTimer.singleShot(200, self.restore_window_flags)  # Vänta och återställ till normalt läge

    def restore_window_flags(self):
        """Återställ fönstret till normalt läge efter att ha tvingat det överst."""
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)  # Ta bort "always on top"
        self.show()  # Visa igen för att uppdatera fönsterinställningarna



    def force_focus(self):
        """Försök sätta tillbaka fokus på SlotWindow."""
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized)  # Återställ från minimerat läge om det är minimerat
        self.showNormal()  # Se till att fönstret är synligt
        QApplication.processEvents()  # Se till att event-köhantering hinner uppdateras
        self.activateWindow()  # Försök aktivera fönstret
        self.raise_()  # Lägg det överst i stacken  






    def process_schedule(self, schedule_text):
        """Bearbeta schemat som tas emot från schemageneratorn."""
        print(f"[DEBUG] SlotWindow tar emot följande data: {schedule_text}")

        if schedule_text.strip():
            intervals = schedule_text.strip().split("\n")
            for interval in intervals:
                if "-" in interval:
                    self.add_interval_to_list(interval.strip())
            # Ta bort bekräftelsemeddelandet och ersätt det med en loggutskrift
            print("[INFO] Tidsintervaller har lagts till i SlotWindow.")
        else:
            QMessageBox.warning(self, "Tomt schema", "Schemageneratorn skickade inget schema.")  # Behåll varningen


    def load_settings(self):
        """Ladda befintliga inställningar i Slot."""
        if self.slot_data.get("tracklist"):
            self.tracklist_combo.setCurrentText(self.slot_data["tracklist"])
        if self.slot_data.get("group"):
            self.group_combo.setCurrentText(self.slot_data["group"])
        if self.slot_data.get("pool"):
            self.pool_combo.setCurrentText(self.slot_data["pool"])

        # Återställ tidigare val för veckodagar, månader, veckor och år
        if self.slot_data.get("weekdays"):
            self.weekday_combo.set_selected(self.slot_data["weekdays"])
        if self.slot_data.get("months"):
            self.month_combo.set_selected(self.slot_data["months"])
        if self.slot_data.get("weeks"):
            self.week_combo.set_selected(self.slot_data["weeks"])
        if self.slot_data.get("years"):
            self.year_combo.set_selected(self.slot_data["years"])

        # Ladda tidsintervaller i listan
        self.interval_list.clear()  # Rensa listan innan vi lägger till nya rader
        print("[DEBUG] Laddar sparade intervaller:", self.slot_data.get("intervals", []))

        if self.slot_data.get("intervals"):
            for interval in self.slot_data["intervals"]:
                parts = interval.split(">")

                # Kontrollera att vi har exakt två delar: start_time och end_time
                if len(parts) != 2:
                    print(f"[ERROR] Felaktigt intervallformat: {interval}")  # Debug-utskrift
                    continue  # Hoppa över detta intervall

                start_time, end_time = parts  # Dela upp start och stopptid

                # Lägg till intervallet i listan i formatet "HH:MM:SS>HH:MM:SS"
                self.interval_list.addItem(f"{start_time}>{end_time}")

        # 🔹 Återställ start- och sluttid i `QTimeEdit` om de finns i `slot_data`
        if "start_time" in self.slot_data and "end_time" in self.slot_data:
            start_hour = int(self.slot_data["start_time"])
            end_hour = int(self.slot_data["end_time"])
            
            self.start_time_edit.setTime(QTime(start_hour, 0, 0))
            self.end_time_edit.setTime(QTime(end_hour, 0, 0))

            print(f"[DEBUG] Återställer start_time: {start_hour}, end_time: {end_hour}")




    def add_interval_to_list(self, interval):
        """Lägg till ett tidsintervall i tabellen i formatet HH:MM:SS>HH:MM:SS"""
        print(f"[DEBUG] Försöker lägga till intervallet: {interval}")  # Debugutskrift

        # Om intervallet använder "-", konvertera till ">"
        interval = interval.replace("-", ">")

        if isinstance(interval, str) and ">" in interval:
            self.interval_list.addItem(interval)  # Lägg till intervallet i listan

        else:
            print(f"[ERROR] Ogiltigt format på intervallet: {interval}")  # Debugutskrift vid fel



    def add_interval(self):
        """Lägg till ett nytt tidsintervall."""
        start_time = self.start_time_edit.time().toString("HH:mm:ss")
        end_time = self.end_time_edit.time().toString("HH:mm:ss")
        interval = f"{start_time}-{end_time}"
        self.add_interval_to_list(interval)

        # 🟢 Nollställ start- och sluttid efter att intervallet har lagts till
        self.start_time_edit.setTime(QTime(0, 0, 0))
        self.end_time_edit.setTime(QTime(0, 0, 0))

    def remove_selected_intervals(self):
        """Ta bort markerade tidsintervaller."""
        selected_items = self.interval_list.selectedItems()
        for item in selected_items:
            self.interval_list.takeItem(self.interval_list.row(item))

    def paste_intervals(self):
        """Lägg till tidsintervaller från den inklistrade texten."""
        pasted_text = self.paste_intervals_textedit.toPlainText().strip()
        lines = pasted_text.split('\n')
        for line in lines:
            if "-" in line:
                self.add_interval_to_list(line.strip())

    def save_and_close(self):
        """Spara inställningarna och stäng fönstret."""
        # Se till att intervalldata är korrekt sparad
        self.slot_data['tracklist'] = self.tracklist_combo.currentText()
        self.slot_data['group'] = self.group_combo.currentText()
        self.slot_data['pool'] = self.pool_combo.currentText()


        # Debug-utskrift innan sparning av intervaller
        print("[DEBUG] Intervaller före sparning:")
        for i in range(self.interval_list.count()):
            print(self.interval_list.item(i).text())  # Skriver ut varje intervall i listan




        self.slot_data['intervals'] = []

        # Säkerställ att varje rad innehåller ett korrekt format
        for i in range(self.interval_list.count()):
            item_text = self.interval_list.item(i).text()
            
            if ">" in item_text:  # Kontrollera att det är ett giltigt tidsintervall
                self.slot_data['intervals'].append(item_text)
                print(f"[DEBUG] Sparar intervall: {item_text}")  # Debug-utskrift
            else:
                print(f"[ERROR] Felaktigt format på intervallet: {item_text}")




    
        # Hämta valda alternativ från dropdown-menyerna
        self.slot_data['weekdays'] = self.weekday_combo.get_selected()
        self.slot_data['months'] = self.month_combo.get_selected()
        self.slot_data['weeks'] = self.week_combo.get_selected()
        self.slot_data['years'] = self.year_combo.get_selected()

        # Hämta start- och stop-sekunder samt minuter från slot_data
        self.slot_data["start_second"] = self.slot_data.get("start_second", "0")
        self.slot_data["stop_second"] = self.slot_data.get("stop_second", "*")
        self.slot_data["start_minute"] = self.slot_data.get("start_minute", "0")
        self.slot_data["stop_minute"] = self.slot_data.get("stop_minute", "*")

        # Debugutskrift för att se vad tidväljaren returnerar
        print(f"[DEBUG] start_time_edit: {self.start_time_edit.time().toString('HH:mm:ss')}, "
            f"end_time_edit: {self.end_time_edit.time().toString('HH:mm:ss')}")


        self.slot_data["start_time"] = self.start_time_edit.time().hour()
        self.slot_data["end_time"] = self.end_time_edit.time().hour()

        # Debugutskrift för att se vad som sparas i slot_data
        print(f"[DEBUG] Sparar start_time: {self.slot_data['start_time']}, end_time: {self.slot_data['end_time']}")

        


        # Hämta val från GUI
        selected_weekdays = self.weekday_combo.get_selected()
        selected_months = self.month_combo.get_selected()
        selected_weeks = self.week_combo.get_selected()
        selected_years = self.year_combo.get_selected()

        # Endast spara om användaren har gjort faktiska val, annars behåll tidigare värden
        if selected_weekdays and selected_weekdays != ["*"]:
            self.slot_data["weekdays"] = selected_weekdays
        if selected_months and selected_months != ["*"]:
            self.slot_data["months"] = selected_months
        if selected_weeks and selected_weeks != ["*"]:
            self.slot_data["weeks"] = selected_weeks
        if selected_years and selected_years != ["*"]:
            self.slot_data["years"] = selected_years



        print("[DEBUG] Sparar följande intervaller i slot_data['intervals']:")
        for i in range(self.interval_list.count()):
            print(self.interval_list.item(i).text())  # Skriver ut intervallen i rätt format

            




        # Anropa on_save() om den är definierad
        if callable(self.on_save):
            print("[DEBUG] on_save() anropas från save_and_close()")
            self.on_save()

        self.close()



    def update_intervals(self, new_intervals):
        """Uppdatera tidsintervall-listan i SlotWindow med redigerade tider och spara."""
        self.interval_list.clear()  # Rensa gamla intervaller
        for interval in new_intervals:
            self.add_interval_to_list(interval)  # Lägg till de nya intervallerna

        # Uppdatera self.slot_data så att ändringarna sparas
        self.slot_data["intervals"] = new_intervals

        # Kontrollera att on_save() anropas korrekt
        if callable(self.on_save):
            print("[DEBUG] on_save anropas för att spara uppdaterade intervaller.")
            self.on_save()

    def open_previous_slot(self):
        """Öppna föregående Slot i listan."""
        print("[DEBUG] open_previous_slot() anropad")  # Felsökning

        if hasattr(self, "main_window") and self.main_window:
            slot_names = list(self.main_window.slot_data.keys())  # Hämta alla slot-namn
            current_slot_name = self.label.text().replace("Slot: ", "") if self.label.text() else None

            if current_slot_name in slot_names:
                current_index = slot_names.index(current_slot_name)
                if current_index > 0:  # Finns en föregående Slot?
                    prev_slot_name = slot_names[current_index - 1]
                    print(f"[DEBUG] Öppnar föregående Slot: {prev_slot_name}")
                    self.switch_to_slot(prev_slot_name)

    def open_next_slot(self):
        """Öppna nästa Slot i listan."""
        print("[DEBUG] open_next_slot() anropad")  # Felsökning

        if hasattr(self, "main_window") and self.main_window:
            slot_names = list(self.main_window.slot_data.keys())  # Hämta alla slot-namn
            current_slot_name = self.label.text().replace("Slot: ", "") if self.label.text() else None

            if current_slot_name in slot_names:
                current_index = slot_names.index(current_slot_name)
                if current_index < len(slot_names) - 1:  # Finns en nästa Slot?
                    next_slot_name = slot_names[current_index + 1]
                    print(f"[DEBUG] Öppnar nästa Slot: {next_slot_name}")
                    self.switch_to_slot(next_slot_name)

    def switch_to_slot(self, new_slot_name):
        """Stäng aktuell Slot och öppna en ny."""
        print(f"[DEBUG] switch_to_slot() anropad med: {new_slot_name}")  # Felsökning

        if not hasattr(self, "main_window") or not self.main_window:
            print("[ERROR] self.main_window saknas i SlotWindow!")
            return

        if new_slot_name not in self.main_window.slot_data:
            print(f"[ERROR] Slot '{new_slot_name}' finns inte i slot_data!")
            return

        print(f"[DEBUG] Sparar och stänger nuvarande Slot: {self.label.text().replace('Slot: ', '')}")
        self.save_and_close()  # Spara och stäng nuvarande Slot

        print(f"[DEBUG] Försöker öppna ny Slot: {new_slot_name}")
        self.main_window.open_slot_window(new_slot_name)  # Öppna ny slot


    def open_progress_window(self):
        from ProgressWindow import ProgressWindow
        self.progress_window = ProgressWindow(self)  # Skicka self som förälder
        self.progress_window.show()
        # Flytta fönstret om du vill, t.ex.:
        main_geo = self.geometry()
        x = main_geo.x() + main_geo.width() + 20
        y = main_geo.y() + 200
        self.progress_window.move(x, y)


    def open_time_settings(self):
        """Öppna popup-fönstret för sekund- och minutinställningar."""
        self.time_adjustment_window = TimeAdjustmentWindow(self, self.slot_data)
        self.time_adjustment_window.exec_()  # Öppna fönstret modalt
        






class TimeAdjustmentWindow(QDialog):
    """Popup-fönster för att välja start- och stop-sekunder samt minuter."""

    from PyQt5.QtGui import QIntValidator
    from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout

    def __init__(self, parent, slot_data):
        super().__init__(parent)
        self.setWindowTitle("Tidsinställningar")
        self.setFixedSize(350, 200)  # Justerat fönsterstorleken för bättre layout
        self.setStyleSheet("background-color: #5C4033; color: white; font-size: 14px;")

        self.slot_data = slot_data
        layout = QVBoxLayout(self)

        # Skapa en stil för inmatningsfälten
        input_style = """
            QLineEdit {
                background-color: #3E2723;
                color: white;
                border: 1px solid #FFD180;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
                text-align: center;
                width: 60px;
            }
            QLabel {
                font-weight: bold;
                padding-bottom: 8px;
            }
        """

        # Skapa en validator för att tillåta endast siffror mellan 0-59
        validator = QIntValidator(0, 59, self)

        # 🟢 Start- och stop-sekund i en rad med etiketter ovanför
        sec_layout = QHBoxLayout()

        sec_start_layout = QVBoxLayout()
        self.start_second_edit = QLineEdit(self)
        self.start_second_edit.setPlaceholderText("0-59")
        self.start_second_edit.setValidator(validator)
        self.start_second_edit.setStyleSheet(input_style)
        sec_start_layout.addWidget(QLabel("Start-sekund:"))
        sec_start_layout.addWidget(self.start_second_edit)

        sec_stop_layout = QVBoxLayout()
        self.stop_second_edit = QLineEdit(self)
        self.stop_second_edit.setPlaceholderText("0-59")
        self.stop_second_edit.setValidator(validator)
        self.stop_second_edit.setStyleSheet(input_style)
        sec_stop_layout.addWidget(QLabel("Stop-sekund:"))
        sec_stop_layout.addWidget(self.stop_second_edit)

        sec_layout.addLayout(sec_start_layout)
        sec_layout.addLayout(sec_stop_layout)
        
        layout.addLayout(sec_layout)

        # 🟢 Start- och stop-minut i en rad med etiketter ovanför
        min_layout = QHBoxLayout()

        min_start_layout = QVBoxLayout()
        self.start_minute_edit = QLineEdit(self)
        self.start_minute_edit.setPlaceholderText("0-59")
        self.start_minute_edit.setValidator(validator)
        self.start_minute_edit.setStyleSheet(input_style)
        min_start_layout.addWidget(QLabel("Start-minut:"))
        min_start_layout.addWidget(self.start_minute_edit)

        min_stop_layout = QVBoxLayout()
        self.stop_minute_edit = QLineEdit(self)
        self.stop_minute_edit.setPlaceholderText("0-59")
        self.stop_minute_edit.setValidator(validator)
        self.stop_minute_edit.setStyleSheet(input_style)
        min_stop_layout.addWidget(QLabel("Stop-minut:"))
        min_stop_layout.addWidget(self.stop_minute_edit)

        min_layout.addLayout(min_start_layout)
        min_layout.addLayout(min_stop_layout)
        
        layout.addLayout(min_layout)

        # 🟢 Knapp för att spara
        save_button = QPushButton("✅ Spara och Stäng", self)
        save_button.setStyleSheet("background-color: #FFD180; color: black; font-weight: bold; padding: 8px; border-radius: 5px;")
        save_button.clicked.connect(self.save_and_close)
        layout.addWidget(save_button)

        self.load_settings()




    def load_settings(self):
        """Ladda befintliga inställningar i fälten."""
        self.start_second_edit.setText(self.slot_data.get("start_second", ""))
        self.stop_second_edit.setText(self.slot_data.get("stop_second", ""))
        self.start_minute_edit.setText(self.slot_data.get("start_minute", ""))
        self.stop_minute_edit.setText(self.slot_data.get("stop_minute", ""))

    def save_and_close(self):
        """Spara start- och stop-sekunder samt minuter och stäng fönstret."""
        self.slot_data["start_second"] = self.start_second_edit.text().strip() or "0"
        self.slot_data["stop_second"] = self.stop_second_edit.text().strip() or "*"
        self.slot_data["start_minute"] = self.start_minute_edit.text().strip() or "0"
        self.slot_data["stop_minute"] = self.stop_minute_edit.text().strip() or "*"

        self.accept()  # Stänger fönstret


    









from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QLabel
from datetime import datetime
from PyQt5.QtWidgets import QPushButton  # Flytta hit om det inte fungerar högst upp
from PyQt5.QtWidgets import QHeaderView



class ExportWindow(QDialog):
    """Fönster för att visa och redigera tidsintervaller och pauser."""

    def __init__(self, slot_name, intervals, slot_window):
        super().__init__()
        self.setWindowTitle(f"Redigera Tidsintervaller - {slot_name}")
        self.resize(600, 550)
        self.setStyleSheet("background-color: #333333; color: white;")

        self.slot_window = slot_window  # Hämta referens till SlotWindow

        layout = QVBoxLayout(self)

        # Lägg till en rubrik med slot-namnet
        self.title_label = QLabel(f"Tidsslot: {slot_name}")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(self.title_label)

        # Skapa en tabell med två kolumner
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Speltid", "Speltid (min)", "Paus", "Paus (min)"])
        self.table.setStyleSheet("background-color: #222222; color: white;")
        layout.addWidget(self.table)

        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)


        # Anpassa kolumnbredden
        self.table.setColumnWidth(0, 290)  # Speltid (vänster)
        self.table.setColumnWidth(1, 290)  # Paus (höger)
        self.table.horizontalHeader().setStretchLastSection(False)

        # Tillåt redigering
        self.table.setEditTriggers(QTableWidget.AllEditTriggers)

        # Lägg till data i tabellen
        self.populate_table(intervals)


        # PROGRESS IKON
        from PyQt5.QtWidgets import QPushButton, QStyle

        self.progress_button = QPushButton()
        icon = self.style().standardIcon(QStyle.SP_MediaVolume)  # Du kan byta till annan ikon
        self.progress_button.setIcon(icon)
        self.progress_button.setFixedSize(32, 32)
        self.progress_button.setStyleSheet("border: none;")
        self.progress_button.clicked.connect(self.open_progress_window)
        layout.addWidget(self.progress_button)



        # Lägg till en "Spara"-knapp
        save_button = QPushButton("Spara")
        save_button.setStyleSheet("background-color: #228B22; color: white;")
        save_button.clicked.connect(self.save_changes)
        layout.addWidget(save_button)

        # Lägg till en "Stäng"-knapp
        close_button = QPushButton("Stäng")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

    def populate_table(self, intervals):
        """Fyll tabellen med tidsintervaller, pauser och minuter."""
        if not intervals:
            self.table.setRowCount(1)
            self.table.setItem(0, 0, QTableWidgetItem("Inga intervaller"))
            return

        self.table.setRowCount(len(intervals))

        last_end_time = None  # Håller koll på när senaste intervallet slutade

        for row, interval in enumerate(intervals):
            interval = interval.replace(">", "-")
            if "-" not in interval:
                print(f"[ERROR] Ogiltigt intervallformat: {interval}")
                continue

            try:
                start_time, end_time = interval.split("-")

                # Sätt speltid (klockslag)
                self.table.setItem(row, 0, QTableWidgetItem(interval))

                # Beräkna och sätt speltid i minuter
                play_minutes = self.calculate_minutes(start_time, end_time)
                self.table.setItem(row, 1, QTableWidgetItem(str(play_minutes)))

                # Om ett föregående intervall finns, beräkna paus
                if last_end_time:
                    pause_start, pause_end = self.calculate_pause_times(last_end_time, start_time)
                    pause_text = f"{pause_start} - {pause_end}"
                    self.table.setItem(row - 1, 2, QTableWidgetItem(pause_text))

                    # Beräkna och sätt paus i minuter
                    pause_minutes = self.calculate_minutes(last_end_time, start_time)
                    self.table.setItem(row - 1, 3, QTableWidgetItem(str(pause_minutes)))

                last_end_time = end_time  # Uppdatera senaste sluttiden

            except ValueError:
                print(f"[ERROR] Kunde inte dela upp intervallet korrekt: {interval}")
                continue

        # Sista raden ska ha "-" för paus och paustid
        if len(intervals) > 0:
            self.table.setItem(len(intervals) - 1, 2, QTableWidgetItem("-"))
            self.table.setItem(len(intervals) - 1, 3, QTableWidgetItem("-"))




    def calculate_pause_times(self, end_time, next_start):
        """Beräkna paustiden och returnera start och sluttid som klockslag."""
        time_format = "%H:%M:%S"
        end_dt = datetime.strptime(end_time, time_format)
        start_dt = datetime.strptime(next_start, time_format)

        return end_dt.strftime(time_format), start_dt.strftime(time_format)
    
    def calculate_minutes(self, start, end):
        """Beräkna antal minuter mellan två tider."""
        time_format = "%H:%M:%S"
        start_dt = datetime.strptime(start, time_format)
        end_dt = datetime.strptime(end, time_format)
        delta = end_dt - start_dt
        return int(delta.total_seconds() // 60)  # Returnera minuter (avrundat nedåt)


    def save_changes(self):
        """Spara redigerade tider och uppdatera SlotWindow."""
        self.table.clearFocus()  # Säkerställ att alla redigeringar sparas
        self.table.setCurrentCell(-1, -1)  # Avmarkera alla celler

        new_intervals = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.text().strip():
                new_intervals.append(item.text().strip())

        # Skicka de nya tiderna till SlotWindow
        self.slot_window.update_intervals(new_intervals)
        self.close()


    def open_progress_window(self):
        from ProgressWindow import ProgressWindow
        self.progress_window = ProgressWindow(self)  # Skicka self som förälder
        self.progress_window.show()
        # Flytta fönstret om du vill, t.ex.:
        main_geo = self.geometry()
        x = main_geo.x() + main_geo.width() + 20
        y = main_geo.y() + 200
        self.progress_window.move(x, y)

    




    
        

    
        



import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QPushButton, QLineEdit, QInputDialog, QSlider
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMenu
from PyQt5.QtGui import QPalette, QColor, QPixmap
from settings_window import SettingsWindow
from PyQt5.QtWidgets import QPushButton  # Flytta hit om det inte fungerar högst upp



class MainWindow(QMainWindow):

    import os

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Eyra Soundscape Manager")
        self.setGeometry(100, 100, 1100, 780)

        # Kontrollera och skapa bankstrukturen vid start
        ensure_bank_structure()

        # Använd en mörkbrun bakgrund för huvudfönstret
        self.setStyleSheet("""
            QMainWindow { background-color: #5C4033; }  /* Mörkbrun bakgrundsfärg för huvudfönstret */
            """)

        # Skapa en widget och layout för huvudfönstret
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)

        # Tracklist-sektionen
        tracklist_layout = QVBoxLayout()
        layout.addLayout(tracklist_layout)
        self.tracklist_input = QLineEdit()
        self.tracklist_input.setPlaceholderText("Namn på ny tracklist")
        tracklist_layout.addWidget(self.tracklist_input)
        self.tracklist_input.returnPressed.connect(self.add_tracklist)
        self.add_tracklist_button = QPushButton("Skapa Tracklist")
        self.add_tracklist_button.clicked.connect(self.add_tracklist)
        tracklist_layout.addWidget(self.add_tracklist_button)
        self.tracklist_list = QListWidget()
        self.tracklist_list.setSelectionMode(QAbstractItemView.ExtendedSelection)  # Tillåt multival
        self.tracklist_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tracklist_list.customContextMenuRequested.connect(self.show_tracklist_context_menu)
        self.tracklist_list.setDragDropMode(QAbstractItemView.InternalMove)  # Aktivera omordning
        self.tracklist_list.model().rowsMoved.connect(self.sync_tracklist_data)
        tracklist_layout.addWidget(self.tracklist_list)
        self.tracklist_list.itemDoubleClicked.connect(self.open_tracklist_window)
        self.load_tracklist_button = QPushButton("Ladda Tracklist")
        self.load_tracklist_button.clicked.connect(self.load_tracklist_from_bank)
        tracklist_layout.addWidget(self.load_tracklist_button)

        


                # Initialisera datastrukturer
        self.tracklist_data = {}  # För tracklists
        self.group_data = {}      # För grupper
        self.pool_data = {}       # För pools
        self.slot_data = {}       # För slots
        self.tracklist_windows = {}  # Hantera öppna Tracklist-fönster



        # Group-sektionen
        group_layout = QVBoxLayout()
        layout.addLayout(group_layout)
        self.group_input = QLineEdit()
        self.group_input.setPlaceholderText("Namn på ny Group")
        group_layout.addWidget(self.group_input)
        self.group_input.returnPressed.connect(self.add_group)
        self.add_group_button = QPushButton("Skapa Group")
        self.add_group_button.clicked.connect(self.add_group)
        group_layout.addWidget(self.add_group_button)
        self.group_list = QListWidget()
        self.group_list.setSelectionMode(QListWidget.SingleSelection)
        self.group_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.group_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.group_list.model().rowsMoved.connect(self.sync_group_data)
        self.group_list.customContextMenuRequested.connect(self.show_group_context_menu)
        group_layout.addWidget(self.group_list)
        self.load_group_button = QPushButton("Ladda Group")
        self.load_group_button.clicked.connect(self.load_group_from_bank)
        group_layout.addWidget(self.load_group_button)
        self.group_list.itemDoubleClicked.connect(self.open_group_window)

        # Pool-sektionen
        pool_layout = QVBoxLayout()
        layout.addLayout(pool_layout)
        self.pool_input = QLineEdit()
        self.pool_input.setPlaceholderText("Namn på ny Pool")
        pool_layout.addWidget(self.pool_input)
        self.pool_input.returnPressed.connect(self.add_pool)
        self.add_pool_button = QPushButton("Skapa Pool")
        self.add_pool_button.clicked.connect(self.add_pool)
        pool_layout.addWidget(self.add_pool_button)
        self.pool_list = QListWidget()
        self.pool_list.setSelectionMode(QListWidget.SingleSelection)
        self.pool_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.pool_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.pool_list.model().rowsMoved.connect(self.sync_pool_data)
        self.pool_list.customContextMenuRequested.connect(self.show_pool_context_menu)
        pool_layout.addWidget(self.pool_list)
        self.load_pool_button = QPushButton("Ladda Pool")
        self.load_pool_button.clicked.connect(self.load_pool_from_bank)
        pool_layout.addWidget(self.load_pool_button)
        self.pool_list.itemDoubleClicked.connect(self.open_pool_window)

        # Slot-sektionen
        slot_layout = QVBoxLayout()
        layout.addLayout(slot_layout)
        self.slot_input = QLineEdit()
        self.slot_input.setPlaceholderText("Namn på ny Slot")
        slot_layout.addWidget(self.slot_input)
        self.slot_input.returnPressed.connect(self.add_slot)
        self.add_slot_button = QPushButton("Skapa Slot")
        self.add_slot_button.clicked.connect(self.add_slot)
        slot_layout.addWidget(self.add_slot_button)
        self.slot_list = QListWidget()
        self.slot_list.setSelectionMode(QListWidget.SingleSelection)
        self.slot_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.slot_list.customContextMenuRequested.connect(self.show_slot_context_menu)
        self.slot_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.slot_list.model().rowsMoved.connect(self.sync_slot_data)
        slot_layout.addWidget(self.slot_list)
        self.load_slot_button = QPushButton("Ladda Slot")
        self.load_slot_button.clicked.connect(self.load_slot_from_bank)
        slot_layout.addWidget(self.load_slot_button)
        self.slot_list.itemDoubleClicked.connect(self.open_slot_window)

        self.current_file_path = None  # För att hålla koll på den aktuella filen

        self.installEventFilter(self)

        self.create_file_menu()

        self.create_settings_menu()



        self.create_master_section(layout)

        



    

    from PyQt5.QtWidgets import QColorDialog

    def change_item_color(self, list_widget):
        """Ändra bakgrundsfärg på markerad post i listwidget."""
        selected_item = list_widget.currentItem()
        if selected_item:
            # Öppna färgdialog och låt användaren välja färg
            color = QColorDialog.getColor()
            if color.isValid():
                selected_item.setBackground(color)
                # Spara färg i data om det är en tracklist, group, pool eller slot
                list_name = selected_item.text()
                if list_widget == self.tracklist_list:
                    self.tracklist_data[list_name]["color"] = color.name()
                elif list_widget == self.group_list:
                    self.group_data[list_name]["color"] = color.name()
                elif list_widget == self.pool_list:
                    self.pool_data[list_name]["color"] = color.name()
                elif list_widget == self.slot_list:
                    self.slot_data[list_name]["color"] = color.name()

        
    def load_list_with_colors(self, list_widget, data):
        """Ladda objekt och färger i listan."""
        list_widget.clear()
        for name, item_data in data.items():
            item = QListWidgetItem(name)

            # 🔽 Lägg till tooltip baserat på _source
            source = item_data.get("_source")
            if source == "ProjectFolder":
                item.setToolTip("Importerad från projektmapp")
            elif source == "SavedBank":
                item.setToolTip("Importerad från SavedBank")
            else:
                item.setToolTip("Skapad i projektet")

            # 🔽 Sätt färg om tillgänglig
            try:
                if "color" in item_data and item_data["color"]:
                    item.setBackground(QColor(item_data["color"]))
            except Exception as e:
                print(f"Fel vid laddning av färg för '{name}': {e}")

            list_widget.addItem(item)

        

    def add_tracklist(self):
        """Lägg till en ny tracklist till listan och synkronisera datan."""
        tracklist_name = self.tracklist_input.text().strip()

        # Validera att namnet inte är tomt eller en dubblett
        if not tracklist_name:
            QMessageBox.warning(self, "Ogiltigt namn", "Tracklistens namn kan inte vara tomt.")
            return
        if tracklist_name in self.tracklist_data:
            QMessageBox.warning(self, "Dubblett", "En tracklist med detta namn finns redan.")
            return

        # Uppdatera GUI och data
        item = QListWidgetItem(tracklist_name)
        item.setToolTip("Skapad i projektet")
        self.tracklist_list.addItem(item)

        # Lägg till standardvärden för tracklisten
        self.tracklist_data[tracklist_name] = {
            'volume': 0.1,          # Standardvolym
            'primary_group': None,  # Ingen huvudgrupp initialt
            'groups': []            # Tom lista över tillhörande grupper
        }
        self.tracklist_input.clear()
        print(f"Ny tracklist tillagd: {tracklist_name}")


    def load_tracklist_from_bank(self):
        """Fråga användaren om en eller flera tracklists ska laddas."""
        msg = QMessageBox()
        msg.setWindowTitle("Välj hur du vill ladda")
        msg.setText("Vill du ladda en enskild tracklist eller alla från en mapp?")
        load_one = msg.addButton("Ladda en", QMessageBox.AcceptRole)
        load_all = msg.addButton("Ladda flera", QMessageBox.AcceptRole)
        msg.addButton("Avbryt", QMessageBox.RejectRole)
        msg.exec_()

        if msg.clickedButton() == load_one:
            self.load_single_tracklist_from_bank()
        elif msg.clickedButton() == load_all:
            self.load_all_tracklists_from_bank()



    def load_single_tracklist_from_bank(self):
        """Ladda en enskild Tracklist från banken."""
        bank_folder = os.path.join("SavedBank", "Tracklists")
        if not os.path.exists(bank_folder):
            QMessageBox.warning(self, "Ingen bank", "Det finns inga sparade Tracklists.")
            return

        files = sorted([f for f in os.listdir(bank_folder) if f.endswith(".json")])
        if not files:
            QMessageBox.warning(self, "Tom bank", "Det finns inga sparade Tracklists.")
            return

        selected_file, ok = QInputDialog.getItem(self, "Ladda Tracklist", "Välj en Tracklist:", files, editable=False)
        if ok and selected_file:
            self._add_tracklist_from_file(os.path.join(bank_folder, selected_file))
            



    def load_all_tracklists_from_bank(self):
        """Låt användaren välja flera Tracklists att ladda in."""
        bank_folder = os.path.join("SavedBank", "Tracklists")
        if not os.path.exists(bank_folder):
            QMessageBox.warning(self, "Ingen bank", "Det finns inga sparade Tracklists.")
            return

        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Välj en eller flera Tracklists att ladda",
            bank_folder,
            "JSON-filer (*.json)"
        )

        if not files:
            return  # Användaren avbröt

        laddade = 0
        for file_path in files:
            self._add_tracklist_from_file(file_path)
            laddade += 1

        QMessageBox.information(self, "Tracklists inlästa", f"{laddade} tracklists har laddats.")



    def _add_tracklist_from_file(self, file_path):
        """Lägg till en tracklist i projektet från en .json-fil."""
        with open(file_path, "r") as file:
            tracklist_data = json.load(file)
            tracklist_data["_source"] = "SavedBank"


        # Se till att gamla versioner fungerar
        if "primary_group" not in tracklist_data:
            tracklist_data["primary_group"] = None
        if "groups" not in tracklist_data:
            tracklist_data["groups"] = []

        # Undvik dubbletter i namnet
        tracklist_name = os.path.splitext(os.path.basename(file_path))[0]
        original_name = tracklist_name
        counter = 1
        while tracklist_name in self.tracklist_data:
            tracklist_name = f"{original_name}_{counter}"
            counter += 1

        self.tracklist_data[tracklist_name] = tracklist_data
        item = QListWidgetItem(tracklist_name)
        item.setToolTip("Importerad från SavedBank/Tracklists")
        self.tracklist_list.addItem(item)

        print(f"Tracklist '{tracklist_name}' har laddats från {file_path}")



    def add_group(self):
        """Skapa en ny grupp och lägg till den i gruppdatan."""
        group_name = self.group_input.text().strip()

        # Validera att namnet inte är tomt eller en dubblett
        if not group_name:
            QMessageBox.warning(self, "Ogiltigt namn", "Gruppens namn kan inte vara tomt.")
            return
        if group_name in self.group_data:
            QMessageBox.warning(self, "Dubblett", "En grupp med detta namn finns redan.")
            return

        # Lägg till gruppen i GUI och data
        item = QListWidgetItem(group_name)
        item.setToolTip("Skapad i projektet")
        self.group_list.addItem(item)

        self.group_data[group_name] = {'tracklists': [], 'groups': [], 'tracklists_data': {}}  # Initiera tracklists_data
        self.group_input.clear()
        print(f"Ny grupp tillagd: {group_name}")


    def sync_group_data(self):
        """Synkronisera group_data med den aktuella ordningen i group_list."""
        new_order = [self.group_list.item(i).text() for i in range(self.group_list.count())]
        self.group_data = {name: self.group_data[name] for name in new_order}



    def load_group_from_bank(self):
        """Fråga användaren om en eller flera grupper ska laddas."""
        msg = QMessageBox()
        msg.setWindowTitle("Välj hur du vill ladda grupper")
        msg.setText("Vill du ladda en enskild Group eller flera?")
        load_one = msg.addButton("Ladda en", QMessageBox.AcceptRole)
        load_many = msg.addButton("Ladda flera", QMessageBox.AcceptRole)
        msg.addButton("Avbryt", QMessageBox.RejectRole)
        msg.exec_()

        if msg.clickedButton() == load_one:
            self.load_single_group_from_bank()
        elif msg.clickedButton() == load_many:
            self.load_multiple_groups_from_bank()





    def load_single_group_from_bank(self):
        """Ladda en Group från banken."""
        bank_folder = os.path.join("SavedBank", "Groups")
        if not os.path.exists(bank_folder):
            QMessageBox.warning(self, "Ingen bank", "Det finns inga sparade Groups.")
            return

        files = sorted([f for f in os.listdir(bank_folder) if f.endswith(".json")])
        if not files:
            QMessageBox.warning(self, "Tom bank", "Det finns inga sparade Groups.")
            return

        selected_file, ok = QInputDialog.getItem(self, "Ladda Group", "Välj en Group:", files, editable=False)
        if ok and selected_file:
            file_path = os.path.join(bank_folder, selected_file)
            with open(file_path, "r") as file:
                group_data = json.load(file)
                group_data["_source"] = "SavedBank"


            group_name = os.path.splitext(selected_file)[0]
            group_name = self.generate_unique_name(group_name)

            self.group_data[group_name] = group_data
            item = QListWidgetItem(group_name)
            item.setToolTip("Importerad från SavedBank/Groups")
            self.group_list.addItem(item)

            print(f"Group '{group_name}' har laddats från banken.")



    def load_multiple_groups_from_bank(self):
        """Låt användaren välja flera Groups att ladda in."""
        bank_folder = os.path.join("SavedBank", "Groups")
        if not os.path.exists(bank_folder):
            QMessageBox.warning(self, "Ingen bank", "Det finns inga sparade Groups.")
            return

        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Välj en eller flera Groups att ladda",
            bank_folder,
            "JSON-filer (*.json)"
        )

        if not files:
            return  # Användaren avbröt

        laddade = 0
        for file_path in files:
            with open(file_path, "r") as file:
                group_data = json.load(file)
                group_data["_source"] = "SavedBank"


            group_name = os.path.splitext(os.path.basename(file_path))[0]
            group_name = self.generate_unique_name(group_name)  # Generera unikt namn

            self.group_data[group_name] = group_data
            item = QListWidgetItem(group_name)
            item.setToolTip("Importerad från SavedBank/Groups")
            self.group_list.addItem(item)

            print(f"Group '{group_name}' har laddats från {file_path}")
            laddade += 1

        QMessageBox.information(self, "Groups inlästa", f"{laddade} grupper har laddats.")
            



    def add_pool(self):
        """Lägg till en ny Pool till listan och datastrukturen."""
        pool_name = self.pool_input.text().strip()

        # Validera att namnet inte är tomt
        if not pool_name:
            QMessageBox.warning(self, "Ogiltigt namn", "Poolens namn kan inte vara tomt.")
            return

        # Generera ett unikt namn
        pool_name = self.generate_unique_name(pool_name)

        # Uppdatera GUI och data
        item = QListWidgetItem(pool_name)
        item.setToolTip("Skapad i projektet")
        self.pool_list.addItem(item)

        self.pool_data[pool_name] = {"tracklists": [], "groups": [], "randomize": False}
        self.pool_input.clear()
        print(f"Ny Pool tillagd: {pool_name}")

    def sync_pool_data(self):
        """Synkronisera pool_data med den aktuella ordningen i pool_list."""
        new_order = [self.pool_list.item(i).text() for i in range(self.pool_list.count())]
        self.pool_data = {name: self.pool_data[name] for name in new_order}




    def load_pool_from_bank(self):
        """Fråga användaren om en eller flera Pools ska laddas."""
        msg = QMessageBox()
        msg.setWindowTitle("Välj hur du vill ladda pools")
        msg.setText("Vill du ladda en enskild Pool eller flera?")
        load_one = msg.addButton("Ladda en", QMessageBox.AcceptRole)
        load_many = msg.addButton("Ladda flera", QMessageBox.AcceptRole)
        msg.addButton("Avbryt", QMessageBox.RejectRole)
        msg.exec_()

        if msg.clickedButton() == load_one:
            self.load_single_pool_from_bank()
        elif msg.clickedButton() == load_many:
            self.load_multiple_pools_from_bank()




    def load_single_pool_from_bank(self):
        """Ladda en Pool från banken."""
        bank_folder = os.path.join("SavedBank", "Pools")
        if not os.path.exists(bank_folder):
            QMessageBox.warning(self, "Ingen bank", "Det finns inga sparade Pools.")
            return

        files = sorted([f for f in os.listdir(bank_folder) if f.endswith(".json")])
        if not files:
            QMessageBox.warning(self, "Tom bank", "Det finns inga sparade Pools.")
            return

        selected_file, ok = QInputDialog.getItem(self, "Ladda Pool", "Välj en Pool:", files, editable=False)
        if ok and selected_file:
            file_path = os.path.join(bank_folder, selected_file)
            with open(file_path, "r") as file:
                pool_data = json.load(file)
                pool_data["_source"] = "SavedBank"


            pool_name = os.path.splitext(selected_file)[0]
            pool_name = self.generate_unique_name(pool_name)

            self.pool_data[pool_name] = pool_data
            item = QListWidgetItem(pool_name)
            item.setToolTip("Importerad från SavedBank/Pools")
            self.pool_list.addItem(item)

            print(f"Pool '{pool_name}' har laddats från banken.")



    def load_multiple_pools_from_bank(self):
        """Låt användaren välja flera Pools att ladda in."""
        bank_folder = os.path.join("SavedBank", "Pools")
        if not os.path.exists(bank_folder):
            QMessageBox.warning(self, "Ingen bank", "Det finns inga sparade Pools.")
            return

        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Välj en eller flera Pools att ladda",
            bank_folder,
            "JSON-filer (*.json)"
        )

        if not files:
            return

        laddade = 0
        for file_path in files:
            with open(file_path, "r") as file:
                pool_data = json.load(file)
                pool_data["_source"] = "SavedBank"


            pool_name = os.path.splitext(os.path.basename(file_path))[0]
            pool_name = self.generate_unique_name(pool_name)

            self.pool_data[pool_name] = pool_data
            item = QListWidgetItem(pool_name)
            item.setToolTip("Importerad från SavedBank/Pools")
            self.pool_list.addItem(item)

            print(f"Pool '{pool_name}' har laddats från {file_path}")
            laddade += 1

        QMessageBox.information(self, "Pools inlästa", f"{laddade} pools har laddats.")




    def add_slot(self):
        """Lägg till en ny Slot till listan och datastrukturen."""
        slot_name = self.slot_input.text().strip()

        # Validera att namnet inte är tomt
        if not slot_name:
            QMessageBox.warning(self, "Ogiltigt namn", "Slotens namn kan inte vara tomt.")
            return

        # Generera ett unikt namn
        slot_name = self.generate_unique_name(slot_name)

        # Uppdatera GUI och data
        item = QListWidgetItem(slot_name)
        item.setToolTip("Skapad i projektet")
        self.slot_list.addItem(item)

        self.slot_data[slot_name] = {
            "intervals": [],
            "tracklist": None,
            "group": None,
            "pool": None,
            "loop": False,
            "randomize": False,
        }
        self.slot_input.clear()
        print(f"Ny Slot tillagd: {slot_name}")

    def sync_slot_data(self):
        """Synkronisera slot_data med den aktuella ordningen i slot_list."""
        new_order = [self.slot_list.item(i).text() for i in range(self.slot_list.count())]
        self.slot_data = {name: self.slot_data[name] for name in new_order}




    def load_slot_from_bank(self):
        """Fråga användaren om en eller flera Slots ska laddas."""
        msg = QMessageBox()
        msg.setWindowTitle("Välj hur du vill ladda slots")
        msg.setText("Vill du ladda en enskild Slot eller flera?")
        load_one = msg.addButton("Ladda en", QMessageBox.AcceptRole)
        load_many = msg.addButton("Ladda flera", QMessageBox.AcceptRole)
        msg.addButton("Avbryt", QMessageBox.RejectRole)
        msg.exec_()

        if msg.clickedButton() == load_one:
            self.load_single_slot_from_bank()
        elif msg.clickedButton() == load_many:
            self.load_multiple_slots_from_bank()



    def load_single_slot_from_bank(self):
        """Ladda en Slot från banken."""
        bank_folder = os.path.join("SavedBank", "Slots")
        if not os.path.exists(bank_folder):
            QMessageBox.warning(self, "Ingen bank", "Det finns inga sparade Slots.")
            return

        files = sorted([f for f in os.listdir(bank_folder) if f.endswith(".json")])
        if not files:
            QMessageBox.warning(self, "Tom bank", "Det finns inga sparade Slots.")
            return

        selected_file, ok = QInputDialog.getItem(self, "Ladda Slot", "Välj en Slot:", files, editable=False)
        if ok and selected_file:
            file_path = os.path.join(bank_folder, selected_file)
            with open(file_path, "r") as file:
                slot_data = json.load(file)
                slot_data["_source"] = "SavedBank"


            slot_name = os.path.splitext(selected_file)[0]
            slot_name = self.generate_unique_name(slot_name)

            self.slot_data[slot_name] = slot_data
            item = QListWidgetItem(slot_name)
            item.setToolTip("Importerad från SavedBank/Slots")
            self.slot_list.addItem(item)

            print(f"Slot '{slot_name}' har laddats från banken.")



    def load_multiple_slots_from_bank(self):
        """Låt användaren välja flera Slots att ladda in."""
        bank_folder = os.path.join("SavedBank", "Slots")
        if not os.path.exists(bank_folder):
            QMessageBox.warning(self, "Ingen bank", "Det finns inga sparade Slots.")
            return

        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Välj en eller flera Slots att ladda",
            bank_folder,
            "JSON-filer (*.json)"
        )

        if not files:
            return

        laddade = 0
        for file_path in files:
            with open(file_path, "r") as file:
                slot_data = json.load(file)
                slot_data["_source"] = "SavedBank"


            slot_name = os.path.splitext(os.path.basename(file_path))[0]
            slot_name = self.generate_unique_name(slot_name)

            self.slot_data[slot_name] = slot_data
            item = QListWidgetItem(slot_name)
            item.setToolTip("Importerad från SavedBank/Slots")
            self.slot_list.addItem(item)

            print(f"Slot '{slot_name}' har laddats från {file_path}")
            laddade += 1

        QMessageBox.information(self, "Slots inlästa", f"{laddade} slots har laddats.")
            
            



    def generate_unique_name(self, base_name):
        """
        Generera ett unikt namn för en ny Tracklist, Group, Pool eller Slot.
        Det säkerställer att namnet är unikt över alla kategorier.
        """
        # Kombinera alla namn från de olika kategorierna
        all_names = set(self.tracklist_data.keys()) | set(self.group_data.keys()) | \
                    set(self.pool_data.keys()) | set(self.slot_data.keys())

        # Om basnamnet redan är unikt, returnera det
        if base_name not in all_names:
            return base_name

        # Annars generera ett unikt namn genom att lägga till en siffra
        counter = 1
        new_name = f"{base_name}_{counter}"
        while new_name in all_names:
            counter += 1
            new_name = f"{base_name}_{counter}"

        return new_name
        


    from PyQt5.QtWidgets import QFileDialog
    
    def save_project(self):
        """Spara projekt till den aktuella filen om den finns, annars öppna 'Save As'-fönstret."""
        if self.current_file_path:
            # Spara direkt till den senaste använda filbanan
            self._save_to_file(self.current_file_path)
            # Uppdatera listan över nyligen använda projekt
            self.update_recent_projects(self.current_file_path)
      
            self.update_window_title()  # Uppdatera titel
        else:
            # Öppna 'Save As'-fönstret om ingen fil är sparad ännu
            self.save_project_as()


           

    def save_project_as(self):
        """Öppnar en 'Spara som'-dialog och sparar projektet till vald plats."""
        default_folder = '/Users/stefanbackas/Documents/000_EYRA/Eyra_Soundscapes/Eyra Manager Filer'
        file_path, _ = QFileDialog.getSaveFileName(self, "Spara Projekt Som", default_folder, "JSON Files (*.json)")
        if file_path:
            self._save_to_file(file_path)
            self.current_file_path = file_path
            # Uppdatera listan över nyligen använda projekt
            self.update_recent_projects(file_path)
    
            self.update_window_title()  # Uppdatera titel
            print(f"Projekt sparat till: {file_path}")


        

    def _save_to_file(self, file_path):
        """Skriv projektdata till en specifik fil."""
        # 🔽 Skapa projektmapp och undermappar
        project_folder = os.path.splitext(file_path)[0] + "_data"
        os.makedirs(os.path.join(project_folder, "Tracklists"), exist_ok=True)
        os.makedirs(os.path.join(project_folder, "Groups"), exist_ok=True)
        os.makedirs(os.path.join(project_folder, "Pools"), exist_ok=True)
        os.makedirs(os.path.join(project_folder, "Slots"), exist_ok=True)

        # Synkronisera tracklist_data innan sparning
        self.sync_tracklist_data()

        project_data = {
            "tracklists": {
                name: {
                    **data,
                    "color": self.get_item_color(self.tracklist_list, name)
                }
                for name, data in self.tracklist_data.items()
            },
            "groups": {
                name: {
                    **data,
                    "color": self.get_item_color(self.group_list, name)
                }
                for name, data in self.group_data.items()
            },
            "pools": {
                name: {
                    **data,
                    "color": self.get_item_color(self.pool_list, name)
                }
                for name, data in self.pool_data.items()
            },
            "slots": {
                name: {
                    **data,
                    "color": self.get_item_color(self.slot_list, name)
                }
                for name, data in self.slot_data.items()
            },
            "master_volume": self.master_volume_slider.value()
        }
        with open(file_path, "w") as file:
            json.dump(project_data, file, indent=4)

        # 🔽 Spara varje enhet som enskild fil i projektmappen
        for name, data in self.tracklist_data.items():
            filepath = os.path.splitext(file_path)[0] + "_data/Tracklists/" + name + ".json"
            with open(filepath, "w") as f:
                json.dump(data, f, indent=4)

        for name, data in self.group_data.items():
            filepath = os.path.splitext(file_path)[0] + "_data/Groups/" + name + ".json"
            with open(filepath, "w") as f:
                json.dump(data, f, indent=4)

        for name, data in self.pool_data.items():
            filepath = os.path.splitext(file_path)[0] + "_data/Pools/" + name + ".json"
            with open(filepath, "w") as f:
                json.dump(data, f, indent=4)

        for name, data in self.slot_data.items():
            filepath = os.path.splitext(file_path)[0] + "_data/Slots/" + name + ".json"
            with open(filepath, "w") as f:
                json.dump(data, f, indent=4)
            

        # Uppdatera listan över nyligen använda projekt
        self.update_recent_projects(file_path)
        self.current_file_path = file_path  # Uppdatera aktuell filväg
        self.update_window_title()  # Uppdatera titel
        print(f"Projekt sparat: {file_path}")



    
       

    def load_project(self):
        """Ladda ett projekt från en JSON-fil."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Ladda Projekt", "", "JSON Files (*.json)")
        if file_path:
            # Läs in data från JSON-filen
            with open(file_path, "r") as file:
                project_data = json.load(file)

            project_folder = os.path.splitext(file_path)[0] + "_data"

            # Återställ all data från huvudfilen (för att få med master_volume och färger)
            self.tracklist_data = project_data.get("tracklists", {})
            self.group_data = project_data.get("groups", {})
            self.pool_data = project_data.get("pools", {})
            self.slot_data = project_data.get("slots", {})

            # Importera enheter från projektmapp (ersätter ev. objekt från huvudfilen)
            import glob

            # Tracklists
            tracklist_path = os.path.join(project_folder, "Tracklists", "*.json")
            for path in glob.glob(tracklist_path):
                name = os.path.splitext(os.path.basename(path))[0]
                with open(path, "r") as f:
                    self.tracklist_data[name] = json.load(f)
                    self.tracklist_data[name]["_source"] = "ProjectFolder"

            # Groups
            group_path = os.path.join(project_folder, "Groups", "*.json")
            for path in glob.glob(group_path):
                name = os.path.splitext(os.path.basename(path))[0]
                with open(path, "r") as f:
                    self.group_data[name] = json.load(f)
                    self.group_data[name]["_source"] = "ProjectFolder"

            # Pools
            pool_path = os.path.join(project_folder, "Pools", "*.json")
            for path in glob.glob(pool_path):
                name = os.path.splitext(os.path.basename(path))[0]
                with open(path, "r") as f:
                    self.pool_data[name] = json.load(f)
                    self.pool_data[name]["_source"] = "ProjectFolder"

            # Slots
            slot_path = os.path.join(project_folder, "Slots", "*.json")
            for path in glob.glob(slot_path):
                name = os.path.splitext(os.path.basename(path))[0]
                with open(path, "r") as f:
                    self.slot_data[name] = json.load(f)
                    self.slot_data[name]["_source"] = "ProjectFolder"

            # Återställ mastervolym
            self.master_volume_slider.setValue(project_data.get("master_volume", 100))

            # Återställ listor i GUI med rätt färg och tooltip
            self.load_list_with_colors(self.tracklist_list, self.tracklist_data)
            self.load_list_with_colors(self.group_list, self.group_data)
            self.load_list_with_colors(self.pool_list, self.pool_data)
            self.load_list_with_colors(self.slot_list, self.slot_data)

            # Spara sökvägen och uppdatera fönstertitel
            self.current_file_path = file_path
            self.update_window_title()
            self.update_recent_projects(file_path)

            print("Projekt laddat:", file_path)



    def load_project_from_path(self, file_path):
        """Ladda ett projekt direkt från en given filväg."""
        try:
            # Läs in data från JSON-filen
            with open(file_path, "r") as file:
                project_data = json.load(file)

            project_folder = os.path.splitext(file_path)[0] + "_data"

            # Återställ all data från huvudfilen
            self.tracklist_data = project_data.get("tracklists", {})
            self.group_data = project_data.get("groups", {})
            self.pool_data = project_data.get("pools", {})
            self.slot_data = project_data.get("slots", {})

            # Importera enheter från projektmapp
            import glob

            # Tracklists
            tracklist_path = os.path.join(project_folder, "Tracklists", "*.json")
            for path in glob.glob(tracklist_path):
                name = os.path.splitext(os.path.basename(path))[0]
                with open(path, "r") as f:
                    self.tracklist_data[name] = json.load(f)
                    self.tracklist_data[name]["_source"] = "ProjectFolder"

            # Groups
            group_path = os.path.join(project_folder, "Groups", "*.json")
            for path in glob.glob(group_path):
                name = os.path.splitext(os.path.basename(path))[0]
                with open(path, "r") as f:
                    self.group_data[name] = json.load(f)
                    self.group_data[name]["_source"] = "ProjectFolder"

            # Pools
            pool_path = os.path.join(project_folder, "Pools", "*.json")
            for path in glob.glob(pool_path):
                name = os.path.splitext(os.path.basename(path))[0]
                with open(path, "r") as f:
                    self.pool_data[name] = json.load(f)
                    self.pool_data[name]["_source"] = "ProjectFolder"

            # Slots
            slot_path = os.path.join(project_folder, "Slots", "*.json")
            for path in glob.glob(slot_path):
                name = os.path.splitext(os.path.basename(path))[0]
                with open(path, "r") as f:
                    self.slot_data[name] = json.load(f)
                    self.slot_data[name]["_source"] = "ProjectFolder"

            # Återställ mastervolym
            self.master_volume_slider.setValue(project_data.get("master_volume", 100))

            # Återställ listor i GUI
            self.load_list_with_colors(self.tracklist_list, self.tracklist_data)
            self.load_list_with_colors(self.group_list, self.group_data)
            self.load_list_with_colors(self.pool_list, self.pool_data)
            self.load_list_with_colors(self.slot_list, self.slot_data)

            # Uppdatera övrigt
            self.current_file_path = file_path
            self.update_window_title()

            print("Projekt laddat:", file_path)

        except Exception as e:
            QMessageBox.critical(self, "Fel", f"Kunde inte läsa projektfilen.\n{e}")

            


    def update_recent_projects(self, project_path):
        """Lägg till ett projekt i listan över nyligen använda projekt."""
        recent_file = "recent_projects.json"  # Fil där vi sparar nyligen använda projekt
        try:
            # Läs befintlig lista
            if os.path.exists(recent_file):
                with open(recent_file, 'r') as file:
                    recent_projects = json.load(file)
            else:
                recent_projects = []

            # Uppdatera listan (undvik dubbletter och begränsa antalet)
            if project_path in recent_projects:
                recent_projects.remove(project_path)
            recent_projects.insert(0, project_path)  # Lägg till överst
            recent_projects = recent_projects[:10]  # Behåll de senaste 10 projekten

            # Spara tillbaka till fil
            with open(recent_file, 'w') as file:
                json.dump(recent_projects, file)
        except Exception as e:
            print(f"Fel vid uppdatering av nyligen använda projekt: {e}")

    def show_recent_projects(self):
        """Visa en lista över nyligen använda projekt."""
        recent_file = "recent_projects.json"
        try:
            if os.path.exists(recent_file):
                with open(recent_file, 'r') as file:
                    recent_projects = json.load(file)
            else:
                recent_projects = []

            if not recent_projects:
                QMessageBox.information(self, "Inga projekt", "Det finns inga nyligen använda projekt.")
                return

            # Skapa en dialog för att visa projekten
            selected_project, ok = QInputDialog.getItem(
                self, "Nyligen använda projekt", "Välj ett projekt:", recent_projects, editable=False
            )

            if ok and selected_project:
                self.load_project_from_path(selected_project)  # Använd rätt metod för att ladda projektet
        except Exception as e:
            QMessageBox.critical(self, "Fel", f"Kunde inte läsa nyligen använda projekt.\n{e}")

        
        
    

    def open_tracklist_window(self, tracklist_name=None):
        """Öppna ett Tracklist-fönster för redigering. Kan anropas från lista eller navigeringspilar."""

        # Om tracklist_name är None, försök hämta den från den valda listan
        if tracklist_name is None:
            selected_item = self.tracklist_list.currentItem()
            if not selected_item:
                QMessageBox.warning(self, "Ingen Tracklist Vald", "Välj en Tracklist att öppna.")
                return
            tracklist_name = selected_item.text()  # Hämta texten korrekt

        # Om tracklist_name fortfarande är en QListWidgetItem, konvertera det till text
        if isinstance(tracklist_name, QListWidgetItem):
            tracklist_name = tracklist_name.text()

        print(f"Försöker öppna Tracklist: {tracklist_name}")

        if tracklist_name not in self.tracklist_data:
            QMessageBox.critical(self, "Fel", f"Tracklisten '{tracklist_name}' finns inte i data.")
            return


        # Kontrollera om fönstret redan är öppet
        if tracklist_name in self.tracklist_windows:
            self.tracklist_windows[tracklist_name].activateWindow()
            return

        # Synkronisera volymen
        group_name = self.tracklist_data[tracklist_name].get('primary_group')
        if group_name and group_name in self.group_data:
            group_volume = self.group_data[group_name].get('volume', 1.0)
            original_volume = self.group_data[group_name]['tracklists_data'][tracklist_name]['original_volume']
            self.tracklist_data[tracklist_name]['volume'] = round(original_volume * group_volume, 3)

        # Skapa och öppna TracklistWindow
        tracklist_data = self.tracklist_data[tracklist_name]
        tracklist_window = TracklistWindow(
            tracklist_name,
            tracklist_data,
            self.save_tracklist_data,
            main_window=self
        )
        tracklist_window.closed.connect(self.on_close_tracklist)
        tracklist_window.show()
        self.tracklist_windows[tracklist_name] = tracklist_window




    def on_close_tracklist(self, tracklist_name):
        """Ta bort Tracklist-fönstret från listan när det stängs."""
        if tracklist_name in self.tracklist_windows:
            del self.tracklist_windows[tracklist_name]
            print(f"[DEBUG] Tracklist '{tracklist_name}' fönster har stängts.")




    def open_group_window(self, group_name=None):
        """Öppna ett GroupWindow för redigering. Kan anropas från lista eller navigeringspilar."""

        # Om group_name är None, försök hämta det från den valda listan
        if group_name is None:
            selected_item = self.group_list.currentItem()
            if not selected_item:
                QMessageBox.warning(self, "Ingen Grupp Vald", "Välj en Grupp att öppna.")
                return
            group_name = selected_item.text()  # Hämta texten från QListWidgetItem

        elif isinstance(group_name, QListWidgetItem):
            group_name = group_name.text()  # Om det är ett QListWidgetItem, hämta texten

        print(f"Försöker öppna Grupp: {group_name}")

        if not isinstance(group_name, str):
            QMessageBox.critical(self, "Fel", "Ogiltigt gruppnamn.")
            return

        if group_name not in self.group_data:
            QMessageBox.critical(self, "Fel", f"Gruppen '{group_name}' finns inte i data.")
            return

        # Kontrollera om fönstret redan är öppet
        if hasattr(self, "group_window") and self.group_window and self.group_window.isVisible():
            self.group_window.close()  # Stäng det nuvarande fönstret innan vi öppnar ett nytt

        available_tracklists = list(self.tracklist_data.keys())  # Hämta alla tillgängliga tracklists
        available_groups = [name for name in self.group_data.keys() if name != group_name]  # Exkludera den aktuella gruppen

        # Skapa och öppna GroupWindow
        self.group_window = GroupWindow(
            group_name,
            self.group_data[group_name],
            available_tracklists,
            available_groups,
            self.save_group_data,
            main_window=self  # Skicka en referens till MainWindow
        )
        self.group_window.show()





    def open_pool_window(self, pool_name=None):
        """Öppna ett fönster för en pool. Kan anropas från lista eller navigeringspilar."""

        # Om pool_name är None, försök hämta det från den valda listan
        if pool_name is None:
            selected_item = self.pool_list.currentItem()
            if not selected_item:
                QMessageBox.warning(self, "Ingen Pool Vald", "Välj en Pool att öppna.")
                return
            pool_name = selected_item.text()  # Hämta texten från QListWidgetItem

        elif isinstance(pool_name, QListWidgetItem):
            pool_name = pool_name.text()  # Om det är ett QListWidgetItem, hämta texten

        print(f"Försöker öppna Pool: {pool_name}")

        if not isinstance(pool_name, str):
            QMessageBox.critical(self, "Fel", "Ogiltigt pool-namn.")
            return

        if pool_name not in self.pool_data:
            QMessageBox.critical(self, "Fel", f"Poolen '{pool_name}' finns inte i data.")
            return

        # Kontrollera om fönstret redan är öppet
        if hasattr(self, "pool_window") and self.pool_window and self.pool_window.isVisible():
            self.pool_window.close()  # Stäng det nuvarande fönstret innan vi öppnar ett nytt

        # Skapa och öppna PoolWindow
        self.pool_window = PoolWindow(self, pool_name, self.pool_data[pool_name], self.save_pool_data)
        self.pool_window.show()



    def open_slot_window(self, slot_name=None):
        """Öppna ett fönster för en Slot. Kan anropas från lista eller navigeringspilar."""

        # Om slot_name är None, försök hämta det från den valda listan
        if slot_name is None:
            selected_item = self.slot_list.currentItem()
            if not selected_item:
                QMessageBox.warning(self, "Ingen Slot Vald", "Välj en Slot att öppna.")
                return
            slot_name = selected_item.text()  # Hämta texten från QListWidgetItem

        # Om slot_name fortfarande är ett QListWidgetItem, konvertera det till text
        elif isinstance(slot_name, QListWidgetItem):
            slot_name = slot_name.text()

        print(f"Försöker öppna Slot: {slot_name}")

        # Lägg till en extra säkerhetskontroll
        if not isinstance(slot_name, str) or slot_name.strip() == "":
            QMessageBox.critical(self, "Fel", "Ogiltigt slot-namn.")
            return

        if slot_name not in self.slot_data:
            QMessageBox.critical(self, "Fel", f"Sloten '{slot_name}' finns inte i data.")
            return

        # Kontrollera om fönstret redan är öppet
        if hasattr(self, "slot_window") and self.slot_window and self.slot_window.isVisible():
            self.slot_window.close()  # Stäng det nuvarande fönstret innan vi öppnar ett nytt

        # Skapa och öppna SlotWindow
        self.slot_window = SlotWindow(
            slot_name,
            self.slot_data[slot_name],
            list(self.tracklist_data.keys()),  # Tillgängliga tracklists
            list(self.group_data.keys()),      # Tillgängliga grupper
            list(self.pool_data.keys()),       # Tillgängliga pools
            self.save_slot_data,
            main_window=self  # Se till att main_window skickas in!
        )

        self.slot_window.show()
        self.slot_window.raise_()
        self.slot_window.activateWindow()







    # Spara data
    def save_tracklist_data(self):
        """Funktion för att spara uppdaterade Tracklist-data."""
        selected_item = self.tracklist_list.currentItem()
        if selected_item:
            tracklist_name = selected_item.text()
            tracklist_data = self.tracklist_data[tracklist_name]

            if tracklist_data.get("_source") == "SavedBank":
                self.statusBar().showMessage(f"⚠️ Tracklisten '{tracklist_name}' kommer från SavedBank och kan inte sparas direkt.", 5000)  # Visas i 5 sekunder
            else:
                self.save_to_bank("Tracklists", tracklist_name, tracklist_data)
                self.statusBar().showMessage(f"Tracklist '{tracklist_name}' sparad.", 3000)  # Visas i 3 sekunder

            print("Tracklist-data uppdaterad:", self.tracklist_data)




    def save_group_data(self):
        """Funktion för att spara uppdaterade Group-data."""
        selected_item = self.group_list.currentItem()
        if selected_item:
            group_name = selected_item.text()
            group_data = self.group_data[group_name]
            
            # Spara i banken
            if group_data.get("_source") == "SavedBank":
                QMessageBox.warning(self, "Skyddad", f"Gruppen '{group_name}' kommer från SavedBank och kan inte sparas direkt.")
            else:
                self.save_to_bank("Groups", group_name, group_data)

            
            print(f"[DEBUG] Group-data sparad för '{group_name}': {group_data}")



    def save_pool_data(self):
        """Funktion för att spara uppdaterade Pool-data."""
        selected_item = self.pool_list.currentItem()
        if selected_item:
            pool_name = selected_item.text()
            pool_data = self.pool_data[pool_name]
            
            # Spara i banken
            if pool_data.get("_source") == "SavedBank":
                QMessageBox.warning(self, "Skyddad", f"Poolen '{pool_name}' kommer från SavedBank och kan inte sparas direkt.")
            else:
                self.save_to_bank("Pools", pool_name, pool_data)

            
            print("Pool-data uppdaterad:", self.pool_data)


    def save_slot_data(self):
        """Funktion för att spara uppdaterade Slot-data."""
        selected_item = self.slot_list.currentItem()
        if selected_item:
            slot_name = selected_item.text()
            slot_data = self.slot_data[slot_name]
            
            # Spara i banken
            if slot_data.get("_source") == "SavedBank":
                QMessageBox.warning(self, "Skyddad", f"Sloten '{slot_name}' kommer från SavedBank och kan inte sparas direkt.")
            else:
                self.save_to_bank("Slots", slot_name, slot_data)

            
            print("Slot-data uppdaterad:", self.slot_data)


    def get_item_color(self, list_widget, item_name):
        """Hämta färgen för ett objekt i listan."""
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            if item.text() == item_name:
                color = item.background().color()
                return color.name() if color.isValid() else None
        return None        

    def update_window_title(self):
        """Uppdatera fönstrets titel med det aktuella filnamnet."""
        base_title = "Eyra Soundscape Manager"
        if self.current_file_path:
            file_name = os.path.basename(self.current_file_path)
            self.setWindowTitle(f"{base_title} - {file_name}")
        else:
            self.setWindowTitle(base_title)


    # Skapa Master-sektionen
    def create_master_section(self, layout):
        """Skapa Master-sektionen med Save, Load, Export etc., med enhetlig design."""
        from PyQt5.QtWidgets import QPushButton, QLabel, QSlider, QHBoxLayout, QVBoxLayout
        
        master_layout = QVBoxLayout()
        layout.addLayout(master_layout)

        # Gemensam stil för alla knappar
        button_style = """
            QPushButton {
                background-color: #80a48c;  /* Olivgrön färg */
                color: white;
                border-radius: 5px;
                padding: 6px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #6B8E23;  /* Lite ljusare grön vid hover */
            }
        """

        # Skapa och lägga till knappar med samma stil
        buttons = [
            #("Save", self.save_project),
            #("Save As", self.save_project_as),
            #("Load", self.load_project),
            #("Recent Projects", self.show_recent_projects),
            ("Export", self.export_project),
            #("Validera exportstruktur", self.validate_export_structure_before_export),
            #("Rensa All Data", self.clear_all_data),
            #("Inställningar", self.open_settings_window),
            ("Progress Window", self.open_progress_window)
        ]

        for text, function in buttons:
            button = QPushButton(text)
            button.setFixedSize(150, 20)
            button.setStyleSheet(button_style)
            button.clicked.connect(function)
            master_layout.addWidget(button)



        #validate_button = QPushButton("Validera projektstruktur")
        #validate_button.setFixedSize(150, 20)
        #validate_button.setStyleSheet(button_style)
        #validate_button.clicked.connect(self.validate_project_structure)
        #master_layout.addWidget(validate_button)

       # Knapp för att starta Eyra Player
        eyra_player_button = QPushButton("Starta Eyra Player")
        eyra_player_button.setFixedSize(150, 20)
        eyra_player_button.setStyleSheet(button_style)
        eyra_player_button.clicked.connect(self.open_eyra_player_window)
        master_layout.addWidget(eyra_player_button)


            

        # **Master Volume**
        master_volume_label = QLabel("Master Volume")
        master_layout.addWidget(master_volume_label)

        volume_layout = QHBoxLayout()

        self.master_volume_slider = QSlider(Qt.Horizontal)
        self.master_volume_slider.setMinimum(0)
        self.master_volume_slider.setMaximum(100)
        self.master_volume_slider.setValue(100)
        self.master_volume_slider.valueChanged.connect(self.update_master_volume_label)
        volume_layout.addWidget(self.master_volume_slider)

        self.master_volume_value_label = QLabel("100")
        volume_layout.addWidget(self.master_volume_value_label)

        master_layout.addLayout(volume_layout)


        



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

        master_layout.addLayout(logo_layout)  # Lägg logotypen efter volymslidern

        # Sträck layouten så att knapparna inte trycks ihop
        master_layout.addStretch()


    def update_master_volume_label(self, value):
        """Uppdatera etiketten bredvid volymslidern med det aktuella värdet."""
        self.master_volume_value_label.setText(str(value))



    # Kontextmenyer för redigering och borttagning
    def show_tracklist_context_menu(self, position):
        menu = QMenu()
        edit_action = menu.addAction("Redigera Namn")
        copy_action = menu.addAction("Kopiera Tracklist")  # Nytt menyval
        delete_action = menu.addAction("Ta bort Tracklist")
        color_action = menu.addAction("Välj färg")

        action = menu.exec_(self.tracklist_list.viewport().mapToGlobal(position))
        if action == edit_action:
            self.edit_tracklist()
        elif action == copy_action:
            self.copy_tracklist()  # Anropa kopieringsfunktionen
        elif action == delete_action:
            self.delete_tracklist()
        elif action == color_action:
            self.change_item_color(self.tracklist_list)



    def show_group_context_menu(self, position):
        menu = QMenu()
        edit_action = menu.addAction("Redigera Group")
        delete_action = menu.addAction("Ta bort Group")
        color_action = menu.addAction("Välj färg")

        action = menu.exec_(self.group_list.viewport().mapToGlobal(position))
        if action == edit_action:
            self.edit_group()
        elif action == delete_action:
            self.delete_group()
        elif action == color_action:  # Hantera färgändring
            self.change_item_color(self.group_list)    

    def show_pool_context_menu(self, position):
        menu = QMenu()
        edit_action = menu.addAction("Redigera Pool")
        delete_action = menu.addAction("Ta bort Pool")
        color_action = menu.addAction("Välj färg")

        action = menu.exec_(self.pool_list.viewport().mapToGlobal(position))
        if action == edit_action:
            self.edit_pool()
        elif action == delete_action:
            self.delete_pool()
        elif action == color_action:  # Hantera färgändring
            self.change_item_color(self.pool_list)    

    def show_slot_context_menu(self, position):
        menu = QMenu()
        edit_action = menu.addAction("Redigera Slot")
        delete_action = menu.addAction("Ta bort Slot")
        color_action = menu.addAction("Välj färg")

        action = menu.exec_(self.slot_list.viewport().mapToGlobal(position))
        if action == edit_action:
            self.edit_slot()
        elif action == delete_action:
            self.delete_slot()
        elif action == color_action:  # Hantera färgändring
            self.change_item_color(self.slot_list)    



        

    # Redigeringsfunktioner
    def edit_tracklist(self):
        """Redigera namnet på en tracklist och synkronisera datan."""
        selected_item = self.tracklist_list.currentItem()

        # Kontrollera att något är markerat
        if not selected_item:
            QMessageBox.warning(self, "Inget markerat", "Ingen tracklist är vald för redigering.")
            return

        old_name = selected_item.text()
        new_name, ok = QInputDialog.getText(
            self, 
            "Redigera Tracklist", 
            "Nytt namn på Tracklist:", 
            QLineEdit.Normal, 
            old_name
        )

        # Validera det nya namnet
        if ok and new_name:
            new_name = new_name.strip()  # Ta bort extra mellanrum
            if new_name == old_name:
                return  # Inget ändras om namnet är detsamma
            if new_name in self.tracklist_data:
                QMessageBox.warning(self, "Dubblett", "En tracklist med detta namn finns redan.")
                return

            # Uppdatera GUI och data
            selected_item.setText(new_name)
            self.tracklist_data[new_name] = self.tracklist_data.pop(old_name)

            # Om det finns färgdata kopplat till tracklisten, uppdatera även detta
            if hasattr(self, "tracklist_colors") and old_name in self.tracklist_colors:
                self.tracklist_colors[new_name] = self.tracklist_colors.pop(old_name)

            print(f"Tracklist '{old_name}' bytt namn till '{new_name}'")
        elif ok and not new_name:
            QMessageBox.warning(self, "Ogiltigt namn", "Namnet kan inte vara tomt.")


    def copy_tracklist(self):
        selected_item = self.tracklist_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Inget markerat", "Ingen tracklist är vald för kopiering.")
            return

        old_name = selected_item.text()
        new_name, ok = QInputDialog.getText(
            self,
            "Kopiera Tracklist",
            "Nytt namn på kopian:",
            QLineEdit.Normal,
            old_name + "_copy"
        )

        if ok and new_name:
            new_name = new_name.strip()
            if new_name in self.tracklist_data:
                QMessageBox.warning(self, "Dubblett", "En tracklist med detta namn finns redan.")
                return

            # Kopiera datan
            self.tracklist_data[new_name] = self.tracklist_data[old_name].copy()

            # Skapa nytt listobjekt
            new_item = QListWidgetItem(new_name)

            # Hämta färgen från original och sätt på kopian
            original_color = self.get_item_color(self.tracklist_list, old_name)
            if original_color:
                new_item.setBackground(QColor(original_color))

            new_item.setToolTip("Kopia av " + old_name)
            self.tracklist_list.addItem(new_item)
            print(f"Tracklist '{old_name}' kopierad till '{new_name}'")

                



    def edit_group(self):
        """Redigera namnet på en vald grupp."""
        selected_item = self.group_list.currentItem()

        # Kontrollera att något är markerat
        if not selected_item:
            QMessageBox.warning(self, "Inget valt", "Välj en grupp att redigera.")
            return

        old_name = selected_item.text()
        new_name, ok = QInputDialog.getText(
            self, "Redigera Grupp", "Nytt namn på grupp:", QLineEdit.Normal, old_name
        )

        # Validera det nya namnet
        if ok and new_name:
            new_name = new_name.strip()
            if new_name == old_name:
                return
            if new_name in self.group_data:
                QMessageBox.warning(self, "Dubblett", "En grupp med detta namn finns redan.")
                return

            # Uppdatera GUI och data
            selected_item.setText(new_name)
            self.group_data[new_name] = self.group_data.pop(old_name)

            print(f"Gruppen '{old_name}' bytt namn till '{new_name}'")
        elif ok and not new_name:
            QMessageBox.warning(self, "Ogiltigt namn", "Namnet kan inte vara tomt.")





    def edit_pool(self):
        """Redigera namn på markerad Pool."""
        selected_item = self.pool_list.currentItem()
        if selected_item:
            old_name = selected_item.text()
            
            # Be användaren om ett nytt namn
            new_name, ok = QInputDialog.getText(
                self,
                "Redigera Pool",
                "Nytt namn på Pool:",
                QLineEdit.Normal,
                old_name
            )
            if ok and new_name and new_name != old_name:
                if new_name in self.pool_data:
                    QMessageBox.warning(self, "Fel", "En pool med detta namn finns redan.")
                    return
                
                # Uppdatera GUI
                selected_item.setText(new_name)
                
                # Uppdatera datastrukturen
                self.pool_data[new_name] = self.pool_data.pop(old_name)
                
                print(f"Pool redigerad: {old_name} → {new_name}")
            else:
                print("Redigering avbruten eller ogiltigt namn.")



    def edit_slot(self):
        """Redigera namn på markerad Slot."""
        selected_item = self.slot_list.currentItem()
        if selected_item:
            old_name = selected_item.text()
            
            # Be användaren om ett nytt namn
            new_name, ok = QInputDialog.getText(
                self,
                "Redigera Slot",
                "Nytt namn på Slot:",
                QLineEdit.Normal,
                old_name
            )
            if ok and new_name and new_name != old_name:
                if new_name in self.slot_data:
                    QMessageBox.warning(self, "Fel", "En slot med detta namn finns redan.")
                    return
                
                # Uppdatera GUI
                selected_item.setText(new_name)
                
                # Uppdatera datastrukturen
                self.slot_data[new_name] = self.slot_data.pop(old_name)
                
                print(f"Slot redigerad: {old_name} → {new_name}")
            else:
                print("Redigering avbruten eller ogiltigt namn.")


    def sync_group_data(self):
        """Synkronisera group_data med den aktuella ordningen i group_list."""
        new_order = [self.group_list.item(i).text() for i in range(self.group_list.count())]
        self.group_data = {name: self.group_data[name] for name in new_order}

    def sync_pool_data(self):
        """Synkronisera pool_data med den aktuella ordningen i pool_list."""
        new_order = [self.pool_list.item(i).text() for i in range(self.pool_list.count())]
        self.pool_data = {name: self.pool_data[name] for name in new_order}

    def sync_slot_data(self):
        """Synkronisera slot_data med den aktuella ordningen i slot_list."""
        new_order = [self.slot_list.item(i).text() for i in range(self.slot_list.count())]
        self.slot_data = {name: self.slot_data[name] for name in new_order}
            



    # Borttagningsfunktioner
    def delete_tracklist(self):
        """Ta bort markerad tracklist från listan och synkronisera datan."""
        selected_item = self.tracklist_list.currentItem()

        # Kontrollera att något är markerat
        if not selected_item:
            QMessageBox.warning(self, "Inget markerat", "Ingen tracklist är vald för borttagning.")
            return

        # Hämta tracklistens namn och bekräfta borttagning
        tracklist_name = selected_item.text()
        reply = QMessageBox.question(
            self,
            "Bekräfta borttagning",
            f"Är du säker på att du vill ta bort tracklisten '{tracklist_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            # Uppdatera GUI och data
            self.tracklist_list.takeItem(self.tracklist_list.row(selected_item))
            if tracklist_name in self.tracklist_data:
                del self.tracklist_data[tracklist_name]
            print(f"Tracklist borttagen: {tracklist_name}")



    def delete_group(self):
        """Ta bort markerad grupp från listan och datan."""
        selected_item = self.group_list.currentItem()

        if not selected_item:
            QMessageBox.warning(self, "Inget valt", "Välj en grupp att ta bort.")
            return

        group_name = selected_item.text()

        # Bekräftelse innan borttagning
        reply = QMessageBox.question(
            self,
            "Bekräfta borttagning",
            f"Är du säker på att du vill ta bort gruppen '{group_name}'? Detta kan inte ångras.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Ta bort från GUI och data
            self.group_list.takeItem(self.group_list.row(selected_item))
            if group_name in self.group_data:
                del self.group_data[group_name]
            print(f"Gruppen '{group_name}' har tagits bort.")



    def delete_pool(self):
        """Ta bort markerad Pool från listan och datastrukturen."""
        selected_item = self.pool_list.currentItem()
        if selected_item:
            pool_name = selected_item.text()
            
            # Bekräfta borttagning
            reply = QMessageBox.question(
                self,
                "Bekräfta borttagning",
                f"Vill du verkligen ta bort poolen '{pool_name}'? Detta kan inte ångras.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                # Ta bort från GUI
                self.pool_list.takeItem(self.pool_list.row(selected_item))
                
                # Ta bort från datastrukturen
                if pool_name in self.pool_data:
                    del self.pool_data[pool_name]
                
                print(f"Pool borttagen: {pool_name}")



    def delete_slot(self):
        """Ta bort markerad Slot från listan och datastrukturen."""
        selected_item = self.slot_list.currentItem()
        if selected_item:
            slot_name = selected_item.text()
            
            # Bekräfta borttagning
            reply = QMessageBox.question(
                self,
                "Bekräfta borttagning",
                f"Vill du verkligen ta bort sloten '{slot_name}'? Detta kan inte ångras.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                # Ta bort från GUI
                self.slot_list.takeItem(self.slot_list.row(selected_item))
                
                # Ta bort från datastrukturen
                if slot_name in self.slot_data:
                    del self.slot_data[slot_name]
                
                print(f"Slot borttagen: {slot_name}")

    def keyPressEvent(self, event):
        """Hantera tangenttryckningar i MainWindow, men låt andra fönster hantera sina egna events."""
        print(f"Tangentkod: {event.key()}, Modifiers: {int(event.modifiers())}")  # Debug-utskrift

        is_mac = sys.platform == 'darwin'  # Kontrollera om vi kör på macOS

        if is_mac and int(event.modifiers()) == 67108864 and event.key() == Qt.Key_Backspace:
            print("Cmd+Backspace aktiverat")  # Debug
            self.delete_selected_tracklists()
        elif event.key() == Qt.Key_Delete:
            print("Delete aktiverat")  # Debug
            self.delete_selected_tracklists()
        else:
            # Om tangenttrycket inte hanteras, skicka det vidare
            super().keyPressEvent(event)



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

    def sync_tracklist_data(self):
        """Synkronisera tracklist_data med den aktuella ordningen i tracklist_list."""
        new_order = []
        for i in range(self.tracklist_list.count()):
            item_text = self.tracklist_list.item(i).text()
            new_order.append(item_text)
        
        # Bevara endast de poster som finns i den nya ordningen
        self.tracklist_data = {name: self.tracklist_data[name] for name in new_order}



    def on_close_tracklist(self, tracklist_name):
        """Ta bort Tracklist-fönstret från listan när det stängs."""
        if tracklist_name in self.tracklist_windows:
            del self.tracklist_windows[tracklist_name]
            print(f"Tracklist '{tracklist_name}' fönster har stängts.")



    def open_settings_window(self):
        self.settings_window = SettingsWindow()
        self.settings_window.exec_()  # Öppnar inställningsfönstret som en modal dialog
        
        
        
            



    import json
    from PyQt5.QtWidgets import QFileDialog, QMessageBox
    from ProjectValidator import validate_exported_project_structure

    def export_project(self):
        """Exportera projektdata till en specifik JSON-struktur."""

        # 1. Förhandsvalidera
        export_data_temp = {
            "tracklists": self.tracklist_data,
            "groups": self.group_data,
            "pools": self.pool_data,
            "slots": self.slot_data
        }
        errors, warnings = validate_exported_project_structure(export_data_temp)

        # 2. Försök rensa ogiltiga referenser
        if hasattr(self, "clean_invalid_references"):
            self.clean_invalid_references()

        # 3. Validera på nytt efter rensning
        export_data_temp = {
            "tracklists": self.tracklist_data,
            "groups": self.group_data,
            "pools": self.pool_data,
            "slots": self.slot_data
        }
        errors, warnings = validate_exported_project_structure(export_data_temp)

        # 4. Visa fel och varningar
        if errors:
            QMessageBox.critical(self, "Fel vid export", "Export avbruten p.g.a. icke-rensbara fel:\n\n" + "\n".join(errors))
            return
        elif warnings:
            QMessageBox.warning(self, "Varningar vid export", "⚠️ Följande varningar hittades:\n\n" + "\n".join(warnings))

        # 5. Dialog för att spara export
        default_folder = '/Users/stefanbackas/Documents/000_EYRA/Eyra_Soundscapes/Designed_Soundscapes'
        file_path, _ = QFileDialog.getSaveFileName(self, "Exportera Projekt", default_folder, "JSON Files (*.json)")
        if not file_path:
            return

        # 6. Bygg exportdata
        soundscapes = []
        timeslots = []

        for tracklist_name, tracklist_data in self.tracklist_data.items():
            tracklist_entry = {
                "type": "Tracklist",
                "id": tracklist_name,
                "fadetime": tracklist_data.get('fadetime', 0),
                "slotfadetime": tracklist_data.get('slotfadetime', 0),
                "volume": round(tracklist_data.get('volume', 0), 3),
                "loop": tracklist_data.get('loop', False),
                "randomise": tracklist_data.get('randomize', False),
                "items": tracklist_data.get('files', [])
            }
            soundscapes.append(tracklist_entry)

        for group_name, group_data in self.group_data.items():
            combined_items = group_data.get('tracklists', []) + group_data.get('groups', [])
            group_entry = {
                "type": "Group",
                "id": group_name,
                "items": combined_items
            }
            soundscapes.append(group_entry)

        for pool_name, pool_data in self.pool_data.items():
            pool_entry = {
                "type": "Pool",
                "id": pool_name,
                "randomize": pool_data.get('randomize', False),
                "items": pool_data.get('tracklists', []) + pool_data.get('groups', [])
            }
            soundscapes.append(pool_entry)

        for slot_name, slot_data in self.slot_data.items():
            item = slot_data.get('tracklist')
            if item == "Ingen":
                item = slot_data.get('group')
            if item == "Ingen":
                item = slot_data.get('pool')
            if item == "Ingen":
                item = None

            timeslot_entry = {
                "id": slot_name,
                "type": slot_data.get("type", "Timeslot"),
                "slotexpression": self.format_slot_expression(
                    slot_data.get('intervals', []),
                    slot_data.get('weekdays', []),
                    slot_data.get('months', []),
                    slot_data.get('weeks', []),
                    slot_data.get('years', []),
                    slot_data
                ),
                "items": [item] if item else []
            }
            timeslots.append(timeslot_entry)

        general_settings = [{"Volume": self.master_volume_slider.value()}]

        export_data = {
            "Soundblocks": soundscapes,
            "Slots": timeslots,
            "SoundscapeSettings": general_settings
        }

        json_str = json.dumps(export_data, indent=2)
        json_str = json_str.replace('"Soundblocks":', '"Soundblocks" :')
        json_str = json_str.replace('"Slots":', '"Slots" :')
        json_str = json_str.replace('"SoundscapeSettings":', '"SoundscapeSettings" :')

        with open(file_path, "w") as file:
            file.write(json_str)

        print("Projekt exporterat:", file_path)


    def format_slot_expression(self, intervals, weekdays, months, weeks, years, slot_data):
        """
        Skapar en slotexpression-sträng i cron-format baserat på valda tider, spellängd, veckodagar, månader, veckor och år.
        """

        # 🟢 Hämta start- och stop-sekunder/minuter från slot_data
        start_second = slot_data.get("start_second", "*")
        stop_second = slot_data.get("stop_second", "*")
        start_minute = slot_data.get("start_minute", "*")
        stop_minute = slot_data.get("stop_minute", "*")

        # 🟢 Skapa tidsuttryck genom att behandla varje del separat
        def build_time_expression(start, stop):
            """ Bygger ett korrekt uttryck för sekunder eller minuter. """
            if start == "*" and stop == "*":
                return "*"
            elif start == stop:
                return start  # Om båda är samma, skriv bara ut ett värde
            else:
                return f"{start}>{stop}"  # Intervall

        time_seconds = build_time_expression(start_second, stop_second)
        time_minutes = build_time_expression(start_minute, stop_minute)

        # 🟢 Korrigera den sista biten: Om "0>*", byt ut mot "*"
        if time_seconds == "0>*":
            time_seconds = "*"
        if time_minutes == "0>*":
            time_minutes = "*"

        # 🟢 Konstruera tidsdelen av uttrycket
        time_expression = f"{time_seconds} {time_minutes}"

        # 🟢 Hantera specialval ('Vardagar' och 'Veckoslut')
        expanded_weekdays = set()
        for day in weekdays:
            if day == "Vardagar (Mån-Fre)":
                expanded_weekdays.update(["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag"])
            elif day == "Veckoslut (Lör-Sön)":
                expanded_weekdays.update(["Lördag", "Söndag"])
            else:
                expanded_weekdays.add(day)

        weekdays = list(expanded_weekdays)

        # 🟢 Konvertera veckodagar till cron-format
        weekday_mapping = {
            "Söndag": "0", "Måndag": "1", "Tisdag": "2", "Onsdag": "3",
            "Torsdag": "4", "Fredag": "5", "Lördag": "6"
        }
        sorted_weekdays = sorted([day for day in weekdays if day in weekday_mapping], key=lambda day: int(weekday_mapping[day]))
        weekdays_cron = "*" if not sorted_weekdays else ",".join(weekday_mapping[day] for day in sorted_weekdays)

        # 🟢 Konvertera månader till cron-format
        month_mapping = {
            "Januari": "1", "Februari": "2", "Mars": "3", "April": "4", "Maj": "5", "Juni": "6",
            "Juli": "7", "Augusti": "8", "September": "9", "Oktober": "10", "November": "11", "December": "12"
        }
        months_cron = "*" if "*" in months or not months else ",".join(month_mapping[m] for m in sorted(months, key=lambda m: int(month_mapping[m])))

        weeks_cron = "*" if "*" in weeks or not weeks else ",".join(sorted(weeks, key=int))
        years_cron = "*" if "*" in years or not years else ",".join(sorted(years, key=int))

        # 🟢 Formatera tidsintervall korrekt
        expressions = []
        for interval in intervals:
            if isinstance(interval, str) and ">" in interval:
                start, end = interval.split('>')
                expressions.append(f"{start}>{end}")

        if not expressions:
            expressions.append("*")

        # 🟢 Generera slotexpression
        cron_output = f"{time_expression} {','.join(expressions)} {weekdays_cron} {months_cron} {weeks_cron} {years_cron}"

        return cron_output







    def validate_export_structure_before_export(self):
        """Validera strukturen innan export."""
        # Skapa en temporär exportstruktur i minnet
        export_data = {
            "tracklists": self.tracklist_data,
            "groups": self.group_data,
            "pools": self.pool_data,
            "slots": self.slot_data
        }

        errors, warnings = validate_exported_project_structure(export_data)

        if not errors and not warnings:
            QMessageBox.information(self, "Validering slutförd", "✅ Inga problem hittades.")
        else:
            msg = "❌ Problem:\n" + "\n".join(errors) if errors else ""
            if warnings:
                msg += "\n\n⚠️ Varningar:\n" + "\n".join(warnings)
            QMessageBox.warning(self, "Valideringsresultat", msg)













    def clear_all_data(self):
        """Töm alla tracklists, groups, pools och slots efter bekräftelse."""
        reply = QMessageBox.question(
            self,
            "Bekräfta Rensning",
            "Är du säker på att du vill tömma alla Tracklists, Groups, Pools och Slots? Detta kan inte ångras.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Rensa interna datalagringsstrukturer
            self.tracklist_data.clear()
            self.group_data.clear()
            self.pool_data.clear()
            self.slot_data.clear()
            
            # Rensa GUI-listorna
            self.tracklist_list.clear()
            self.group_list.clear()
            self.pool_list.clear()
            self.slot_list.clear()
            
            # Återställ andra relaterade element (t.ex. mastervolym)
            self.master_volume_slider.setValue(100)
            
            QMessageBox.information(self, "Rensning Utförd", "All data har rensats.")

    from PyQt5.QtCore import QEvent

    def eventFilter(self, source, event):
        """Övervaka alla tangenttryckningar och musklick."""
        if event.type() == QEvent.KeyPress:
            print(f"GLOBAL - Tangent tryckt: {event.key()} | Fokus: {QApplication.focusWidget()}")

        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            if not any(
                widget.geometry().contains(self.mapFromGlobal(event.globalPos())) for widget in [
                    self.tracklist_list,
                    self.group_list,
                    self.pool_list,
                    self.slot_list
                ]
            ):
                self.clear_all_selections()
        return super().eventFilter(source, event)



    def clear_all_selections(self):
        """Avmarkera alla val i listorna."""
        self.tracklist_list.clearSelection()
        self.group_list.clearSelection()
        self.pool_list.clearSelection()
        self.slot_list.clearSelection()

    def update_loaded_data(self):
        """Uppdatera äldre JSON-data till den senaste versionen."""
        # Iterera över alla grupper
        for group_name, group_data in self.group_data.items():
            if 'tracklists_data' not in group_data:
                group_data['tracklists_data'] = {}  # Lägg till nyckeln om den saknas

            for tracklist_name in group_data.get('tracklists', []):
                if tracklist_name not in group_data['tracklists_data']:
                    group_data['tracklists_data'][tracklist_name] = {
                        'original_volume': 0.1,  # Standardvärde
                        'volume': 0.1,  # Standardvolym
                        'primary_group': group_name  # Tilldela gruppen som huvudgrupp
                    }

        # Iterera över alla tracklists
        for tracklist_name, tracklist_data in self.tracklist_data.items():
            if 'primary_group' not in tracklist_data:
                tracklist_data['primary_group'] = None  # Lägg till standardvärde
            if 'groups' not in tracklist_data:
                tracklist_data['groups'] = []  # Lägg till tom lista som standard



    def open_progress_window(self):
        from ProgressWindow import ProgressWindow
        self.progress_window = ProgressWindow(self)  # Skicka self som förälder
        self.progress_window.show()
        # Flytta fönstret om du vill, t.ex.:
        main_geo = self.geometry()
        x = main_geo.x() + main_geo.width() + 20
        y = main_geo.y() + 200
        self.progress_window.move(x, y)






    from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QHBoxLayout, QMessageBox
    from ProjectValidator import validate_exported_project_structure

    def validate_project_structure(self):
        # Skapa data att validera
        export_data_temp = {
            "tracklists": self.tracklist_data,
            "groups": self.group_data,
            "pools": self.pool_data,
            "slots": self.slot_data
        }

        # Validera strukturen
        errors, warnings = validate_exported_project_structure(export_data_temp)

        if not errors and not warnings:
            QMessageBox.information(self, "Validering slutförd", "✔ Alla samband ser korrekta ut.")
            return

        # Skapa ett nytt fönster
        dialog = QDialog(self)
        dialog.setWindowTitle("Valideringsresultat")
        dialog.setMinimumSize(600, 400)

        layout = QVBoxLayout(dialog)

        label = QLabel("Resultat av valideringen:")
        layout.addWidget(label)

        # Skapa scroll-bara textfältet med både fel och varningar
        text_box = QTextEdit()
        text_box.setReadOnly(True)

        combined_messages = []
        if errors:
            combined_messages.append("❌ Fel:\n" + "\n".join(errors))
        if warnings:
            combined_messages.append("⚠️ Varningar:\n" + "\n".join(warnings))

        text_box.setText("\n\n".join(combined_messages))
        layout.addWidget(text_box)

        # Knapprad
        button_layout = QHBoxLayout()

        if errors:
            clean_button = QPushButton("Rensa ogiltiga referenser")
            clean_button.clicked.connect(lambda: [self.clean_invalid_references(), dialog.accept()])
            button_layout.addWidget(clean_button)

        close_button = QPushButton("Stäng")
        close_button.clicked.connect(dialog.reject)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

        dialog.exec_()




                    
          
    def clean_invalid_references(self):
        """Rensa ogiltiga referenser från tracklists, grupper, pooler och slots."""
        valid_tracklists = set(self.tracklist_data.keys())
        valid_groups = set(self.group_data.keys())
        valid_pools = set(self.pool_data.keys())

        # Tracklists
        for tl in self.tracklist_data.values():
            tl["groups"] = [g for g in tl.get("groups", []) if g in valid_groups]
            if "primary_group" in tl and tl["primary_group"] not in valid_groups:
                tl["primary_group"] = None

        # Groups
        for g in self.group_data.values():
            g["tracklists"] = [t for t in g.get("tracklists", []) if t in valid_tracklists]
            g["groups"] = [gr for gr in g.get("groups", []) if gr in valid_groups]

        # Pools
        for p in self.pool_data.values():
            p["tracklists"] = [t for t in p.get("tracklists", []) if t in valid_tracklists]
            p["groups"] = [g for g in p.get("groups", []) if g in valid_groups]

        # Slots
        for s in self.slot_data.values():
            t = s.get("tracklist")
            if t in ("None", None) or t not in valid_tracklists:
                s["tracklist"] = "Ingen"
            g = s.get("group")
            if g in ("None", None) or g not in valid_groups:
                s["group"] = "Ingen"
            p = s.get("pool")
            if p in ("None", None) or p not in valid_pools:
                s["pool"] = "Ingen"


    def new_file(self):
        # Bekräfta med användaren innan rensning
        reply = QMessageBox.question(
            self,
            "Nytt projekt",
            "Vill du skapa ett nytt tomt projekt? All osparad data förloras.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.tracklist_data.clear()
            self.group_data.clear()
            self.pool_data.clear()
            self.slot_data.clear()

            self.tracklist_list.clear()
            self.group_list.clear()
            self.pool_list.clear()
            self.slot_list.clear()

            self.master_volume_slider.setValue(100)

            self.current_file_path = None
            self.update_window_title()
            self.statusBar().showMessage("Nytt tomt projekt skapat.", 5000)




    def create_file_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")

        actions = [
            ("New File", self.new_file),
            ("Save", self.save_project),
            ("Save As", self.save_project_as),
            ("Load", self.load_project),
            ("Recent Projects", self.show_recent_projects),
            ("Rensa all data", self.clear_all_data),  # Här lägger vi till funktionen
        ]

        for name, func in actions:
            action = QAction(name, self)
            action.triggered.connect(func)
            file_menu.addAction(action)

                

    def create_settings_menu(self):
        menubar = self.menuBar()
        settings_menu = menubar.addMenu("Project Settings")

        open_settings_action = QAction("Open Settings", self)
        open_settings_action.triggered.connect(self.open_settings_window)
        settings_menu.addAction(open_settings_action)

        validate_action = QAction("Validate Project Structure", self)
        validate_action.triggered.connect(self.validate_project_structure)
        settings_menu.addAction(validate_action)

                        





    def open_eyra_player_window(self):
        self.eyra_player_window = EyraPlayerWindow()

        # Hämta huvudfönstrets position och storlek
        main_geo = self.geometry()
        x = main_geo.x() + main_geo.width() + 20  # 20 pixlar till höger om huvudfönstret
        y = main_geo.y()

        # Placera EyraPlayerWindow
        self.eyra_player_window.move(x, y)
        self.eyra_player_window.show()





            




    

        

    import os
    import json

    import os
    import json

    def save_to_bank(self, category, name, data):
        """Spara data till banken."""
        try:
            bank_folder = os.path.join("SavedBank", category)
            os.makedirs(bank_folder, exist_ok=True)  # Skapa mappen om den inte finns
            file_path = os.path.join(bank_folder, f"{name}.json")
            with open(file_path, "w") as file:
                json.dump(data, file, indent=4)
            print(f"{category[:-1]} '{name}' har sparats i banken.")
        except Exception as e:
            print(f"Fel vid sparning i banken: {e}")



        
        

# Skapa applikationen
app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())
