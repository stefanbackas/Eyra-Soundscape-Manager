import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QTreeView, QListWidget,
    QPushButton, QFileSystemModel, QMessageBox, QListWidgetItem, QAbstractItemView, QComboBox, QInputDialog
)
from PyQt5.QtCore import Qt, QDir
from PyQt5.QtGui import QPalette, QColor, QPixmap
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import QEvent  # Lägg till denna import om den saknas


print("This is FileOrganizerWindow")
class FileOrganizerWindow(QDialog):
    print("FileOrganizerWindow loaded from", __file__)

    instance_count = 0
    def __init__(self, base_folder, tracklist_callback):
        print("USING THIS FileOrganizerWindow")
        super().__init__()
        print(f"[DEBUG] Instansierar FileOrganizerWindow: Instans-ID: {id(self)}")
        self.tracklist_callback = tracklist_callback  # Tilldela callback
        print(f"[DEBUG] Callback tilldelad i __init__: {self.tracklist_callback}")


        # Sätt fönstertitel och layout
        self.setWindowTitle("File Organizer")
        self.resize(1100, 600)

        # Sätt en mörkbrun bakgrund
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(92, 64, 81))  # Mörkbrun färg
        self.setPalette(palette)

        # Layouts
        main_layout = QHBoxLayout(self)
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        # File system tree view (left panel)
        self.tree_view = QTreeView()
        self.file_model = QFileSystemModel()

        # Hämta sparad standardmapp eller använd hemkatalogen som fallback
        base_folder = self.load_default_folder()
        self.file_model.setRootPath(base_folder)
        self.tree_view.setModel(self.file_model)
        self.tree_view.setRootIndex(self.file_model.index(base_folder))
        self.tree_view.setSelectionMode(QTreeView.ExtendedSelection)
        self.tree_view.setDragEnabled(True)

        left_layout.addWidget(self.tree_view)

        # Add Selected and Remove Selected buttons
        self.add_button = QPushButton("Add Selected")
        self.add_button.clicked.connect(self.add_selected_files)
        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.clicked.connect(self.remove_selected_files)
        left_layout.addWidget(self.add_button)
        left_layout.addWidget(self.remove_button)

        self.change_folder_button = QPushButton("Change Default Folder")
        self.change_folder_button.clicked.connect(self.change_default_folder)
        left_layout.addWidget(self.change_folder_button)

        # Right panel setup
        self.category_dropdown = QComboBox()
        self.category_dropdown.setEditable(False)
        self.category_dropdown.setContextMenuPolicy(Qt.CustomContextMenu)
        self.category_dropdown.customContextMenuRequested.connect(self.rename_category)
        self.category_dropdown.currentIndexChanged.connect(self.load_selected_category)
        right_layout.addWidget(self.category_dropdown)

        # Buttons for category management
        category_button_layout = QHBoxLayout()
        self.select_all_button = QPushButton("Select All")
        self.select_all_button.clicked.connect(self.select_all_files)
        category_button_layout.addWidget(self.select_all_button)
        self.add_category_button = QPushButton("Add Category")
        self.add_category_button.clicked.connect(self.add_category)
        category_button_layout.addWidget(self.add_category_button)
        self.remove_category_button = QPushButton("Remove Category")
        self.remove_category_button.clicked.connect(self.remove_category)
        category_button_layout.addWidget(self.remove_category_button)

        right_layout.addLayout(category_button_layout)

        # Selected files list (right panel)
        self.selected_files_list = QListWidget()
        self.selected_files_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.selected_files_list.setAcceptDrops(True)
        self.selected_files_list.setDragEnabled(True)
        self.selected_files_list.setDragDropMode(QListWidget.InternalMove)
        self.selected_files_list.installEventFilter(self)
        self.selected_files_list.setSortingEnabled(True)
        print(f"Filer i 'selected_files_list': {[self.selected_files_list.item(i).text() for i in range(self.selected_files_list.count())]}")
        right_layout.addWidget(self.selected_files_list)

        # Add to Tracklist button
        self.add_to_tracklist_button = QPushButton("Add to Tracklist")
        self.add_to_tracklist_button.clicked.connect(self.add_to_tracklist)
        right_layout.addWidget(self.add_to_tracklist_button)

        # Save and Exit buttons
        bottom_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_categories)
        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.exit_and_save)
        bottom_layout.addWidget(self.save_button)
        bottom_layout.addWidget(self.exit_button)
        right_layout.addLayout(bottom_layout)

        # Initialize categories
        self.categories = self.load_categories()
        self.current_category = None
        self.populate_dropdown()

        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)

    #def __setattr__(self, name, value):
    #   print(f"[DEBUG] Sätter attribut '{name}' till: {value}")
    #   super().__setattr__(name, value)

    #def __delattr__(self, name):
    #    print(f"[DEBUG] Tar bort attribut '{name}'")
    #    super().__delattr__(name)



    #@property
    #def tracklist_callback(self):
    #    return self._tracklist_callback

    #@tracklist_callback.setter
    #def tracklist_callback(self, value):
    #    raise AttributeError("tracklist_callback kan inte ändras efter instansiering")



    def keyPressEvent(self, event):
        """Handle key press events."""
        # Kontrollera om Cmd+Backspace har tryckts (MacOS)
        if event.matches(QKeySequence.Delete) and event.modifiers() == Qt.MetaModifier:
            self.remove_selected_files()  # Anropa funktionen för att ta bort valda filer
                


    def populate_dropdown(self):
        """Load categories into the dropdown menu with 'Default' on top and the rest sorted alphabetically."""
        self.category_dropdown.clear()
        
        # Separera 'Default' och sortera de andra kategorierna
        default_category = "Default"
        sorted_categories = sorted([cat for cat in self.categories.keys() if cat != default_category])
        
        # Lägg till 'Default' först om den existerar
        if default_category in self.categories:
            self.category_dropdown.addItem(default_category)
        
        # Lägg till de övriga kategorierna i alfabetisk ordning
        self.category_dropdown.addItems(sorted_categories)
        
        # Välj den första kategorin i listan
        if self.categories:
            self.category_dropdown.setCurrentIndex(0)
            self.load_selected_category()



    def add_selected_files(self):
        """Add selected files from the tree view to the selected category."""
        if not self.current_category:
            QMessageBox.warning(self, "No Category Selected", "Please select or create a category first.")
            return

        # Filtrera unika filvägar från de valda indexen
        selected_indexes = self.tree_view.selectionModel().selectedIndexes()
        file_paths = set()  # Använd en set för att lagra unika filvägar

        for index in selected_indexes:
            if self.file_model.isDir(index):
                continue  # Hoppa över kataloger
            file_path = self.file_model.filePath(index)
            file_paths.add(file_path)  # Lägg till filvägen i setet

        # Lägg till varje unik fil i kategorin och listan
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            self.categories[self.current_category].append(file_name)
            self.selected_files_list.addItem(file_name)
        selected_files = [item.text() for item in self.selected_files_list.selectedItems()]
        print(f"Markerade filer i 'selected_files_list': {selected_files}")
    



    def remove_selected_files(self):
        """Remove selected files from the selected category."""
        if not self.current_category:
            QMessageBox.warning(self, "No Category Selected", "Please select a category first.")
            return

        # Ta bort valda filer från kategoridatan
        removed_files = []
        for item in self.selected_files_list.selectedItems():
            file_name = item.text()
            if file_name in self.categories[self.current_category]:
                self.categories[self.current_category].remove(file_name)
                removed_files.append(file_name)
            self.selected_files_list.takeItem(self.selected_files_list.row(item))

        print(f"Removed files: {removed_files}")  # Logga vilka filer som togs bort
        # print(f"Updated category '{self.current_category}': {self.categories[self.current_category]}")  # Logga kategorin efter uppdatering






    def add_category(self):
        """Add a new category."""
        category_name, ok = QInputDialog.getText(self, "Add Category", "Enter category name:")
        if ok and category_name:
            if category_name in self.categories:
                QMessageBox.warning(self, "Duplicate Category", f"The category '{category_name}' already exists.")
                return
            # Lägg till den nya kategorin
            self.categories[category_name] = []
            
            # Uppdatera dropdown-menyn med sorterade kategorier
            self.populate_dropdown()
            
            # Välj den nya kategorin och töm det högra fönstret
            self.category_dropdown.setCurrentText(category_name)
            self.selected_files_list.clear()
            self.current_category = category_name



    def remove_category(self):
        """Remove the currently selected category."""
        if not self.current_category:
            QMessageBox.warning(self, "No Category Selected", "Please select a category first.")
            return

        reply = QMessageBox.question(
            self, "Remove Category",
            f"Are you sure you want to remove the category '{self.current_category}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.categories.pop(self.current_category, None)
            current_index = self.category_dropdown.currentIndex()
            self.category_dropdown.removeItem(current_index)
            self.current_category = None
            self.selected_files_list.clear()

    def rename_category(self):
        """Rename the currently selected category."""
        if not self.current_category:
            QMessageBox.warning(self, "No Category Selected", "Please select a category first.")
            return

        new_name, ok = QInputDialog.getText(self, "Rename Category", "Enter new category name:", text=self.current_category)
        if ok and new_name and new_name != self.current_category:
            if new_name in self.categories:
                QMessageBox.warning(self, "Duplicate Category", f"The category '{new_name}' already exists.")
                return
            # Save the new name and update dropdown
            self.categories[new_name] = self.categories.pop(self.current_category)
            self.current_category = new_name
            self.category_dropdown.setItemText(self.category_dropdown.currentIndex(), new_name)
            self.save_categories()  # Ensure changes are saved immediately


    def load_selected_category(self):
        """Load files from the selected category into the list."""
        self.selected_files_list.clear()
        self.current_category = self.category_dropdown.currentText()
        if self.current_category and self.current_category in self.categories:
            for file_name in self.categories[self.current_category]:
                self.selected_files_list.addItem(file_name)












    def add_to_tracklist(self, selected_files):
        print(f"[DEBUG] add_to_tracklist anropad. Instans-ID: {id(self)}")
        print(f"[DEBUG] Attribut vid add_to_tracklist: {self.__dict__}")
        if hasattr(self, 'tracklist_callback'):
            print(f"[DEBUG] tracklist_callback finns: {self.tracklist_callback}")
        else:
            print("[ERROR] tracklist_callback saknas!")









    


    def save_categories(self):
        """Save categories and their files to a file."""
        try:
            with open("categories.json", "w") as file:
                json.dump(self.categories, file, indent=4)
            # print("Categories saved successfully.")  # Logga när filen sparas
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save categories: {e}")



    def load_categories(self):
        """Load categories from a file."""
        if os.path.exists("categories.json"):
            try:
                with open("categories.json", "r") as file:
                    categories = json.load(file)
                    # print(f"Loaded categories: {categories}")  # Logga laddade kategorier
                    return categories
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load categories: {e}")
        return {}  # Returnera en tom dictionary om filen inte finns eller inte kan läsas


    def exit_and_save(self):
        """Save categories and close the dialog."""
        try:
            self.save_categories()  # Spara kategorier
            self.accept()  # Stäng fönstret korrekt genom att acceptera dialogen
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while saving or closing: {e}")


    def select_all_files(self):
        """Välj alla filer i den högra listan."""
        for i in range(self.selected_files_list.count()):
            self.selected_files_list.item(i).setSelected(True)

    def load_default_folder(self):
        """Load the default folder path from a configuration file."""
        config_file = "config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as file:
                    config = json.load(file)
                    default_folder = config.get("default_folder", QDir.homePath())
                    if os.path.exists(default_folder):  # Kontrollera att mappen finns
                        return default_folder
                    else:
                        QMessageBox.warning(self, "Warning", f"Default folder '{default_folder}' does not exist. Reverting to home directory.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load default folder: {e}")
        return QDir.homePath()  # Om inget hittas eller fel uppstår


    def save_default_folder(self, folder_path):
        """Save the default folder path to a configuration file."""
        config_file = "config.json"
        try:
            with open(config_file, "w") as file:
                json.dump({"default_folder": folder_path}, file, indent=4)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save default folder: {e}")


    from PyQt5.QtWidgets import QFileDialog

    def change_default_folder(self):
        """Allow the user to select a new default folder."""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Default Folder", QDir.homePath())
        if folder_path:
            self.save_default_folder(folder_path)

            # Skapa om filmodellen
            self.file_model = QFileSystemModel()
            self.file_model.setRootPath(folder_path)
            self.tree_view.setModel(self.file_model)
            self.tree_view.setRootIndex(self.file_model.index(folder_path))

            QMessageBox.information(self, "Default Folder Changed", f"Default folder set to: {folder_path}")


    

    def eventFilter(self, source, event):
        """Handle key press events for specific widgets."""
        if source == self.selected_files_list and event.type() == QEvent.KeyPress:
            # Kontrollera Cmd+Backspace med flexibel modifierarhantering
            if event.key() == Qt.Key_Backspace and (event.modifiers() & Qt.MetaModifier or event.modifiers() & 67108864):
                print("Cmd+Backspace detected. Removing selected files.")
                self.remove_selected_files()
                return True  # Händelsen har hanterats
            # Logga alla tangenttryckningar för fortsatt felsökning
            print(f"Key: {event.key()}, Modifiers: {event.modifiers()} (Expected MetaModifier: {Qt.MetaModifier})")
        return super().eventFilter(source, event)




   
    def __del__(self):
         print(f"[DEBUG] FileOrganizerWindow raderas. Instans-ID: {id(self)}")





if __name__ == "__main__":
    def test_callback(files):
        print("Adding to tracklist:", files)

    app = QApplication(sys.argv)

    # Skapa och kör FileOrganizerWindow
    window = FileOrganizerWindow(None, tracklist_callback=test_callback)
    if window.exec_():
        _ = window.categories  # Behåll data, men logga inte

    sys.exit(app.exec_())
