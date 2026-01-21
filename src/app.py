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
        self.left_panel.configSaved.connect(self.handleConfigSave)
        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.right_panel)
        self.splitter.setSizes([350, 930])
        self.setCentralWidget(self.splitter)
        self.setupMenus()

    def setupMenus(self) -> None:
        """Creates the File menu."""
        menu = self.menuBar().addMenu("File")
        actions = [
            ("Import YAML...", self.onImportYaml),
            ("Export YAML...", self.onExportYaml),
            ("Import JSON Session...", self.onImportJson),
        ]
        for label, func in actions:
            act = QtW.QAction(label, self)
            act.triggered.connect(func)
            menu.addAction(act)

    def handleConfigSave(self, data: Dict[str, Any]) -> None:
        """Serializes session."""
        session = self.right_panel.graph.serialize_session()
        try:
            with open("nodegraph_session.json", "w") as f:
                json.dump(session, f, indent=4)
        except Exception as e:
            print(f"[JUNEbug] Error: {e}")

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

    def onImportJson(self) -> None:
        """Handles session loading."""
        p, _ = QtW.QFileDialog.getOpenFileName(
            self, "Open Session", "", "JSON (*.json)"
        )
        if p:
            with open(p, "r") as f:
                data = json.load(f)
            self.right_panel.graph.deserialize_session(data)


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
