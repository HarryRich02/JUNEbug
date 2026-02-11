"""
PROJECT STRUCTURE AND CODE ORGANIZATION

JUNEbug - PyQt5-based GUI for JUNE Disease Configuration

================================================================================
DIRECTORY LAYOUT
================================================================================

src/
├── main.py                    # Entry point
├── app.py                     # Main window orchestration
├── configPanel.py             # Left panel: configuration forms
├── graph.py                   # Right panel: node graph editor
├── yamlLoader.py              # YAML import/export logic
└── style/
    └── theme.qss              # Qt stylesheet

================================================================================
MODULE OVERVIEW
================================================================================

main.py
-------
Entry point for the application. Run with:
  python -m main

app.py (Application Module)
---------------------------
Contains:
  - MainWindow: Main application window with split layout
    - Left panel: configuration metadata and transmission parameters
    - Right panel: node-graph disease trajectory editor
    - File menu: Import/Export YAML

Responsibilities:
  - Create and manage the main window layout
  - Handle menu actions (import/export)
  - Coordinate between config panel and graph widget
  - Load and apply stylesheet

configPanel.py (Configuration Panel Module)
-------------------------------------------
Contains:
  - DistributionEditor: Reusable widget for statistical parameters
    - Dynamic field visibility based on distribution type
    - Supports: constant, normal, lognormal, beta, gamma, exponweib
  - CollapsibleBox: Expandable accordion-style container
  - AccordionWidget: Manages multiple collapsible boxes with mutual exclusivity
  - DiseaseConfigWidget: Main left panel for disease configuration
    - Disease metadata (name, default stage, max mild tag)
    - Transmission dynamics (type and distribution parameters)

Key Data Structures:
  - DISEASE_STAGES: List of clinical stage names
  - DISTRIBUTION_TYPES: List of supported probability distributions
  - Each DistributionEditor tracks parameter values in self.inputs dict

graph.py (Graph Panel Module)
-----------------------------
Contains:
  - DefaultLowestStage: Entry point node (green)
  - TransitionNode: Intermediate stage (green)
  - TerminalStage: Final stage like "recovered" (red)
  - UniversalTimeNode: Time distribution parameters (yellow)
  - NodeGraphWidget: Container managing the node graph editor

Key Features:
  - Automatic time node insertion between symptom-to-symptom connections
  - Dynamic field visibility based on distribution type
  - Context menus for node creation
  - Auto-layout with keyboard support
  - Event wrapper for zoom/pan visibility fixes

Key Data Structures:
  - STAGE_TYPES: JUNE behavior categories
  - UniversalTimeNode.VISIBILITY_MAP: Which fields to show per distribution type

yamlLoader.py (YAML Serialization Module)
------------------------------------------
Contains:
  - NoAliasDumper: Custom YAML dumper without aliases/anchors
  - loadConfig(): Import YAML into UI and graph
  - saveConfig(): Export UI and graph to YAML
  - updateConfigPanel(): Populate form fields from YAML data
  - updateGraph(): Rebuild node graph from trajectories
  - findTrajectoriesDfs(): Extract all disease paths via depth-first search
  - Helper functions for data transformation

Responsibilities:
  - Read/write YAML configuration files
  - Transform between file format and application objects
  - Graph reconstruction with deduplication for re-entrant stages
  - Trajectory extraction and serialization

================================================================================
DATA FLOW
================================================================================

IMPORT (File -> UI & Graph):
  File (YAML)
    ↓
  yamlLoader.loadConfig()
    ├→ updateConfigPanel() → populates form fields
    ├→ updateGraph() → rebuilds node graph
    │   ├→ Create master nodes for unique stages
    │   ├→ Draw trajectory paths with time nodes
    │   └→ Auto-layout
    └→ finalizeVisibility() → adjust node heights

EXPORT (UI & Graph -> File):
  DiseaseConfigWidget + NodeGraphWidget
    ↓
  yamlLoader.saveConfig()
    ├→ Extract panel data (name, settings, transmission)
    ├→ Extract graph nodes (stages, tags, categories)
    ├→ Extract trajectories (via findTrajectoriesDfs)
    ├→ Build disease dictionary
    └→ Write YAML file

================================================================================
KEY DESIGN PATTERNS
================================================================================

1. SEPARATION OF CONCERNS
   - app.py: Window management and coordination
   - configPanel.py: Left panel UI and data gathering
   - graph.py: Right panel UI and node management
   - yamlLoader.py: File I/O and format translation

2. REUSABLE COMPONENTS
   - DistributionEditor: Generic distribution parameter widget
   - CollapsibleBox + AccordionWidget: Generic accordion pattern

3. SIGNALS AND SLOTS
   - PyQt5 signals for loose coupling (e.g., sigResize, toggled)
   - Node property changes trigger visibility updates
   - Graph signals (port_connected, node_created, property_changed)

4. DYNAMIC UI
   - DistributionEditor.updateFields() shows/hides fields per type
   - UniversalTimeNode._apply_widget_visibility() manages field visibility
   - NodeGraphWidget wraps zoom/pan events to fix visibility

5. GRAPH RECONSTRUCTION
   - Topology analysis to determine node types
   - Deduplication to prevent recursion with re-entrant stages
   - Cache key system to avoid duplicate time nodes

================================================================================
CONSTANTS AND CONFIGURATION
================================================================================

DISEASE_STAGES (configPanel.py)
  Clinical stage identifiers: recovered, exposed, mild, severe, etc.

DISTRIBUTION_TYPES (configPanel.py)
  Statistical distributions: constant, normal, lognormal, gamma, beta, exponweib
  Mapping shows required parameters for each type.

STAGE_TYPES (graph.py)
  JUNE simulator behavior categories: stay_at_home_stage, fatality_stage, etc.

UniversalTimeNode.VISIBILITY_MAP (graph.py)
  Maps distribution types to visible input field names.

================================================================================
RUNNING THE APPLICATION
================================================================================

Setup:
  python -m venv .venv
  .venv\Scripts\activate.bat          # Windows cmd
  pip install -e .

Run:
  python -m main

The application opens with:
  - Left panel: Configuration form
  - Right panel: Empty graph (add nodes via right-click context menu)
  - File menu: Import/Export YAML

================================================================================
EXAMPLE WORKFLOW
================================================================================

1. Import a disease configuration:
   File > Import YAML > select covid.yaml
   - Config panel populates with disease metadata
   - Graph displays disease trajectories

2. Edit the configuration:
   - Modify fields in the left panel
   - Right-click in graph to add/remove nodes
   - Draw connections between symptom stages
   - Time nodes auto-insert between symptom connections

3. Save the modified configuration:
   File > Export YAML > choose output location
   - Extracts all panel and graph data
   - Saves as human-readable YAML

================================================================================
TESTING
================================================================================

Example YAML files are in examples/:
  - covid19.yaml
  - measles.yaml
  - config_simulation.yaml
  - covid (export).yaml

Use these to test import/export and graph visualization.

================================================================================
DOCUMENTATION REFERENCES
================================================================================

This file: CODE_ORGANIZATION.md
  Overview of project structure and organization

Additional resources:
  - Copilot instructions: .github/copilot-instructions.md
  - PyQt5 documentation: https://doc.qt.io/qt-5/
  - NodeGraphQt: https://github.com/jchanvfx/NodeGraphQt
  - PyYAML: https://pyyaml.org/

================================================================================
"""
