"""
Configuration Panel Module

Left panel UI for disease metadata and transmission dynamics configuration.
Provides form-based controls for global disease parameters.
"""

from typing import Dict, Any, List, Optional
from PyQt5 import QtWidgets as QtW
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QAbstractAnimation

# ============================================================================
# Constants: Clinical Disease Stages
# ============================================================================

DISEASE_STAGES: List[str] = [
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

# ============================================================================
# Constants: Statistical Distribution Types
# ============================================================================

DISTRIBUTION_TYPES: List[str] = [
    "constant",
    "normal",
    "lognormal",
    "beta",
    "gamma",
    "exponweib",
]


class DistributionEditor(QtW.QWidget):
    """
    Sub-panel for defining global transmission mathematical distribution parameters.
    """

    sigResize = pyqtSignal()

    def __init__(self, label_text: str, default_type: str = "constant"):
        """
        Initializes the DistributionEditor widget.

        Args:
            label_text: The label text to display for this distribution group.
            default_type: The mathematical distribution type to select by default.
        """
        super().__init__()
        layout = QtW.QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        header = QtW.QHBoxLayout()
        header.addWidget(QtW.QLabel(f"{label_text} Type:"))
        self.type_combo = QtW.QComboBox()
        self.type_combo.addItems(DISTRIBUTION_TYPES)
        self.type_combo.setCurrentText(default_type)
        self.type_combo.currentTextChanged.connect(self.updateFields)
        header.addWidget(self.type_combo)
        layout.addLayout(header)

        self.params_widget = QtW.QWidget()
        self.params_layout = QtW.QFormLayout(self.params_widget)
        self.params_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.params_widget)
        self.inputs: Dict[str, QtW.QLineEdit] = {}
        self.updateFields(default_type)

    def updateFields(self, dist_type: str) -> None:
        """
        Rebuilds the input fields dynamically based on the selected distribution type.

        Args:
            dist_type: The name of the statistical distribution (e.g., 'beta').
        """
        while self.params_layout.count():
            child = self.params_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.inputs = {}
        fields = {
            "constant": ["value"],
            "normal": ["loc", "scale"],
            "lognormal": ["s", "loc", "scale"],
            "gamma": ["a", "loc", "scale"],
            "beta": ["a", "b", "loc", "scale"],
            "exponweib": ["a", "c", "loc", "scale"],
        }.get(dist_type, [])

        for f in fields:
            edit = QtW.QLineEdit()
            self.inputs[f] = edit
            self.params_layout.addRow(f"{f}:", edit)
        self.sigResize.emit()

    def getData(self) -> Dict[str, Any]:
        """
        Gathers the entered parameters into a dictionary for YAML export.

        Returns:
            A dictionary containing the distribution 'type' and its numeric parameters.
        """
        data = {"type": self.type_combo.currentText()}
        for f, widget in self.inputs.items():
            val = widget.text()
            try:
                data[f] = float(val) if "." in val else int(val)
            except ValueError:
                data[f] = 0.0
        return data


class CollapsibleBox(QtW.QWidget):
    """
    An individual styled container in the accordion that can expand or collapse its content.
    """

    toggled = pyqtSignal(bool)

    def __init__(
        self, title: str, content: QtW.QWidget, parent: Optional[QtW.QWidget] = None
    ):
        """
        Initializes the CollapsibleBox.

        Args:
            title: The text displayed on the toggle button.
            content: The widget to be shown or hidden.
            parent: The optional parent widget.
        """
        super().__init__(parent)
        self.btn = QtW.QToolButton(text=title, checkable=True)
        self.btn.setObjectName("collapsibleBtn")  # Styled via theme.qss
        self.btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.btn.setArrowType(Qt.RightArrow)
        self.btn.clicked.connect(self.onPressed)

        self.content = content
        self.content.setMaximumHeight(0)

        lay = QtW.QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.btn)
        lay.addWidget(self.content)
        self.anim = QPropertyAnimation(self.content, b"maximumHeight")

    def onPressed(self) -> None:
        """
        Triggers the expansion or collapse animation when the button is pressed.
        """
        chk = self.btn.isChecked()
        self.btn.setArrowType(Qt.DownArrow if chk else Qt.RightArrow)
        self.toggled.emit(chk)
        self.content.layout().activate()
        self.anim.setEndValue(self.content.layout().sizeHint().height() if chk else 0)
        self.anim.setDuration(200)
        self.anim.start()

    def collapse(self) -> None:
        """
        Programmatically collapses the box if it is currently expanded.
        """
        if self.btn.isChecked():
            self.btn.setChecked(False)
            self.onPressed()


