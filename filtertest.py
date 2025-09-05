from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QTreeView, QListWidget,
    QPushButton, QFileSystemModel, QFileDialog, QComboBox, QLabel
)

class CombinedWindow(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("File Organizer")
        self.resize(1200, 800)

        # Main layout
        main_layout = QHBoxLayout()

        # Left panel (File Organizer)
        self.file_organizer_layout = self.create_file_organizer()
        main_layout.addLayout(self.file_organizer_layout)

        # Right panel (Metadata Filter)
        self.metadata_filter_layout = self.create_metadata_filter()
        main_layout.addLayout(self.metadata_filter_layout)

        self.setLayout(main_layout)

    def create_file_organizer(self):
        layout = QVBoxLayout()

        # File tree view
        self.tree_view = QTreeView()
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath("")
        self.tree_view.setModel(self.file_model)
        self.tree_view.setRootIndex(self.file_model.index(""))
        layout.addWidget(self.tree_view)

        # Selected files list
        self.selected_files_list = QListWidget()
        layout.addWidget(self.selected_files_list)

        # Buttons
        add_button = QPushButton("Add Selected")
        add_button.clicked.connect(self.add_selected_files)
        remove_button = QPushButton("Remove Selected")
        remove_button.clicked.connect(self.remove_selected_files)
        change_folder_button = QPushButton("Change Default Folder")
        change_folder_button.clicked.connect(self.change_default_folder)
        layout.addWidget(add_button)
        layout.addWidget(remove_button)
        layout.addWidget(change_folder_button)

        return layout

    def create_metadata_filter(self):
        layout = QVBoxLayout()

        # Dropdowns for metadata filters
        for i in range(5):
            dropdown_label = QLabel(f"Filter {i + 1}")
            dropdown = QComboBox()
            dropdown.addItems(["All", "Option 1", "Option 2"])
            layout.addWidget(dropdown_label)
            layout.addWidget(dropdown)

        # Buttons
        apply_filters_button = QPushButton("Apply Filters")
        time_settings_button = QPushButton("Open Time Settings")
        layout.addWidget(apply_filters_button)
        layout.addWidget(time_settings_button)

        return layout

    def add_selected_files(self):
        selected_indexes = self.tree_view.selectionModel().selectedIndexes()
        for index in selected_indexes:
            if not self.file_model.isDir(index):
                file_name = self.file_model.fileName(index)
                self.selected_files_list.addItem(file_name)

    def remove_selected_files(self):
        for item in self.selected_files_list.selectedItems():
            self.selected_files_list.takeItem(self.selected_files_list.row(item))

    def change_default_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Default Folder", "")
        if folder_path:
            self.file_model.setRootPath(folder_path)
            self.tree_view.setRootIndex(self.file_model.index(folder_path))

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    window = CombinedWindow()
    window.show()

    sys.exit(app.exec_())
