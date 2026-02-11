# JUNEbug

A PyQt5-based GUI for creating and editing disease-stage configurations for the [JUNE](https://github.com/IDAS-Durham/JUNE) epidemiological simulator.

## Installation

### 1. Create Virtual Environment

```bash
python -m venv .venv
```

### 2. Activate Virtual Environment

**Windows (cmd):**
```cmd
.venv\Scripts\activate.bat
```

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -e .
```

## Running the Application

```bash
python -m main
```

The application opens with a split-panel interface:
- **Left panel**: Disease configuration (metadata, transmission parameters)
- **Right panel**: Node graph editor (visual disease trajectory design)

## Usage

### Import a Configuration

1. File > Import YAML
2. Select a YAML file (examples in `examples/`)
3. Configuration loads into both panels

### Edit Configuration

- **Left panel**: Modify disease name, stages, transmission parameters
- **Right panel**: Right-click to add nodes, drag to connect stages

### Export Configuration

1. File > Export YAML
2. Choose output location
3. Edited configuration saved to YAML

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

examples/              # Example YAML configurations
tests/                 # Test suite
```

## Documentation

- **QUICK_REFERENCE.md** - Common tasks and keyboard shortcuts
- **CODE_ORGANIZATION.md** - Project structure and module details
- **DEVELOPER_GUIDE.md** - Guide for extending the application

## Requirements

- Python 3.8+
- PyQt5
- NodeGraphQt
- PyYAML

See [pyproject.toml](pyproject.toml) for complete dependency list.

## Testing

Run the test suite:

```bash
pytest tests/
```

## License

Released under the terms in [LICENSE](LICENSE).
