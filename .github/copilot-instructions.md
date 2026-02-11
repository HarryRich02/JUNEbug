# JUNEbug Copilot Instructions

## Project Overview

JUNEbug is a PyQt5-based GUI for creating and editing disease-stage configurations for the JUNE epidemiological simulator. It combines a form-based configuration panel with a node-graph editor for visual trajectory design.

## Architecture

### Core Components

1. **[app.py](src/app.py)** - Main application orchestrator
   - `MainWindow`: Manages the two-panel layout (config left, graph right)
   - Handles File menu (Import/Export YAML)
   - Loads QSS theme styling from `src/style/theme.qss`

2. **[configPanel.py](src/configPanel.py)** - Left panel for disease metadata
   - `DiseaseConfigWidget`: Main container with metadata and transmission settings
   - `DistributionEditor`: Reusable sub-widget for statistical parameters (constant, normal, lognormal, beta, gamma, exponweib)
   - `CollapsibleBox`: Accordion-style UI with animated expand/collapse
   - Maps form fields to YAML disease section

3. **[graph.py](src/graph.py)** - Right panel for disease trajectory visualization
   - Uses NodeGraphQt library for node-graph interface
   - Four node types:
     - `DefaultLowestStage`: Entry point (green)
     - `TransitionNode`: Intermediate states (green)
     - `TerminalStage`: Final states like "recovered" (red)
     - `UniversalTimeNode`: Time distribution parameters (yellow)
   - Each node stores `stage_type` (JUNE logic mapping) and `tag` (severity value)

4. **[yamlLoader.py](src/yamlLoader.py)** - Import/export logic
   - `loadConfig()`: Reads YAML → updates configPanel → rebuilds graph
   - `saveConfig()`: Exports configPanel + graph structure to YAML
   - `NoAliasDumper`: Custom YAML dumper to avoid aliases/anchors
   - Graph rebuilding uses deduplication to prevent recursion with re-entrant tags

## Data Flow

```
YAML File
    ↓
yamlLoader.loadConfig()
    ↓
    ├→ updateConfigPanel() → DiseaseConfigWidget
    │  (name, settings, transmission params)
    │
    └→ updateGraph() → NodeGraphWidget
       (trajectories → nodes + connections)
```

**Export flow is reversed**: Forms and graph → YAML serialization.

## Key Patterns & Conventions

### YAML Structure

- Root: `disease` object containing:
  - `name`: String identifier
  - `settings`: Contains `default_lowest_stage`, `max_mild_symptom_tag`
  - `transmission`: Maps distribution types to parameters
  - `symptom_tags`: List of `{name, value}` pairs
  - `trajectories`: List of `{name, stages, symptom_tags}` defining paths

### Node Naming & Stage Types

- Disease stage constants: `DISEASE_STAGES` in configPanel (~11 states)
- Stage type mapping: `STAGE_TYPES` in graph.py (~7 JUNE logic categories)
- Node name = clinical identifier (e.g., "exposed", "mild")
- Node `stage_type` = JUNE behavior category (e.g., "stay_at_home_stage")

### Distribution Parameters

- `DistributionEditor.updateFields()` dynamically shows fields based on type
- Field mapping in configPanel.py:
  - `constant`: [] (no parameters)
  - `normal`: [loc, scale]
  - `lognormal`: [s, loc, scale]
  - `gamma`: [a, loc, scale]
  - `beta`: [a, b, loc, scale]
  - `exponweib`: [a, c, loc, scale]

### PyQt5 Patterns

- Use `pyqtSignal()` for component communication (e.g., `configPanel.DistributionEditor.sigResize`)
- Use `QPropertyAnimation` for smooth UI transitions
- Styling via external QSS file, referenced by `setObjectName()` (e.g., `"collapsibleBtn"`)
- Context menus from NodeGraphQt: `self.graph.get_context_menu("graph")`

## Developer Workflows

### Setup & Run

```bash
python -m venv .venv
.venv\Scripts\activate.bat          # Windows cmd
pip install -e .                     # Install in editable mode
python -m main                       # Run application
```

### Testing

- pytest configured in `pyproject.toml` with `testpaths = ["tests"]`
- Current test file `tests/yamlLoader.py` is empty
- Dev dependencies: `pytest`, `black`

### Code Quality

- Format with `black` before commits
- No strict linting enforced yet; follow PEP 8

### Example YAML Files

- Located in `examples/` directory for manual testing
- Use to validate import/export behavior and graph rebuilding

## Integration Points

### External Dependencies

- **PyQt5**: GUI framework (widgets, signals, animations)
- **NodeGraphQt**: Node-graph visualization library
- **PyYAML**: Configuration serialization
- All declared in `pyproject.toml`

### Signal/Slot Connections

- Graph signals: `port_connected`, `node_created`, `property_changed` → handlers in NodeGraphWidget
- Cross-component sync: yamlLoader bridges configPanel ↔ graph updates

## Common Task Patterns

**Adding a new distribution type**:

- Add to `DISTRIBUTION_TYPES` in configPanel.py
- Add parameter mapping to `DistributionEditor.updateFields()`
- Update yamlLoader serialization if needed

**Adding a new node type**:

- Create class inheriting `NGQt.BaseNode` in graph.py
- Register in `NodeGraphWidget.__init__()` via `self.graph.register_nodes()`
- Update yamlLoader to handle serialization

**Styling changes**:

- Edit `src/style/theme.qss` directly (loads on app startup)
- Reference widget `setObjectName()` values in QSS selectors

## Known Limitations & Implementation Notes

### UniversalTimeNode Widget Visibility

- `UniversalTimeNode` hides/shows input fields based on the selected distribution type (see `_apply_widget_visibility()`)
- To prevent visual flicker during zoom/pan, `NodeGraphWidget` hooks into mouse wheel and drag events to re-apply visibility (see `_createWheelEventWrapper()`, `_createMouseMoveEventWrapper()`)
- **Limitation**: NodeGraphQt's `auto_layout_nodes()` uses node bounding rects which include hidden widgets. Auto-layout will therefore space nodes based on their full potential size, not their current visible size. This is a NodeGraphQt design limitation - the library doesn't expose a way to customize bounding rect calculations for hidden content.

## Codebase Structure Notes

- All source in `src/` with flat module layout (no sub-packages)
- Imports use relative module names (e.g., `import graph`, `import configPanel`)
- Entry point: `main.py` calls `runApp()` from app.py
- No separate domain/business logic layer; mostly UI coupling
