import os, sys
from PyQt5 import QtWidgets as QtW
from PyQt5.QtCore import Qt

import graph
import configPanel
import yamlLoader
import json  # Import the json module


class MainWindow(QtW.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("pandemic-config-gui")
        self.resize(1280, 720)

        self.splitter = QtW.QSplitter(Qt.Horizontal)

        left_panel = configPanel.DiseaseConfigWidget()

        self.right_panel = graph.NodeGraphWidget()

        left_panel.config_saved.connect(self.handle_config_save)

        self.splitter.addWidget(left_panel)
        self.splitter.addWidget(self.right_panel)
        self.splitter.setSizes([350, 930])

        self.setCentralWidget(self.splitter)

        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")

        load_action = QtW.QAction("Import YAML...", self)
        load_action.triggered.connect(self.on_import_yaml)
        file_menu.addAction(load_action)

        # ADDED: Action to export YAML
        export_yaml_action = QtW.QAction("Export YAML...", self)
        export_yaml_action.triggered.connect(self.on_export_yaml)
        file_menu.addAction(export_yaml_action)

        # ADDED: Action to import NodeGraph JSON session
        import_json_action = QtW.QAction("Import JSON...", self)
        import_json_action.triggered.connect(self.on_import_json)
        file_menu.addAction(import_json_action)

    def handle_config_save(self, config_data):
        print("MainWindow received saved config.")
        graph_data = self.right_panel.graph.serialize_session()

        # Save the serialized nodegraph data to a file
        output_filename = "nodegraph_session.json"
        try:
            with open(output_filename, "w") as f:
                # Use json.dump for clean, indented output
                json.dump(graph_data, f, indent=4)
            print(f"NodeGraph session successfully saved to: {output_filename}")
        except Exception as e:
            print(f"Error saving NodeGraph session to file: {e}")

    def on_import_yaml(self):
        file_path, _ = QtW.QFileDialog.getOpenFileName(
            self, "Open Config File", "", "YAML Files (*.yaml *.yml)"
        )
        if file_path:
            config_panel = self.splitter.widget(0)
            graph_widget = self.right_panel

            yamlLoader.load_config(file_path, config_panel, graph_widget)

    # ADDED: Method to handle YAML export
    def on_export_yaml(self):
        file_path, _ = QtW.QFileDialog.getSaveFileName(
            self, "Export Config File", "", "YAML Files (*.yaml *.yml)"
        )
        if file_path:
            config_panel = self.splitter.widget(0)
            graph_widget = self.right_panel
            yamlLoader.save_config(file_path, config_panel, graph_widget)

    # ADDED: Method to import NodeGraph JSON session
    def on_import_json(self):
        file_path, _ = QtW.QFileDialog.getOpenFileName(
            self, "Open NodeGraph Session", "", "JSON Files (*.json)"
        )
        if file_path:
            print(f"Loading NodeGraph session from: {file_path}")
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)

                self.right_panel.graph.deserialize_session(data)
                print("NodeGraph session successfully loaded.")
            except Exception as e:
                print(f"Error loading JSON file: {e}")
                QtW.QMessageBox.critical(
                    self, "Error", f"Failed to load NodeGraph session:\n{e}"
                )


def run_app():
    app = QtW.QApplication(sys.argv)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    qss_path = os.path.join(script_dir, "style", "theme.qss")

    if os.path.exists(qss_path):
        try:
            with open(qss_path, "r") as f:
                app.setStyleSheet(f.read())
        except Exception as e:
            print(f"Error loading stylesheet: {e}")

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run_app()
