from PyQt5 import QtWidgets as QtW
from PyQt5 import QtCore
import NodeGraphQt as NGQt

# Import stages for the Stage selection dropdown
from configPanel import DISEASE_STAGES

# Categories for JUNE simulator logic
JUNE_CATEGORIES = [
    "none",
    "stay_at_home_stage",
    "fatality_stage",
    "recovered_stage",
    "hospitalised_stage",
    "intensive_care_stage",
    "severe_symptoms_stay_at_home_stage",
]


class DefaultLowestStage(NGQt.BaseNode):
    __identifier__ = "symptoms"
    NODE_NAME = "DefaultLowestStage"

    def __init__(self):
        super(DefaultLowestStage, self).__init__()
        self.set_name("Lowest Stage")
        self.set_color(40, 150, 40)
        self.add_output("Completion Time")
        # Symptom Tag selection
        self.add_combo_menu("tag_name", "Stage", items=DISEASE_STAGES)
        # JUNE Logic Category selection
        self.add_combo_menu("june_category", "JUNE Category", items=JUNE_CATEGORIES)
        self.add_text_input("tag", "Value", "0")


class TransitionNode(NGQt.BaseNode):
    __identifier__ = "symptoms"
    NODE_NAME = "TransitionNode"

    def __init__(self):
        super(TransitionNode, self).__init__()
        self.set_name("Transition Node")
        self.set_color(40, 150, 40)
        self.add_input("Previous", multi_input=True)
        self.add_output("Completion Time")
        self.add_combo_menu("tag_name", "Stage", items=DISEASE_STAGES)
        self.add_combo_menu("june_category", "JUNE Category", items=JUNE_CATEGORIES)
        self.add_text_input("tag", "Value", "0")


class TerminalStage(NGQt.BaseNode):
    __identifier__ = "symptoms"
    NODE_NAME = "TerminalStage"

    def __init__(self):
        super(TerminalStage, self).__init__()
        self.set_name("Terminal Stage")
        self.set_color(180, 40, 40)
        self.add_input("Previous", multi_input=True)
        self.add_combo_menu("tag_name", "Stage", items=DISEASE_STAGES)
        self.add_combo_menu("june_category", "JUNE Category", items=JUNE_CATEGORIES)
        self.add_text_input("tag", "Value", "0")


class UniversalTimeNode(NGQt.BaseNode):
    __identifier__ = "transitions"
    NODE_NAME = "UniversalTimeNode"

    def __init__(self):
        super(UniversalTimeNode, self).__init__()
        self.set_name("Time Distribution")
        self.set_color(220, 160, 20)

        # Ports
        self.add_input("Symptom")
        self.add_output("Next")

        # Distribution Type Selector
        self.add_combo_menu(
            "type",
            "Distribution",
            items=["constant", "normal", "lognormal", "beta", "gamma", "exponweib"],
        )

        # Parameters
        self.add_text_input("Val", "Value/Loc", text="0.0")
        self.add_text_input("scale", "Scale", text="1.0")
        self.add_text_input("a", "a", text="0.0")
        self.add_text_input("b", "b", text="0.0")
        self.add_text_input("c", "c", text="0.0")
        self.add_text_input("s", "s", text="0.0")


class NodeGraphWidget(QtW.QWidget):
    def __init__(self):
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

        self._setup_context_menu()

        # Connect signals for dynamic behavior
        self.graph.port_connected.connect(self._on_connection_created)
        self.graph.node_created.connect(self._on_node_created)
        self.graph.property_changed.connect(self._on_node_prop_changed)

    def _setup_context_menu(self):
        graph_menu = self.graph.get_context_menu("graph")

        symptom_menu = graph_menu.add_menu("Symptom Nodes")

        def create_cmd(node_class):
            node_key = node_class.__identifier__ + "." + node_class.__name__
            return lambda: self.graph.create_node(node_key)

        symptom_menu.add_command("Lowest Stage", create_cmd(DefaultLowestStage))
        symptom_menu.add_command("Transition Node", create_cmd(TransitionNode))
        symptom_menu.add_command("Terminal Stage", create_cmd(TerminalStage))

        trans_menu = graph_menu.add_menu("Transition Nodes")
        trans_menu.add_command("Time Distribution", create_cmd(UniversalTimeNode))

    def _on_connection_created(self, port_in, port_out):
        """
        Intercepts connections between two 'symptoms' nodes and inserts a UniversalTimeNode.
        """
        node_in = port_in.node()
        node_out = port_out.node()

        if node_in.type_.startswith("symptoms.") and node_out.type_.startswith(
            "symptoms."
        ):
            # Defer insertion to avoid conflicts during signal processing
            QtCore.QTimer.singleShot(
                0, lambda: self._insert_time_node(port_out, port_in)
            )

    def _insert_time_node(self, source_port, target_port):
        """
        Breaks the direct connection and inserts a TimeNode.
        """
        self.graph.clear_selection()

        source_node = source_port.node()
        target_node = target_port.node()

        # 2. Disconnect existing pipe
        source_port.disconnect_from(target_port)

        # 3. Create new node
        time_node = self.graph.create_node(
            "transitions.UniversalTimeNode", push_undo=True
        )

        # 4. Position halfway
        pos_start = source_node.pos()
        pos_end = target_node.pos()
        mid_x = (pos_start[0] + pos_end[0]) / 2
        mid_y = (pos_start[1] + pos_end[1]) / 2
        time_node.set_pos(mid_x, mid_y)

        # 5. Connect: Source -> Time -> Target
        source_port.connect_to(time_node.input(0), push_undo=True)
        time_node.output(0).connect_to(target_port, push_undo=True)

        self.graph.viewer().update()

        # 7. Initial visibility check
        self.update_node_visibility(time_node)

    def _on_node_created(self, node):
        if isinstance(node, UniversalTimeNode):
            QtCore.QTimer.singleShot(10, lambda: self.update_node_visibility(node))

    def _on_node_prop_changed(self, node, prop_name, prop_value):
        if isinstance(node, UniversalTimeNode) and prop_name == "type":
            self.update_node_visibility(node)

    def update_node_visibility(self, node):
        """
        Hides/Shows input fields based on distribution type AND resizes the node.
        """
        dist_type = node.get_property("type")

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
                widget_wrapper.setVisible(should_show)

                if hasattr(widget_wrapper, "widget"):
                    try:
                        inner_widget = widget_wrapper.widget()
                        if inner_widget:
                            inner_widget.setVisible(should_show)
                    except Exception:
                        pass

                if hasattr(widget_wrapper, "label_widget"):
                    widget_wrapper.label_widget.setVisible(should_show)
                elif hasattr(widget_wrapper, "label"):
                    widget_wrapper.label.setVisible(should_show)

                if should_show:
                    visible_count += 1

        new_height = 80 + (visible_count * 28)
        node.set_property("height", new_height, push_undo=False)
        node.update()
