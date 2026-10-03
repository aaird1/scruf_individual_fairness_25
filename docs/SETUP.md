# Running SCRUF-D Experiments

Setup and usage guide for running these experiments. Replaces the Installation and
Running the Experiment sections of the README once complete.

## Requirements

- Python 3.10 or newer. Earlier versions will not work; numpy 2.x requires 3.10+.
- A C compiler (optional). Builds a faster metrics library. Without it the code uses
  a pure-Python implementation that produces the same results.

### Installing Python 3.10+

| Platform | Command |
|---|---|
| macOS (Homebrew) | `brew install python@3.11` |
| Ubuntu / Debian | `sudo apt install python3.11 python3.11-venv` |
| Any platform | Installer from https://www.python.org/downloads/ |
| conda | `conda create -n scruf python=3.11` |

Check your version:

```bash
python3 --version
```

## 1. Create a virtual environment

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate          # macOS, Linux
.venv\Scripts\activate             # Windows
python -m pip install --upgrade pip setuptools wheel
```

Check the version inside the environment:

```bash
python --version
```

With conda, activate your conda environment instead of creating a venv. The remaining
steps are the same.
