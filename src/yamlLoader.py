from typing import Dict, List, Any, Optional, Tuple, Set
import yaml
import traceback
from collections import defaultdict
from PyQt5 import QtWidgets, QtCore
import NodeGraphQt as NGQt

# Node identification for graph building
from graph import DefaultLowestStage, TransitionNode, TerminalStage, UniversalTimeNode
from configPanel import DiseaseConfigWidget


class NoAliasDumper(yaml.SafeDumper):
    """Prevents YAML aliases/anchors to ensure the file is human-readable."""

    def ignore_aliases(self, data: Any) -> bool:
        return True


def log(message: str) -> None:
    """Standardized logging for the loader."""
    print(f"[JUNEbug] {message}", flush=True)


def loadConfig(path: str, panel: DiseaseConfigWidget, widget: Any) -> None:
    """Main entry for importing JUNE YAML configurations."""
    log(f"Loading: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        log(f"Error opening YAML file: {e}")
        return

    disease = data.get("disease", {})
    if disease:
        try:
            updateConfigPanel(panel, disease)
            updateGraph(widget, disease)
            log("Import complete.")
        except Exception as e:
            log(f"Critical error: {e}")
            traceback.print_exc()


def updateConfigPanel(panel: DiseaseConfigWidget, disease: Dict[str, Any]) -> None:
    """Populates metadata fields in the configuration panel."""
    panel.name_entry.setText(disease.get("name", ""))
    sets = disease.get("settings", {})
    if "default_lowest_stage" in sets:
        panel.dls_combo.setCurrentText(sets["default_lowest_stage"])
    if "max_mild_symptom_tag" in sets:
        panel.mmst_combo.setCurrentText(sets["max_mild_symptom_tag"])
    trans = disease.get("transmission", {})
    if "type" in trans:
        panel.trans_type_combo.setCurrentText(trans["type"])
    for k, ed in panel.trans_editors.items():
        if k in trans:
            d_data = trans[k]
            ed.type_combo.setCurrentText(d_data.get("type", "constant"))
            for p, v in d_data.items():
                if p != "type" and p in ed.inputs:
                    ed.inputs[p].setText(str(v))


def updateGraph(widget: Any, disease: Dict[str, Any]) -> None:
    """
    Translates YAML trajectories into a deduplicated node graph.
    Prevents recursion errors by using numbered copies for re-entrant tags.
    """
    graph = widget.graph
    graph.clear_session()
    trajectories = disease.get("trajectories", [])
    tag_vals = {t["name"]: t["value"] for t in disease.get("symptom_tags", [])}

    sets = disease.get("settings", {})
    c_map: Dict[str, str] = {}
    categories = [
        "stay_at_home_stage",
        "fatality_stage",
        "recovered_stage",
        "hospitalised_stage",
        "intensive_care_stage",
        "severe_symptoms_stay_at_home_stage",
    ]
    for cat in categories:
        for item in sets.get(cat, []):
            c_map[item["name"]] = cat

    # Topology analysis
    is_s, is_t, all_tags = set(), set(), set()
    for tr in trajectories:
        st = tr.get("stages", [])
        for i, s in enumerate(st):
            tag = s.get("symptom_tag")
            all_tags.add(tag)
            if i < len(st) - 1:
                is_s.add(tag)
            if i > 0:
                is_t.add(tag)

    # Master Clinical Nodes
    master_nodes: Dict[str, NGQt.BaseNode] = {}
    for tag in all_tags:
        if tag in is_s and tag in is_t:
            n_type = "symptoms.TransitionNode"
        elif tag in is_s:
            n_type = "symptoms.DefaultLowestStage"
        else:
            n_type = "symptoms.TerminalStage"

        n = graph.create_node(n_type, push_undo=False)
        n.set_name(tag)
        if tag in c_map:
            n.set_property("stage_type", c_map[tag], push_undo=False)
        try:
            n.set_property("tag", str(tag_vals.get(tag, 0)), push_undo=False)
        except:
            pass
        master_nodes[tag] = n

    # Draw paths with global distribution deduplication
    dist_cache: Dict[Tuple[str, str, str], NGQt.BaseNode] = {}

    for tr in trajectories:
        st = tr.get("stages", [])
        prev_node = None
        path_tag_counts = defaultdict(int)

        for i, stage in enumerate(st):
            tag = stage.get("symptom_tag")
            path_tag_counts[tag] += 1

            # Prevent cycles for auto-layout if a tag repeats in a trajectory
            if path_tag_counts[tag] == 1:
                curr_node = master_nodes[tag]
            else:
                n_type = (
                    "symptoms.TransitionNode"
                    if i < len(st) - 1
                    else "symptoms.TerminalStage"
                )
                curr_node = graph.create_node(n_type, push_undo=False)
                curr_node.set_name(f"{tag} {path_tag_counts[tag]}")
                if tag in c_map:
                    curr_node.set_property("stage_type", c_map[tag], push_undo=False)
                curr_node.set_property(
                    "tag", str(tag_vals.get(tag, 0)), push_undo=False
                )
                curr_node.set_color(40, 150, 250)

            if prev_node:
                comp = st[i - 1].get("completion_time", {})
                params_key = str(sorted(comp.items()))
                cache_key = (prev_node.name(), curr_node.name(), params_key)

                if cache_key not in dist_cache:
                    time_n = createTimeNode(widget, comp)
                    prev_node.output(0).connect_to(time_n.input(0), push_undo=False)
                    time_n.output(0).connect_to(curr_node.input(0), push_undo=False)
                    dist_cache[cache_key] = time_n
            prev_node = curr_node

    QtWidgets.QApplication.processEvents()
    try:
        # FIX: Explicitly pass the list of nodes
        graph.auto_layout_nodes(graph.all_nodes())
        graph.fit_to_selection()
    except Exception as e:
        log(f"Auto-Layout failed: {e}")

    QtCore.QTimer.singleShot(200, lambda: finalizeVisibility(widget))


def finalizeVisibility(widget: Any) -> None:
    """Updates scaling of nodes once physically placed."""
    for n in widget.graph.all_nodes():
        if isinstance(n, UniversalTimeNode):
            widget.updateNodeVisibility(n)


def createTimeNode(widget: Any, comp: Dict[str, Any]) -> NGQt.BaseNode:
    """Creates a TimeDistribution node with numerical parameters."""
    n = widget.graph.create_node("transitions.UniversalTimeNode", push_undo=False)
    n.set_property("type", comp.get("type", "constant"), push_undo=False)
    for k, v in comp.items():
        if k != "type":
            prop = "Val" if k in ["value", "loc"] else k
            try:
                n.set_property(prop, str(v), push_undo=False)
            except:
                pass
    return n


def saveConfig(path: str, panel: DiseaseConfigWidget, widget: Any) -> None:
    """Exports UI state and Graph paths back into JUNE YAML."""
    p_data = panel.getConfigData()
    output = {
        "disease": {
            "name": p_data.get("name"),
            "settings": {
                "default_lowest_stage": p_data.get("default_lowest_stage"),
                "max_mild_symptom_tag": p_data.get("max_mild_symptom_tag"),
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
            "transmission": p_data.get("transmission"),
        }
    }

    nodes = widget.graph.all_nodes()
    tags: Dict[str, int] = {"healthy": -1}
    for n in [x for x in nodes if x.type_.startswith("symptoms.")]:
        tag_name = n.name().split(" ")[0]
        tags[tag_name] = int(n.get_property("tag"))
        cat = n.get_property("stage_type")
        if cat and cat != "none":
            t_list = output["disease"]["settings"][cat]
            if not any(x["name"] == tag_name for x in t_list):
                t_list.append({"name": tag_name})

    output["disease"]["symptom_tags"] = [
        {"name": k, "value": v} for k, v in tags.items()
    ]

    paths: List[Dict[str, Any]] = []
    for start in [x for x in nodes if isinstance(x, DefaultLowestStage)]:
        findTrajectoriesDfs(start, [], paths)

    unique_traj, seen = [], set()
    for p in paths:
        if p["description"] not in seen:
            unique_traj.append(p)
            seen.add(p["description"])
    output["disease"]["trajectories"] = unique_traj

    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(
            output, f, Dumper=NoAliasDumper, sort_keys=False, default_flow_style=False
        )


def findTrajectoriesDfs(
    n: NGQt.BaseNode, st: List[Dict[str, Any]], acc: List[Dict[str, Any]]
) -> None:
    """Recursive search to discover all valid trajectories through the node network."""
    tag_name = n.name().split(" ")[0]
    entry = {"symptom_tag": tag_name}
    if isinstance(n, TerminalStage) or not n.output(0).connected_ports():
        entry["completion_time"] = {"type": "constant", "value": 0.0}
        full = st + [entry]
        acc.append(
            {
                "description": " => ".join([s["symptom_tag"] for s in full]),
                "stages": full,
            }
        )
        return
    for port in n.output(0).connected_ports():
        time_node = port.node()
        if isinstance(time_node, UniversalTimeNode):
            entry["completion_time"] = extractDistData(time_node)
            for next_p in time_node.output(0).connected_ports():
                findTrajectoriesDfs(next_p.node(), st + [entry], acc)


def extractDistData(n: UniversalTimeNode) -> Dict[str, Any]:
    """Retrieves numerical distribution properties from a node."""
    dt = n.get_property("type")
    data, mapping = {"type": dt}, {
        "constant": [("Val", "value")],
        "normal": [("Val", "loc"), ("scale", "scale")],
        "lognormal": [("s", "s"), ("Val", "loc"), ("scale", "scale")],
        "beta": [("a", "a"), ("b", "b"), ("Val", "loc"), ("scale", "scale")],
        "gamma": [("a", "a"), ("Val", "loc"), ("scale", "scale")],
        "exponweib": [("a", "a"), ("c", "c"), ("Val", "loc"), ("scale", "scale")],
    }
    for p, y in mapping.get(dt, []):
        v = n.get_property(p)
        try:
            data[y] = float(v) if "." in str(v) else int(v)
        except:
            data[y] = v
    return data
