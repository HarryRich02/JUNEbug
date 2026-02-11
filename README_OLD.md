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

- Linux / macOS:

  ```bash
  pip3 install -e .
  ```

4. Run the application from the repository root

- Windows:

  ```cmd
  python -m main
  ```

- Linux / macOS:

  ```bash
  python3 -m main
  ```

## Requirements

- Python 3.8+
- PyQt5
- NodeGraphQt

Dependencies are declared in [pyproject.toml](pyproject.toml).

## License

This project is released under the terms in [LICENSE](LICENSE).
