"""
JUNEbug Application Module

Main window orchestration for the JUNE disease configuration GUI.
Manages the layout, menus, and integration between the configuration panel
and graph editor components.
"""

import os
import sys
from typing import Dict, Any

from PyQt5 import QtWidgets as QtW
from PyQt5.QtCore import Qt

import graph
import configPanel
import yamlLoader


class MainWindow(QtW.QMainWindow):
    """
    Main application window with split configuration and graph panels.
    
    Layout:
        - Left panel: DiseaseConfigWidget for disease metadata and transmission
        - Right panel: NodeGraphWidget for visual trajectory editing
    
    Menu:
        - File > Import YAML: Load disease configuration
        - File > Export YAML: Save current configuration
    """

    def __init__(self):
        """Initialize the main window with UI components and menus."""
        super().__init__()
        self.setWindowTitle("JUNEbug")
        self.resize(1280, 720)
        self.splitter = QtW.QSplitter(Qt.Horizontal)
        self.left_panel = configPanel.DiseaseConfigWidget()
        self.right_panel = graph.NodeGraphWidget()

        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.right_panel)
        self.splitter.setSizes([350, 930])
        self.setCentralWidget(self.splitter)
        self.setupMenus()

    def setupMenus(self) -> None:
        """
        Create the application menu bar.
        
        Adds File menu with:
        - Import YAML: Load disease configuration from file
        - Export YAML: Save configuration to file
        """
        menu = self.menuBar().addMenu("File")
        actions = [
            ("Import YAML...", self.onImportYaml),
            ("Export YAML...", self.onExportYaml),
        ]
        for label, func in actions:
            act = QtW.QAction(label, self)
            act.triggered.connect(func)
            menu.addAction(act)

    def onImportYaml(self) -> None:
        """
        Handle File > Import YAML action.
        
        Prompts user for a YAML file and loads it into the application.
        """
        p, _ = QtW.QFileDialog.getOpenFileName(
            self, "Open Config", "", "YAML (*.yaml *.yml)"
        )
        if p:
            yamlLoader.loadConfig(p, self.left_panel, self.right_panel)

    def onExportYaml(self) -> None:
        """
        Handle File > Export YAML action.
        
        Prompts user for an output location and saves the current configuration.
        """
        p, _ = QtW.QFileDialog.getSaveFileName(
            self, "Save Config", "", "YAML (*.yaml *.yml)"
        )
        if p:
            yamlLoader.saveConfig(p, self.left_panel, self.right_panel)


def runApp() -> None:
    """
    Launch the JUNEbug application.
    
    Initializes:
    - Qt application instance
    - Loads stylesheet from src/style/theme.qss
    - Creates and displays main window
    - Runs the event loop
    """
    app = QtW.QApplication(sys.argv)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    qss_path = os.path.join(script_dir, "style", "theme.qss")
    if os.path.exists(qss_path):
        try:
            with open(qss_path, "r") as f:
                app.setStyleSheet(f.read())
        except Exception as e:
            print(f"[JUNEbug] QSS Error: {e}")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
