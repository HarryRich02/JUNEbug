import os, sys, json
from typing import Dict, Any
from PyQt5 import QtWidgets as QtW
from PyQt5.QtCore import Qt
import graph, configPanel, yamlLoader


class MainWindow(QtW.QMainWindow):
    """Main application window coordination."""

    def __init__(self):
        """Initializes UI components."""
        super().__init__()
        self.setWindowTitle("JUNEbug - pandemic-config-gui")
        self.resize(1280, 720)
        self.splitter = QtW.QSplitter(Qt.Horizontal)
        self.left_panel = configPanel.DiseaseConfigWidget()
        self.right_panel = graph.NodeGraphWidget()

        # Note: handleConfigSave connection removed as the button is gone

        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.right_panel)
        self.splitter.setSizes([350, 930])
        self.setCentralWidget(self.splitter)
        self.setupMenus()

    def setupMenus(self) -> None:
        """Creates the File menu."""
        menu = self.menuBar().addMenu("File")
        # Removed "Import JSON Session..." from the actions list
        actions = [
            ("Import YAML...", self.onImportYaml),
            ("Export YAML...", self.onExportYaml),
        ]
        for label, func in actions:
            act = QtW.QAction(label, self)
            act.triggered.connect(func)
            menu.addAction(act)

    def onImportYaml(self) -> None:
        """Handles import."""
        p, _ = QtW.QFileDialog.getOpenFileName(
            self, "Open Config", "", "YAML (*.yaml *.yml)"
        )
        if p:
            yamlLoader.loadConfig(p, self.left_panel, self.right_panel)

    def onExportYaml(self) -> None:
        """Handles export."""
        p, _ = QtW.QFileDialog.getSaveFileName(
            self, "Save Config", "", "YAML (*.yaml *.yml)"
        )
        if p:
            yamlLoader.saveConfig(p, self.left_panel, self.right_panel)


def runApp() -> None:
    """Bootstrap application with original theme."""
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
