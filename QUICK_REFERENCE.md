# JUNEbug - Quick Reference

## Running the Application

```bash
python -m main
```

## Project Structure

```
src/
├── main.py           # Entry point
├── app.py            # Main window
├── configPanel.py    # Left panel (forms)
├── graph.py          # Right panel (graph editor)
├── yamlLoader.py     # YAML import/export
└── style/
    └── theme.qss     # Stylesheet
```

## Module Overview

| File | Purpose | Key Classes |
|------|---------|-------------|
| app.py | Window management | `MainWindow` |
| configPanel.py | Configuration UI | `DiseaseConfigWidget`, `DistributionEditor`, `AccordionWidget` |
| graph.py | Graph editor | `NodeGraphWidget`, `UniversalTimeNode`, `DefaultLowestStage` |
| yamlLoader.py | File I/O | `loadConfig()`, `saveConfig()` |

## Common Tasks

### Import a disease configuration
1. File > Import YAML
2. Select a YAML file from `examples/`
3. Config panel and graph populate automatically

### Edit configuration
- **Left panel**: Modify disease name, stages, transmission parameters
- **Right panel**: Right-click to add nodes, drag to connect

### Export configuration
1. File > Export YAML
2. Choose output location
3. Edited configuration saved to YAML

### Add a new stage type
1. Add to `DISEASE_STAGES` list in configPanel.py
2. Stage automatically appears in dropdowns

### Add a new distribution type
1. Add to `DISTRIBUTION_TYPES` in configPanel.py
2. Add parameter mapping in `DistributionEditor.updateFields()`
3. Add to `UniversalTimeNode.VISIBILITY_MAP` in graph.py
4. Add extraction in `extractDistData()` in yamlLoader.py

## Documentation

- **CODE_ORGANIZATION.md** - Detailed project structure
- **DEVELOPER_GUIDE.md** - How to develop/extend the code
- **REFACTORING_SUMMARY.md** - Summary of recent improvements

## File Format

The YAML format follows the JUNE disease specification:

```yaml
disease:
  name: "Disease Name"
  settings:
    default_lowest_stage: "exposed"
    max_mild_symptom_tag: "mild"
    stay_at_home_stage: []
    # ... other JUNE categories ...
  
  symptom_tags:
    - name: "healthy"
      value: -1
    - name: "exposed"
      value: 0
    # ...
  
  transmission:
    type: "gamma"
    max_infectiousness:
      type: "lognormal"
      s: 0.0
      loc: 0.0
      scale: 1.0
    # ...
  
  trajectories:
    - description: "exposed => mild => recovered"
      stages:
        - symptom_tag: "exposed"
          completion_time:
            type: "gamma"
            a: 2.0
            loc: 0.0
            scale: 1.0
        - symptom_tag: "mild"
          completion_time: ...
```

## Keyboard Shortcuts (NodeGraphQt)

- **Right-click**: Context menu for node creation
- **Drag**: Pan the graph
- **Scroll**: Zoom in/out
- **Delete**: Remove selected node
- **A**: Auto-layout

## Example Files

Located in `examples/`:
- `covid19.yaml`
- `measles.yaml`
- `config_simulation.yaml`

Use these for testing import/export functionality.

## Troubleshooting

### App won't start
- Check Python version (requires 3.7+)
- Verify PyQt5 is installed: `pip install -e .`
- Check error message in console

### Nodes not showing in graph
- Ensure node type is registered in `NodeGraphWidget.__init__()`
- Right-click on empty graph space for context menu

### YAML won't load
- Check file format (must have 'disease' root key)
- Verify required fields are present
- Check console for error message

### Graph nodes disappear on zoom
- This is being fixed by event wrappers
- Zoom in/out again to refresh visibility

## Dependencies

- Python 3.7+
- PyQt5
- NodeGraphQt
- PyYAML

Install all: `pip install -e .`

## Contact & Support

See `.github/copilot-instructions.md` for additional context on the JUNE simulator integration.
