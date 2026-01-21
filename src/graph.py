from typing import List, Optional, Union, Any
from PyQt5 import QtWidgets as QtW
from PyQt5 import QtCore
import NodeGraphQt as NGQt

# Categories for JUNE simulator logic mapping
STAGE_TYPES: List[str] = [
    "none",
    "stay_at_home_stage",
    "fatality_stage",
    "recovered_stage",
    "hospitalised_stage",
    "intensive_care_stage",
    "severe_symptoms_stay_at_home_stage",
]


class DefaultLowestStage(NGQt.BaseNode):
    """
    Entry point node for a disease trajectory in the JUNE simulation.
    The clinical identifier (e.g., 'exposed') is derived from the node's display name.
    """

    __identifier__ = "symptoms"
    NODE_NAME = "DefaultLowestStage"

    def __init__(self):
        """Initializes the node with Stage Type dropdown and Value input."""
        super(DefaultLowestStage, self).__init__()
        self.set_name("exposed")
        self.set_color(40, 150, 40)
        self.add_output("Completion Time")

        # Mapping to JUNE simulation logic category (e.g., stay_at_home_stage)
        self.add_combo_menu("stage_type", "Stage Type", items=STAGE_TYPES)

        # Numeric value associated with the symptom severity
        self.add_text_input("tag", "Value", "0")


class TransitionNode(NGQt.BaseNode):
    """
    Intermediate progression state within a disease trajectory.
    """

    __identifier__ = "symptoms"
    NODE_NAME = "TransitionNode"

    def __init__(self):
        """Initializes the Transition node."""
        super(TransitionNode, self).__init__()
        self.set_name("mild")
        self.set_color(40, 150, 40)
        self.add_input("Previous", multi_input=True)
        self.add_output("Completion Time")

        self.add_combo_menu("stage_type", "Stage Type", items=STAGE_TYPES)
        self.add_text_input("tag", "Value", "0")


class TerminalStage(NGQt.BaseNode):
    """
    Final state (e.g., 'recovered') where disease progression ends.
    """

    __identifier__ = "symptoms"
    NODE_NAME = "TerminalStage"

    def __init__(self):
        """Initializes the Terminal node."""
        super(TerminalStage, self).__init__()
        self.set_name("recovered")
        self.set_color(180, 40, 40)
        self.add_input("Previous", multi_input=True)

        self.add_combo_menu("stage_type", "Stage Type", items=STAGE_TYPES)
        self.add_text_input("tag", "Value", "0")


class UniversalTimeNode(NGQt.BaseNode):
    """
    Defines the statistical time distribution spent in the preceding symptom stage.
    """

    __identifier__ = "transitions"
    NODE_NAME = "UniversalTimeNode"

    def __init__(self):
        """Initializes the node with mathematical distribution parameters."""
        super(UniversalTimeNode, self).__init__()
        self.set_name("Time Distribution")
        self.set_color(220, 160, 20)

        self.add_input("Symptom")
        self.add_output("Next")

        self.add_combo_menu(
            "type",
            "Distribution",
            items=["constant", "normal", "lognormal", "beta", "gamma", "exponweib"],
        )

        self.add_text_input("Val", "Value/Loc", text="0.0")
        self.add_text_input("scale", "Scale", text="1.0")
        self.add_text_input("a", "a", text="0.0")
        self.add_text_input("b", "b", text="0.0")
        self.add_text_input("c", "c", text="0.0")
        self.add_text_input("s", "s", text="0.0")