class AccordionWidget(QtW.QWidget):
    """
    Manages a stack of CollapsibleBoxes, ensuring only one is open at a time.
    """

    def __init__(self):
        """Initializes the AccordionWidget."""
        super().__init__()
        self.layout = QtW.QVBoxLayout(self)
        self.layout.setSpacing(5)
        self.boxes: List[CollapsibleBox] = []
        self.layout.addStretch(1)

    def addItem(self, title: str, widget: QtW.QWidget) -> None:
        """
        Adds a new collapsible item to the managed stack.

        Args:
            title: The label for the toggle button.
            widget: The content widget for the box.
        """
        box = CollapsibleBox(title, widget)
        self.layout.insertWidget(self.layout.count() - 1, box)
        self.boxes.append(box)
        box.toggled.connect(lambda chk: self.onBoxToggled(box, chk))

    def onBoxToggled(self, sender: CollapsibleBox, checked: bool) -> None:
        """
        Handles mutual exclusivity for the collapsible boxes.

        Args:
            sender: The box instance that was toggled.
            checked: The new expansion state.
        """
        if checked:
            for b in self.boxes:
                if b != sender:
                    b.collapse()


class DiseaseConfigWidget(QtW.QWidget):
    """
    The primary control panel for global disease metadata and transmission dynamics.
    """

    configSaved = pyqtSignal(dict)

    def __init__(self):
        """Initializes the main configuration panel with the original look."""
        super().__init__()
        self.setObjectName("configPanel")
        layout = QtW.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scroll = QtW.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QtW.QFrame.NoFrame)

        content = QtW.QWidget()
        self.form = QtW.QVBoxLayout(content)
        self.form.setContentsMargins(20, 20, 20, 20)

        title = QtW.QLabel("Disease Config")
        title.setObjectName("configTitle")  # Styled via theme.qss
        self.form.addWidget(title)

        self.form.addWidget(QtW.QLabel("Name:"))
        self.name_entry = QtW.QLineEdit()
        self.form.addWidget(self.name_entry)

        self.form.addWidget(QtW.QLabel("Default Lowest Stage:"))
        self.dls_combo = QtW.QComboBox()
        self.dls_combo.addItems(DISEASE_STAGES)
        self.form.addWidget(self.dls_combo)

        self.form.addWidget(QtW.QLabel("Max Mild Symptom Tag:"))
        self.mmst_combo = QtW.QComboBox()
        self.mmst_combo.addItems(DISEASE_STAGES)
        self.form.addWidget(self.mmst_combo)

        self.form.addSpacing(20)
        header = QtW.QLabel("Transmission Dynamics")
        header.setObjectName("sectionHeader")  # Styled via theme.qss
        self.form.addWidget(header)

        self.trans_type_combo = QtW.QComboBox()
        self.trans_type_combo.addItems(["gamma", "normal", "beta"])
        self.form.addWidget(self.trans_type_combo)

        self.accordion = AccordionWidget()
        self.trans_editors: Dict[str, DistributionEditor] = {}

        sections = [
            ("max_infectiousness", "Max Infectiousness", "lognormal"),
            ("shape", "Shape", "normal"),
            ("rate", "Rate", "normal"),
            ("shift", "Shift", "normal"),
            ("asymptomatic_infectious_factor", "Asymp. Factor", "constant"),
            ("mild_infectious_factor", "Mild Factor", "constant"),
        ]

        for k, n, d in sections:
            editor = DistributionEditor(n, default_type=d)
            self.trans_editors[k] = editor
            self.accordion.addItem(n, editor)

        self.form.addWidget(self.accordion)
        self.form.addStretch(1)  # Pushes content to the top

        self.scroll.setWidget(content)
        layout.addWidget(self.scroll)

    def getConfigData(self) -> Dict[str, Any]:
        """
        Aggregates all panel inputs into a single dictionary for processing.

        Returns:
            A dictionary containing the full disease configuration data.
        """
        data = {
            "name": self.name_entry.text(),
            "default_lowest_stage": self.dls_combo.currentText(),
            "max_mild_symptom_tag": self.mmst_combo.currentText(),
            "transmission": {"type": self.trans_type_combo.currentText()},
        }
        for k, ed in self.trans_editors.items():
            data["transmission"][k] = ed.getData()
        return data
