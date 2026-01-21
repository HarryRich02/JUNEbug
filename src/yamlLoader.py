import yaml
import traceback
from collections import defaultdict
from PyQt5 import QtWidgets, QtCore

# Import node types for identification during export
from graph import DefaultLowestStage, TransitionNode, TerminalStage, UniversalTimeNode


# Custom dumper to disable YAML anchors/aliases
class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


def log(message):
    print(f"[JUNEbug] {message}", flush=True)


def load_config(file_path, config_panel, graph_widget):
    log(f"Loading configuration from: {file_path}")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        log(f"Error opening YAML file: {e}")
        return

    disease = data.get("disease", {})
    if not disease:
        log("Error: YAML file does not contain a 'disease' section.")
        return

    # 1. Update Config Panel
    try:
        _update_config_panel(config_panel, disease)
    except Exception as e:
        log(f"Error updating config panel: {e}")

    # 2. Update Node Graph
    try:
        _update_graph(graph_widget, disease)
        log("Graph updated and layout complete.")
    except Exception as e:
        log(f"Critical error updating graph: {e}")
        traceback.print_exc()


def _update_config_panel(panel, disease):
    panel.name_entry.setText(disease.get("name", ""))

    settings = disease.get("settings", {})
    if "default_lowest_stage" in settings:
        panel.dls_combo.setCurrentText(settings["default_lowest_stage"])
    if "max_mild_symptom_tag" in settings:
        panel.mmst_combo.setCurrentText(settings["max_mild_symptom_tag"])

    trans = disease.get("transmission", {})
    if "type" in trans:
        panel.trans_type_combo.setCurrentText(trans["type"])

    for key, editor in panel.trans_editors.items():
        if key in trans:
            dist_data = trans[key]
            dist_type = dist_data.get("type", "constant")
            editor.type_combo.setCurrentText(dist_type)
            for param, value in dist_data.items():
                if param == "type":
                    continue
                if param in editor.inputs:
                    editor.inputs[param].setText(str(value))


def _update_graph(graph_widget, disease):
    graph = graph_widget.graph
    graph.clear_session()

    symptom_tags = disease.get("symptom_tags", [])
    tag_name_to_value = {t["name"]: t["value"] for t in symptom_tags}
    trajectories = disease.get("trajectories", [])

    settings = disease.get("settings", {})
    category_reverse_map = {}
    for category in [
        "stay_at_home_stage",
        "fatality_stage",
        "recovered_stage",
        "hospitalised_stage",
        "intensive_care_stage",
        "severe_symptoms_stay_at_home_stage",
    ]:
        items = settings.get(category, [])
        if items is None:
            continue
        for item in items:
            category_reverse_map[item["name"]] = category

    is_source = set()
    is_target = set()
    all_active_tags = set()

    for traj in trajectories:
        stages = traj.get("stages", [])
        for i, stage in enumerate(stages):
            tag = stage.get("symptom_tag")
            all_active_tags.add(tag)
            if i < len(stages) - 1:
                is_source.add(tag)
            if i > 0:
                is_target.add(tag)

    nodes_cache = {}

    for tag in all_active_tags:
        if tag in is_source and tag in is_target:
            node_type = "symptoms.TransitionNode"
        elif tag in is_source:
            node_type = "symptoms.DefaultLowestStage"
        else:
            node_type = "symptoms.TerminalStage"

        node = graph.create_node(node_type, push_undo=False)
        node.set_name(tag)
        node.set_property("tag_name", tag, push_undo=False)

        # Set June Category dropdown if mapped
        if tag in category_reverse_map:
            node.set_property(
                "june_category", category_reverse_map[tag], push_undo=False
            )

        numeric_val = tag_name_to_value.get(tag, 0)
        try:
            node.set_property("tag", str(numeric_val), push_undo=False)
        except Exception:
            pass

        nodes_cache[tag] = node

    time_nodes_cache = defaultdict(list)

    for traj in trajectories:
        stages = traj.get("stages", [])
        previous_node = None
        trajectory_tag_counts = defaultdict(int)

        for i, stage in enumerate(stages):
            tag = stage.get("symptom_tag")
            trajectory_tag_counts[tag] += 1
            count = trajectory_tag_counts[tag]

            if count == 1:
                current_node = nodes_cache.get(tag)
            else:
                node_type = (
                    "symptoms.TransitionNode"
                    if i < len(stages) - 1
                    else "symptoms.TerminalStage"
                )
                current_node = graph.create_node(node_type, push_undo=False)
                current_node.set_name(f"{tag} {count}")
                current_node.set_property("tag_name", tag, push_undo=False)
                if tag in category_reverse_map:
                    current_node.set_property(
                        "june_category", category_reverse_map[tag], push_undo=False
                    )

                numeric_val = tag_name_to_value.get(tag, 0)
                try:
                    current_node.set_property("tag", str(numeric_val), push_undo=False)
                except:
                    pass
                current_node.set_color(40, 150, 250)

            if previous_node:
                comp_data = stages[i - 1].get("completion_time", {})
                cache_key = (previous_node.name(), current_node.name())

                existing_time_node = None
                for node_obj, original_data in time_nodes_cache[cache_key]:
                    if _is_data_equal(comp_data, original_data):
                        existing_time_node = node_obj
                        break

                if not existing_time_node:
                    time_node = _create_time_node(graph_widget, comp_data)
                    time_node.set_name(
                        f"{previous_node.name()} -> {current_node.name()}"
                    )
                    time_nodes_cache[cache_key].append((time_node, comp_data))
                    previous_node.output(0).connect_to(
                        time_node.input(0), push_undo=False
                    )
                    time_node.output(0).connect_to(
                        current_node.input(0), push_undo=False
                    )

            previous_node = current_node

    try:
        graph.auto_layout_nodes()
    except Exception as e:
        log(f"Auto-Layout failed: {e}")

    graph.viewer().update()
    QtCore.QTimer.singleShot(200, lambda: _finalize_visibility(graph_widget))


