# esri-indexer
A little web app that indexes geographic data layers available via ESRI REST endpoints so they are searchable.

## Setup

This project uses [uv](https://docs.astral.sh/uv/) for dependency management and Python environment handling.

### Prerequisites

Install uv:
```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd esri-indexer
```

2. Install dependencies:
```bash
uv sync
```

3. Activate the virtual environment:
```bash
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate     # On Windows
```

### Development

Install development dependencies:
```bash
uv sync --all-extras
```

Set up pre-commit hooks:
```bash
uv run pre-commit install
```

Run the application:
```bash
uv run python app.py
```

### Code Quality

This project uses several code quality tools:

Run all pre-commit hooks:
```bash
uv run pre-commit run --all-files
```

The pre-commit hooks will automatically run on each commit to ensure code quality.
