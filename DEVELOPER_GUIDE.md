# JUNEbug Developer Guide

## Quick Start

### Setup
```bash
python -m venv .venv
.venv\Scripts\activate.bat      # Windows cmd
pip install -e .
```

### Run
```bash
python -m main
```

## Architecture Overview

JUNEbug has a simple, modular structure with clear separation of concerns:

```
┌─────────────────────────────────────┐
│         MainWindow (app.py)         │
├────────────────┬────────────────────┤
│                │                    │
│  configPanel   │     graph.py       │
│  (left panel)  │  (right panel)     │
│                │                    │
│  - Forms       │  - Nodes           │
│  - Accordion   │  - Connections     │
│  - Dropdowns   │  - Auto-layout     │
└────────────────┴────────────────────┘
         ↕                ↕
    yamlLoader.py (YAML I/O)
```

## Module Responsibilities

### app.py
- **MainWindow**: Creates and manages the main window layout
- Creates left (config) and right (graph) panels
- Handles File menu actions (Import/Export)
- Loads stylesheet

**Key class**: `MainWindow`

### configPanel.py
- **DistributionEditor**: Generic widget for statistical parameters
  - Dynamically shows/hides fields based on distribution type
  - Converts input to dictionary for serialization
- **CollapsibleBox**: Single expandable container with animation
- **AccordionWidget**: Manages multiple collapsible boxes
- **DiseaseConfigWidget**: Main left panel
  - Disease metadata (name, stages, thresholds)
  - Transmission dynamics configuration

**Key classes**: `DiseaseConfigWidget`, `DistributionEditor`, `AccordionWidget`

### graph.py
- **Node classes**: Four node types for the graph editor
  - `DefaultLowestStage`: Entry point (no input)
  - `TransitionNode`: Intermediate (input and output)
  - `TerminalStage`: Final state (no output)
  - `UniversalTimeNode`: Time distribution parameters
- **NodeGraphWidget**: Container for the graph
  - Manages node creation and connections
  - Auto-inserts time nodes between symptom connections
  - Handles visibility of time node parameters
  - Wraps zoom/pan events to fix visibility

**Key classes**: `NodeGraphWidget`, `UniversalTimeNode`, `DefaultLowestStage`

### yamlLoader.py
- **loadConfig()**: Entry point for import
  - Reads YAML file
  - Populates config panel
  - Rebuilds graph from trajectories
- **saveConfig()**: Entry point for export
  - Extracts all data from UI and graph
  - Builds YAML structure
  - Writes to file
- Helper functions:
  - `updateConfigPanel()`: Populate form fields
  - `updateGraph()`: Rebuild graph visualization
  - `findTrajectoriesDfs()`: Extract disease paths
  - `createTimeNode()`: Create time distribution node

**Key functions**: `loadConfig()`, `saveConfig()`, `findTrajectoriesDfs()`

## Common Tasks

### Adding a new disease stage

1. Add to `DISEASE_STAGES` in configPanel.py:
```python
DISEASE_STAGES: List[str] = [
    "recovered",
    # ...existing stages...
    "my_new_stage",  # ADD HERE
]
```

2. The stage automatically appears in:
   - "Default Lowest Stage" dropdown
   - "Max Mild Symptom Tag" dropdown
   - Graph node name dropdown

### Adding a new distribution type

1. Add to `DISTRIBUTION_TYPES` in configPanel.py:
```python
DISTRIBUTION_TYPES: List[str] = [
    # ...existing types...
    "my_distribution",  # ADD HERE
]
```

2. Add parameter mapping in `DistributionEditor.updateFields()`:
```python
fields = {
    # ...existing mappings...
    "my_distribution": ["param1", "param2"],  # ADD HERE
}.get(dist_type, [])
```

3. Add to `UniversalTimeNode.VISIBILITY_MAP` in graph.py:
```python
VISIBILITY_MAP = {
    # ...existing mappings...
    "my_distribution": ["Val", "param1", "param2"],  # ADD HERE
}
```

4. Add extraction logic in `extractDistData()` in yamlLoader.py:
```python
param_mapping = {
    # ...existing mappings...
    "my_distribution": [("Val", "loc"), ("param1", "param1"), ("param2", "param2")],  # ADD HERE
}
```

### Adding a new JUNE behavior category

1. Add to `STAGE_TYPES` in graph.py:
```python
STAGE_TYPES: List[str] = [
    # ...existing types...
    "my_behavior_category",  # ADD HERE
]
```

2. Add extraction logic in `updateGraph()` in yamlLoader.py:
```python
categories = [
    # ...existing categories...
    "my_behavior_category",  # ADD HERE
]
```

### Styling UI elements

QSS stylesheet at `src/style/theme.qss` controls appearance. Objects named in code with `setObjectName()`:

```python
# In configPanel.py
title.setObjectName("configTitle")      # References #configTitle in QSS
btn.setObjectName("collapsibleBtn")     # References #collapsibleBtn in QSS
```

Edit theme.qss to style these objects:
```css
#configTitle {
    font-size: 14pt;
    font-weight: bold;
}

#collapsibleBtn {
    background-color: #f0f0f0;
}
```

## Key Design Decisions

### Why separate nodes from NodeGraphWidget?
Node classes (`DefaultLowestStage`, `TransitionNode`, etc.) inherit from `NGQt.BaseNode` and represent the graph elements. `NodeGraphWidget` is the container that manages them. This separation allows:
- Clean node definitions
- Easy to add new node types
- Separate visualization logic

### Why DistributionEditor instead of inline?
`DistributionEditor` is reused 6 times in the transmission section. Making it reusable reduces code duplication and ensures consistency.

### Why UniversalTimeNode.VISIBILITY_MAP?
Persisting visibility across redraws requires the node to know which fields should be visible. NodeGraphQt's LOD rendering sometimes hides widgets, so we re-apply visibility after zoom/pan events.

### Why deduplication in graph rebuild?
When a stage appears multiple times in a trajectory, only the first uses the "master" node; later occurrences create numbered copies. This prevents circular layout issues while maintaining trajectory accuracy.

## Testing

### Manual Testing
1. Open the application
2. Try importing an example YAML from `examples/`
3. Verify the config panel populates correctly
4. Verify the graph displays trajectories
5. Modify some values
6. Export to a new YAML file
7. Re-import to verify round-trip works

### Syntax Checking
```bash
python -m py_compile src/app.py src/configPanel.py src/graph.py src/yamlLoader.py
```

### Module Imports
```bash
python -c "import app; import configPanel; import graph; import yamlLoader; print('OK')"
```

## Troubleshooting

### "Module not found" error
Make sure you're running from the `src` directory or that src is in PYTHONPATH.

### Graph nodes not appearing
- Check that node types are registered in `NodeGraphWidget.__init__()`
- Verify the identifier matches: `f"{node_class.__identifier__}.{node_class.__name__}"`

### Visibility of time node fields not updating
- The event wrappers for zoom/pan may not be triggering
- Check `NodeGraphWidget._createWheelEventWrapper()` and `_createMouseMoveEventWrapper()`

### YAML export fails
- Check file permissions
- Verify the output path exists
- Look for error in console output

## Code Style

- Use type hints on function arguments and returns
- Document public methods with docstrings
- Use meaningful variable names
- Keep methods focused and small
- Extract constants to the top of files
- Use f-strings for formatting

## Future Improvements

- Add undo/redo for graph operations
- Add validation for required fields
- Add keyboard shortcuts for common operations
- Add graph search/filter
- Add trajectory simulation/visualization
- Add unit tests
- Add save/load session state (not just YAML config)
