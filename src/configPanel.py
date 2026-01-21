from PyQt5 import QtWidgets as QtW
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QAbstractAnimation

DISEASE_STAGES = [
    "recovered",
    "healthy",
    "exposed",
    "asymptomatic",
    "mild",
    "severe",
    "hospitalised",
    "intensive_care",
    "dead_home",
    "dead_hospital",
    "dead_icu",
]

DISTRIBUTION_TYPES = ["constant", "normal", "lognormal", "beta", "gamma", "exponweib"]


class DistributionEditor(QtW.QWidget):
    sig_resize = pyqtSignal()

    def __init__(self, label_text, default_type="constant"):
        super().__init__()
        self.main_layout = QtW.QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        header_layout = QtW.QHBoxLayout()
        header_layout.addWidget(QtW.QLabel(f"{label_text} Type:"))
        self.type_combo = QtW.QComboBox()
        self.type_combo.addItems(DISTRIBUTION_TYPES)
        self.type_combo.setCurrentText(default_type)
        self.type_combo.currentTextChanged.connect(self._update_fields)
        header_layout.addWidget(self.type_combo)
        self.main_layout.addLayout(header_layout)
        self.params_widget = QtW.QWidget()
        self.params_layout = QtW.QFormLayout(self.params_widget)
        self.params_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.params_widget)
        self.inputs = {}
        self._update_fields(default_type)

    def _update_fields(self, dist_type):
        while self.params_layout.count():
            child = self.params_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.inputs = {}
        fields = []
        if dist_type == "constant":
            fields = ["value"]
        elif dist_type == "normal":
            fields = ["loc", "scale"]
        elif dist_type == "lognormal":
            fields = ["s", "loc", "scale"]
        elif dist_type == "gamma":
            fields = ["a", "loc", "scale"]
        elif dist_type == "beta":
            fields = ["a", "b", "loc", "scale"]
        elif dist_type == "exponweib":
            fields = ["a", "c", "loc", "scale"]
        for field in fields:
            line_edit = QtW.QLineEdit()
            self.inputs[field] = line_edit
            self.params_layout.addRow(f"{field}:", line_edit)
        self.sig_resize.emit()

    def get_data(self):
        dist_type = self.type_combo.currentText()
        data = {"type": dist_type}
        for field, widget in self.inputs.items():
            val = widget.text()
            try:
                data[field] = float(val) if "." in val else int(val)
            except ValueError:
                data[field] = val if val else 0.0
        return data


class CollapsibleBox(QtW.QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, title, content_widget, parent=None):
        super().__init__(parent)
        self.toggle_button = QtW.QToolButton(text=title, checkable=True, checked=False)
        self.toggle_button.setStyleSheet(
            "QToolButton { border: none; font-weight: bold; text-align: left; background-color: #37474F; color: #ECEFF1; padding: 5px; }"
        )
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(Qt.RightArrow)
        self.toggle_button.clicked.connect(self.on_pressed)
        self.content_area = content_widget
        self.content_area.setMaximumHeight(0)
        if hasattr(self.content_area, "sig_resize"):
            self.content_area.sig_resize.connect(self.on_content_resize)
        lay = QtW.QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.toggle_button)
        lay.addWidget(self.content_area)
        self.anim = QPropertyAnimation(self.content_area, b"maximumHeight")
        self.anim.setDuration(200)

    def on_pressed(self):
        checked = self.toggle_button.isChecked()
        self.toggle_button.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)
        self.toggled.emit(checked)
        self.content_area.layout().activate()
        content_height = self.content_area.layout().sizeHint().height()
        self.anim.setDirection(
            QAbstractAnimation.Forward if checked else QAbstractAnimation.Backward
        )
        self.anim.setEndValue(content_height)
        self.anim.start()

    def on_content_resize(self):
        if self.toggle_button.isChecked():
            self.content_area.layout().activate()
            self.anim.setDirection(QAbstractAnimation.Forward)
            self.anim.setEndValue(self.content_area.layout().sizeHint().height())
            self.anim.start()

    def collapse(self):
        if self.toggle_button.isChecked():
            self.toggle_button.setChecked(False)
            self.on_pressed()


class AccordionWidget(QtW.QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QtW.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(5)
        self.boxes = []
        self.layout.addStretch(1)

    def add_item(self, title, widget):
        box = CollapsibleBox(title, widget)
        self.layout.insertWidget(self.layout.count() - 1, box)
        self.boxes.append(box)
        box.toggled.connect(lambda checked: self._on_box_toggled(box, checked))
        return box

    def _on_box_toggled(self, sender, checked):
        if checked:
            for box in self.boxes:
                if box != sender:
                    box.collapse()


class DiseaseConfigWidget(QtW.QWidget):
    config_saved = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setObjectName("configPanel")
        main_layout = QtW.QVBoxLayout(self)
        self.scroll_area = QtW.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QtW.QFrame.NoFrame)
        self.content_widget = QtW.QWidget()
        self.form_layout = QtW.QVBoxLayout(self.content_widget)
        title_label = QtW.QLabel("Disease Config")
        title_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; margin-bottom: 10px;"
        )
        self.form_layout.addWidget(title_label)
        self.form_layout.addWidget(QtW.QLabel("Name:"))
        self.name_entry = QtW.QLineEdit()
        self.form_layout.addWidget(self.name_entry)
        self.form_layout.addWidget(QtW.QLabel("Default Lowest Stage:"))
        self.dls_combo = QtW.QComboBox()
        self.dls_combo.addItems(DISEASE_STAGES)
        self.form_layout.addWidget(self.dls_combo)
        self.form_layout.addWidget(QtW.QLabel("Max Mild Symptom Tag:"))
        self.mmst_combo = QtW.QComboBox()
        self.mmst_combo.addItems(DISEASE_STAGES)
        self.form_layout.addWidget(self.mmst_combo)
        self.accordion = AccordionWidget()
        self.trans_editors = {}
        self.trans_type_combo = QtW.QComboBox()
        self.trans_type_combo.addItems(["gamma", "normal", "beta"])
        sections = [
            ("max_infectiousness", "Max Infectiousness", "lognormal"),
            ("shape", "Shape", "normal"),
            ("rate", "Rate", "normal"),
            ("shift", "Shift", "normal"),
            ("asymptomatic_infectious_factor", "Asymp. Factor", "constant"),
            ("mild_infectious_factor", "Mild Factor", "constant"),
        ]
        for key, name, default_dist in sections:
            editor = DistributionEditor(name, default_type=default_dist)
            self.trans_editors[key] = editor
            self.accordion.add_item(name, editor)
        self.form_layout.addWidget(self.accordion)
        self.save_button = QtW.QPushButton("Save Configuration")
        self.save_button.clicked.connect(self.getConfigData)
        self.form_layout.addWidget(self.save_button)
        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area)

    def getConfigData(self):
        config_data = {
            "name": self.name_entry.text(),
            "default_lowest_stage": self.dls_combo.currentText(),
            "max_mild_symptom_tag": self.mmst_combo.currentText(),
            "transmission": {"type": self.trans_type_combo.currentText()},
        }
        for key, editor in self.trans_editors.items():
            config_data["transmission"][key] = editor.get_data()
        self.config_saved.emit(config_data)
        return config_data