class NodeGraphWidget(QtW.QWidget):
    """
    Container widget managing the NodeGraphQt instance and automation handlers.
    """

    def __init__(self):
        """Initializes the graph and connects logic signals."""
        super().__init__()
        layout = QtW.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.graph = NGQt.NodeGraph()
        layout.addWidget(self.graph.viewer())

        self.graph.register_nodes(
            [
                DefaultLowestStage,
                TransitionNode,
                TerminalStage,
                UniversalTimeNode,
            ]
        )

        self.graph.set_background_color(38, 50, 56)
        self.graph.set_grid_color(55, 71, 79)

        self.setupContextMenu()

        self.graph.port_connected.connect(self.onConnectionCreated)
        self.graph.node_created.connect(self.onNodeCreated)
        self.graph.property_changed.connect(self.onNodePropChanged)

    def setupContextMenu(self) -> None:
        """
        Initializes the context menus for creating symptom and transition nodes,
        and adds a command for manual auto-layout with a fix for the TypeError.
        """
        graph_menu = self.graph.get_context_menu("graph")

        # FIX: Pass all_nodes() to the layout engine to avoid TypeError
        graph_menu.add_command(
            "Auto Layout", lambda: self.graph.auto_layout_nodes(self.graph.all_nodes())
        )
        graph_menu.add_separator()

        symptom_menu = graph_menu.add_menu("Symptom Nodes")

        def createCmd(node_class):
            node_key = f"{node_class.__identifier__}.{node_class.__name__}"
            return lambda: self.graph.create_node(node_key)

        symptom_menu.add_command("Lowest Stage", createCmd(DefaultLowestStage))
        symptom_menu.add_command("Transition Node", createCmd(TransitionNode))
        symptom_menu.add_command("Terminal Stage", createCmd(TerminalStage))

        trans_menu = graph_menu.add_menu("Transition Nodes")
        trans_menu.add_command("Time Distribution", createCmd(UniversalTimeNode))

    def onConnectionCreated(self, port_in: NGQt.Port, port_out: NGQt.Port) -> None:
        """Detects symptom-to-symptom links and splices a distribution node."""
        node_in = port_in.node()
        node_out = port_out.node()

        if node_in.type_.startswith("symptoms.") and node_out.type_.startswith(
            "symptoms."
        ):
            QtCore.QTimer.singleShot(0, lambda: self.insertTimeNode(port_out, port_in))

    def insertTimeNode(self, source_port: NGQt.Port, target_port: NGQt.Port) -> None:
        """Performs the physical splicing of a distribution node into a connection."""
        self.graph.clear_selection()
        source_node, target_node = source_port.node(), target_port.node()
        source_port.disconnect_from(target_port)

        time_node = self.graph.create_node(
            "transitions.UniversalTimeNode", push_undo=True
        )
        pos_s, pos_e = source_node.pos(), target_node.pos()
        time_node.set_pos((pos_s[0] + pos_e[0]) / 2, (pos_s[1] + pos_e[1]) / 2)

        source_port.connect_to(time_node.input(0), push_undo=True)
        time_node.output(0).connect_to(target_port, push_undo=True)

        self.graph.viewer().update()
        self.updateNodeVisibility(time_node)

    def onNodeCreated(self, node: NGQt.BaseNode) -> None:
        """Ensures visibility is correct for newly added nodes."""
        if isinstance(node, UniversalTimeNode):
            QtCore.QTimer.singleShot(10, lambda: self.updateNodeVisibility(node))

    def onNodePropChanged(
        self, node: NGQt.BaseNode, prop_name: str, prop_value: Any
    ) -> None:
        """Updates distribution UI when the type dropdown is modified."""
        if isinstance(node, UniversalTimeNode) and prop_name == "type":
            self.updateNodeVisibility(node)

    def updateNodeVisibility(self, node: UniversalTimeNode) -> None:
        """
        Hides or shows parameter input fields and their labels based on
        the selected distribution type to prevent 'ghost parameters'.

        Args:
            node: The UniversalTimeNode to update.
        """
        dist_type = node.get_property("type")

        # Define which parameters should be visible for each distribution type
        visibility_map = {
            "constant": ["Val"],
            "normal": ["Val", "scale"],
            "lognormal": ["Val", "scale", "s"],
            "gamma": ["Val", "scale", "a"],
            "beta": ["Val", "scale", "a", "b"],
            "exponweib": ["Val", "scale", "a", "c"],
        }

        all_fields = ["Val", "scale", "a", "b", "c", "s"]
        visible_fields = visibility_map.get(dist_type, ["Val"])

        visible_count = 0
        for field in all_fields:
            widget_wrapper = node.get_widget(field)
            if widget_wrapper:
                should_show = field in visible_fields

                # 1. Toggle visibility of the wrapper itself
                widget_wrapper.setVisible(should_show)

                # 2. Correctly call internal widget() and label() methods
                # This ensures the internal Qt elements are properly hidden
                try:
                    # Check for the widget method and call it
                    if hasattr(widget_wrapper, "widget"):
                        internal_widget = widget_wrapper.widget()
                        if internal_widget:
                            internal_widget.setVisible(should_show)

                    # Check for the label method and call it
                    if hasattr(widget_wrapper, "label"):
                        label_widget = widget_wrapper.label()
                        if label_widget:
                            label_widget.setVisible(should_show)
                except Exception:
                    # Fallback for different NodeGraphQt versions/configurations
                    pass

                if should_show:
                    visible_count += 1

        # 3. Recalculate node height to eliminate empty space from hidden parameters
        new_height = 80 + (visible_count * 28)
        node.set_property("height", new_height, push_undo=False)

        # 4. Trigger a refresh to clear visual artifacts
        node.update()
