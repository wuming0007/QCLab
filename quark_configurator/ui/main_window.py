from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QStackedWidget, QLabel, QTextEdit, QMessageBox, QFileDialog, QTreeWidget, QTreeWidgetItem
import json
import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quark Configurator")
        self.setGeometry(100, 100, 1200, 800)

        # Initialize without loading a specific file
        self.config_data = {}

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)

        # Left Panel (Configuration Navigation with Tree Structure)
        self.left_panel = QTreeWidget()
        self.left_panel.setHeaderLabel("Configuration")
        self.left_panel.setMaximumWidth(200)
        self.left_panel.itemClicked.connect(self.display_config_section)
        main_layout.addWidget(self.left_panel)

        # Middle Panel (Quantum Chip Topology)
        self.middle_panel = QLabel("Quantum Chip Topology (Placeholder)")
        self.middle_panel.setStyleSheet("background-color: lightgray;")
        self.middle_panel.setMinimumWidth(400)
        main_layout.addWidget(self.middle_panel)

        # Right Panel (Dynamic Parameter Editing & Plotting)
        self.right_panel = QStackedWidget()
        self.right_panel.setMinimumWidth(400)
        main_layout.addWidget(self.right_panel)

        # Add Menu for File Operations
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        open_action = file_menu.addAction("Open Config")
        open_action.triggered.connect(self.open_config_file)

    def open_config_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Config File", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    self.config_data = json.load(f)
                self.populate_tree_view()
                if self.left_panel.topLevelItemCount() > 0:
                    self.display_config_section(self.left_panel.topLevelItem(0))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load file: {e}")

    def populate_tree_view(self):
        self.left_panel.clear()
        for key in self.config_data.keys():
            top_item = QTreeWidgetItem(self.left_panel, [key])
            # Add sub-items if the value is a dictionary or list
            value = self.config_data[key]
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, (dict, list)):
                        sub_item = QTreeWidgetItem(top_item, [sub_key])
                        self._populate_sub_tree(sub_item, sub_value)
                    else:
                        sub_item = QTreeWidgetItem(top_item, [f"{sub_key}: {sub_value}"])
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    sub_item = QTreeWidgetItem(top_item, [f"Item {i}"])
                    self._populate_sub_tree(sub_item, item)
            else:
                top_item.setText(0, f"{key}: {value}")
            self.left_panel.addTopLevelItem(top_item)

    def _populate_sub_tree(self, parent_item, data):
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    child_item = QTreeWidgetItem(parent_item, [key])
                    self._populate_sub_tree(child_item, value)
                else:
                    QTreeWidgetItem(parent_item, [f"{key}: {value}"])
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    child_item = QTreeWidgetItem(parent_item, [f"Item {i}"])
                    self._populate_sub_tree(child_item, item)
                else:
                    QTreeWidgetItem(parent_item, [f"Item {i}: {item}"])

    def display_config_section(self, item, column=0):
        section_name = item.text(column)
        section_data = self.config_data.get(section_name, {})
        if item.parent():  # If it's a sub-item
            parent_name = item.parent().text(0)
            section_data = self.config_data.get(parent_name, {}).get(section_name, {})

        # Create a QTextEdit to display the JSON data
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setText(json.dumps(section_data, indent=4))

        # Remove previous widgets from the stacked widget
        while self.right_panel.count() > 0:
            widget_to_remove = self.right_panel.widget(0)
            self.right_panel.removeWidget(widget_to_remove)
            widget_to_remove.deleteLater()

        self.right_panel.addWidget(text_edit)
        self.right_panel.setCurrentWidget(text_edit)