def _finalize_visibility(graph_widget):
    log("Running final visibility refresh...")
    graph = graph_widget.graph
    for node in graph.all_nodes():
        if node.type_ == "transitions.UniversalTimeNode":
            if hasattr(graph_widget, "update_node_visibility"):
                graph_widget.update_node_visibility(node)


def _create_time_node(graph_widget, comp_data):
    graph = graph_widget.graph
    node = graph.create_node("transitions.UniversalTimeNode", push_undo=False)
    dist_type = comp_data.get("type", "constant")
    node.set_property("type", dist_type, push_undo=False)

    for k, v in comp_data.items():
        if k == "type":
            continue
        prop_name = "Val" if k in ["value", "loc"] else k
        try:
            node.set_property(prop_name, str(v), push_undo=False)
        except Exception:
            pass
    return node


def _is_data_equal(data_a, data_b):
    if data_a.get("type") != data_b.get("type"):
        return False
    keys_a = set(k for k in data_a.keys() if k != "type")
    keys_b = set(k for k in data_b.keys() if k != "type")
    if keys_a != keys_b:
        return False
    for k in keys_a:
        try:
            if abs(float(data_a[k]) - float(data_b[k])) > 1e-7:
                return False
        except:
            if str(data_a[k]) != str(data_b[k]):
                return False
    return True


def save_config(file_path, config_panel, graph_widget):
    """Exports current UI and Graph state to JUNE YAML format."""
    panel_data = config_panel.getConfigData()

    # Base structure with categorized settings
    output = {
        "disease": {
            "name": panel_data.get("name"),
            "settings": {
                "default_lowest_stage": panel_data.get("default_lowest_stage"),
                "max_mild_symptom_tag": panel_data.get("max_mild_symptom_tag"),
                "stay_at_home_stage": [],
                "fatality_stage": [],
                "recovered_stage": [],
                "hospitalised_stage": [],
                "intensive_care_stage": [],
                "severe_symptoms_stay_at_home_stage": [],
            },
            "symptom_tags": [],
            "infection_outcome_rates": [],
            "rate_to_tag_mapping": {},
            "unrated_tags": [],
            "trajectories": [],
            "transmission": panel_data.get("transmission"),
        }
    }

    graph = graph_widget.graph
    all_nodes = graph.all_nodes()

    # 1. Reconstruct symptom_tags and populate settings lists
    unique_tags = {"healthy": -1}
    for node in [n for n in all_nodes if n.type_.startswith("symptoms.")]:
        tag_name = node.get_property("tag_name")
        unique_tags[tag_name] = int(node.get_property("tag"))

        # Populate categorized settings lists
        category = node.get_property("june_category")
        if category and category != "none":
            target_list = output["disease"]["settings"][category]
            if not any(item["name"] == tag_name for item in target_list):
                target_list.append({"name": tag_name})

    output["disease"]["symptom_tags"] = [
        {"name": k, "value": v} for k, v in unique_tags.items()
    ]

    # 2. Extract Trajectories
    start_nodes = [n for n in all_nodes if isinstance(n, DefaultLowestStage)]
    trajectories = []
    for start_node in start_nodes:
        _find_trajectories_dfs(start_node, [], trajectories)

    # Deduplicate trajectories
    unique_trajectories = []
    seen_paths = set()
    for traj in trajectories:
        if traj["description"] not in seen_paths:
            unique_trajectories.append(traj)
            seen_paths.add(traj["description"])
    output["disease"]["trajectories"] = unique_trajectories

    with open(file_path, "w", encoding="utf-8") as f:
        yaml.dump(
            output, f, Dumper=NoAliasDumper, sort_keys=False, default_flow_style=False
        )


def _find_trajectories_dfs(current_node, current_path_stages, trajectories_list):
    tag_name = current_node.get_property("tag_name")
    stage_entry = {"symptom_tag": tag_name}

    if (
        isinstance(current_node, TerminalStage)
        or not current_node.output(0).connected_ports()
    ):
        stage_entry["completion_time"] = {"type": "constant", "value": 0.0}
        full_path = current_path_stages + [stage_entry]
        trajectories_list.append(
            {
                "description": " => ".join([s["symptom_tag"] for s in full_path]),
                "stages": full_path,
            }
        )
        return

    for port in current_node.output(0).connected_ports():
        time_node = port.node()
        if isinstance(time_node, UniversalTimeNode):
            stage_entry["completion_time"] = _extract_dist_data(time_node)
            for next_port in time_node.output(0).connected_ports():
                _find_trajectories_dfs(
                    next_port.node(),
                    current_path_stages + [stage_entry],
                    trajectories_list,
                )


def _extract_dist_data(node):
    dist_type = node.get_property("type")
    data = {"type": dist_type}
    mapping = {
        "constant": [("Val", "value")],
        "normal": [("Val", "loc"), ("scale", "scale")],
        "lognormal": [("s", "s"), ("Val", "loc"), ("scale", "scale")],
        "beta": [("a", "a"), ("b", "b"), ("Val", "loc"), ("scale", "scale")],
        "gamma": [("a", "a"), ("Val", "loc"), ("scale", "scale")],
        "exponweib": [("a", "a"), ("c", "c"), ("Val", "loc"), ("scale", "scale")],
    }
    for prop, yaml_key in mapping.get(dist_type, []):
        val = node.get_property(prop)
        try:
            data[yaml_key] = float(val) if "." in str(val) else int(val)
        except:
            data[yaml_key] = val
    return data
