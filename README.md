# tuya-pip

🛡️ Secure pip wrapper with security validation via [python-package-firewall](https://github.com/estibenlicona/python-package-firewall).

## Features

- ✅ Validates packages against security policies before installation
- 🚫 Blocks vulnerable, unmaintained, or non-OSI licensed packages
- 📊 Beautiful terminal UI with rich formatting
- 🔍 Audit command to check why packages are blocked
- 🎯 Drop-in replacement for `pip install`

## Installation

```bash
# With uv (recommended)
uv pip install tuya-pip

# With pip
pip install tuya-pip
```

## Usage

### Install packages with validation

```bash
# Basic install
tuya-pip install requests

# Specific version
tuya-pip install keras==3.11.2

# From requirements file
tuya-pip install -r requirements.txt

# Upgrade package
tuya-pip install requests --upgrade

# Skip validation (use with caution)
tuya-pip install keras --force
```

### Audit a package

```bash
tuya-pip audit keras
```

### Check firewall connectivity

```bash
tuya-pip check
```

## Requirements

- Python 3.10+
- Running instance of [python-package-firewall](https://github.com/estibenlicona/python-package-firewall) at `http://127.0.0.1:8000`

## Configuration

Set the firewall URL via environment variable:

```bash
export TUYA_FIREWALL_URL=http://localhost:8000
tuya-pip install requests
```

Or use the `--url` flag:

```bash
tuya-pip check --url http://custom-firewall:8000
```

## Example Output

### Blocked package

```
🔍 Validating keras==3.11.2 against security policies...

╭─────────────────── 🚫 Installation Blocked ────────────────────╮
│                                                                 │
│  Package: keras                                                 │
│  Version: 3.11.2                                                │
│                                                                 │
│  Reason: Vulnerabilities found: CVE-2025-12060, CVE-2025-99... │
│                                                                 │
│  For details: curl http://127.0.0.1:8000/blocked/keras         │
│                                                                 │
╰─────────────────────────────────────────────────────────────────╯
```

### Allowed package

```
🔍 Validating requests against security policies...
✅ Security checks passed
📦 Installing requests...
[pip output]
```

## Development

```bash
# Clone the repo
git clone https://github.com/estibenlicona/tuya-pip
cd tuya-pip

# Create virtual environment with uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
uv pip install -e .

# Run tests
pytest

# Format code
ruff format .
```

## License

MIT
