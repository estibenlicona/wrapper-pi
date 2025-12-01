# Prompt para generar `tuya-pip` con UV

Crea un proyecto Python llamado `tuya-pip` usando `uv` como gestor de paquetes y dependencias.

## Objetivo del proyecto

`tuya-pip` es un CLI wrapper sobre `pip` que intercepta instalaciones de paquetes y valida contra un firewall de seguridad (`python-package-firewall`) antes de permitir la instalación. Proporciona mensajes de error claros y formatados cuando un paquete es bloqueado por políticas de seguridad.

---

## 1. Estructura del proyecto

```
tuya-pip/
├── pyproject.toml
├── README.md
├── .gitignore
├── .python-version
├── src/
│   └── tuya_pip/
│       ├── __init__.py
│       ├── cli.py          # Entry point del CLI con typer
│       ├── validator.py    # Cliente HTTP para comunicación con firewall API
│       └── ui.py           # Formateo de mensajes con rich
└── tests/
    ├── __init__.py
    ├── test_cli.py
    └── test_validator.py
```

---

## 2. Configuración del proyecto (pyproject.toml)

```toml
[project]
name = "tuya-pip"
version = "0.1.0"
description = "CLI wrapper for pip with security validation via python-package-firewall"
authors = [
    {name = "Estiben Licona", email = "estiben@example.com"}
]
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}

dependencies = [
    "httpx>=0.27.0",
    "rich>=13.7.0",
    "typer>=0.12.0",
]

[project.scripts]
tuya-pip = "tuya_pip.cli:app"

[project.urls]
Homepage = "https://github.com/estibenlicona/tuya-pip"
Repository = "https://github.com/estibenlicona/tuya-pip"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-mock>=3.12.0",
    "ruff>=0.1.0",
]

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

---

## 3. Validador (src/tuya_pip/validator.py)

Implementa un cliente HTTP asíncrono que se comunique con el firewall API:

```python
"""
Cliente HTTP para validación de paquetes contra python-package-firewall.
"""
import httpx
from typing import Optional
from dataclasses import dataclass

@dataclass
class ValidationResult:
    """Resultado de validación de un paquete"""
    status: str  # "allow" | "block"
    reason: str
    details: dict

class FirewallValidator:
    """
    Cliente para comunicarse con python-package-firewall API.
    
    Endpoints utilizados:
    - GET /simple/{package}/  - Obtener índice de versiones
    - GET /blocked/{package}  - Obtener detalles de bloqueo
    """
    
    def __init__(self, firewall_url: str = "http://127.0.0.1:8000"):
        self.firewall_url = firewall_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def validate_package(
        self, 
        package: str, 
        version: Optional[str] = None
    ) -> ValidationResult:
        """
        Valida un paquete contra el firewall intentando obtener su índice.
        
        Args:
            package: Nombre del paquete (ej: "requests")
            version: Versión específica (opcional, ej: "2.32.0")
        
        Returns:
            ValidationResult con status, reason y details
        
        Lógica:
        1. Consulta GET /simple/{package}/ para verificar si existe
        2. Si retorna 404 -> paquete no existe en PyPI
        3. Si retorna 200 -> paquete existe (la validación real se hace en descarga)
        4. Para validación específica de versión, consulta /blocked/{package}
        """
        # TODO: Implementar
        # - Hacer request a /simple/{package}/
        # - Manejar errores 404, 403, 500
        # - Si hay versión específica, consultar /blocked/{package}
        # - Retornar ValidationResult
        pass
    
    async def get_blocked_info(self, package: str) -> dict:
        """
        Obtiene información detallada de por qué un paquete está bloqueado.
        
        Args:
            package: Nombre del paquete
        
        Returns:
            dict con estructura:
            {
                "package": "keras",
                "status": "blocked",
                "blocked_versions": 1,
                "reasons": [
                    "Version 3.11.2: Vulnerabilities found: CVE-2025-12060, ..."
                ]
            }
        """
        # TODO: Implementar
        # - Hacer request a /blocked/{package}
        # - Parsear respuesta JSON
        # - Manejar caso de paquete no bloqueado
        pass
    
    async def close(self):
        """Cierra el cliente HTTP"""
        await self.client.aclose()
```

---

## 4. UI con Rich (src/tuya_pip/ui.py)

Crea funciones para mostrar mensajes formateados con `rich`:

```python
"""
Utilidades para mostrar mensajes formateados en consola con rich.
"""
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from contextlib import contextmanager

console = Console()

def show_blocked_panel(package: str, version: str, reason: str, audit_url: str):
    """
    Muestra un panel rojo cuando un paquete es bloqueado.
    
    Args:
        package: Nombre del paquete
        version: Versión bloqueada
        reason: Razón del bloqueo
        audit_url: URL para consultar detalles
    
    Output esperado:
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
    """
    # TODO: Implementar con Panel.fit()
    # - Usar border_style="red"
    # - Formatear texto con [bold], [cyan], [yellow]
    # - Incluir todos los campos
    pass

def show_success(package: str):
    """
    Muestra mensaje de éxito cuando pasa validación.
    
    Output: ✅ [green]Security checks passed for package[/green]
    """
    # TODO: Implementar
    pass

@contextmanager
def show_checking_spinner(package: str):
    """
    Context manager que muestra un spinner mientras valida.
    
    Uso:
        with show_checking_spinner("requests"):
            # hacer validación
            pass
    
    Output: 🔍 Validating requests against security policies... [spinner]
    """
    # TODO: Implementar con Progress y SpinnerColumn
    pass

def show_error(message: str):
    """Muestra mensaje de error genérico"""
    # TODO: Implementar con console.print("[red]...")
    pass

def show_info(message: str):
    """Muestra mensaje informativo"""
    # TODO: Implementar con console.print("[blue]...")
    pass
```

---

## 5. Entry point del CLI (src/tuya_pip/cli.py)

Implementa el CLI usando `typer`:

```python
"""
CLI principal de tuya-pip.
"""
import typer
import subprocess
import sys
import asyncio
from typing import Optional, List
from .validator import FirewallValidator
from . import ui

app = typer.Typer(
    name="tuya-pip",
    help="🛡️ Secure pip wrapper with firewall validation",
    add_completion=False
)

validator = FirewallValidator()

@app.command()
def install(
    packages: List[str] = typer.Argument(..., help="Package(s) to install"),
    force: bool = typer.Option(
        False, 
        "--force", 
        "-f",
        help="Skip security validation (use with caution)"
    ),
    upgrade: bool = typer.Option(
        False,
        "--upgrade",
        "-U",
        help="Upgrade package to the newest available version"
    ),
    requirement: Optional[str] = typer.Option(
        None,
        "--requirement",
        "-r",
        help="Install from the given requirements file"
    ),
):
    """
    Install packages with security validation.
    
    Examples:
        tuya-pip install requests
        tuya-pip install keras==3.11.2
        tuya-pip install -r requirements.txt
        tuya-pip install requests --upgrade
        tuya-pip install keras --force  # Skip validation
    
    Flujo:
    1. Si --force: ejecutar pip directamente
    2. Si -r requirements.txt: validar cada línea del archivo
    3. Para cada paquete:
       a. Mostrar spinner de validación
       b. Consultar firewall API
       c. Si bloqueado: mostrar panel de error y abortar
       d. Si permitido: continuar
    4. Si todos pasan: ejecutar pip install con argumentos originales
    """
    # TODO: Implementar
    # - Manejar caso de --force
    # - Manejar caso de -r requirements.txt
    # - Para cada paquete: asyncio.run(validator.validate_package())
    # - Si alguno falla: ui.show_blocked_panel() y sys.exit(1)
    # - Si todos pasan: subprocess.run(["pip", "install"] + args)
    pass

@app.command()
def audit(
    package: str = typer.Argument(..., help="Package name to audit")
):
    """
    Check if a package is blocked and why.
    
    Examples:
        tuya-pip audit keras
        tuya-pip audit tensorflow
    
    Output:
    - Si está bloqueado: mostrar detalles con ui.show_blocked_panel()
    - Si no está bloqueado: mostrar mensaje de éxito
    """
    # TODO: Implementar
    # - asyncio.run(validator.get_blocked_info(package))
    # - Mostrar resultado formateado
    pass

@app.command()
def check(
    firewall_url: str = typer.Option(
        "http://127.0.0.1:8000",
        "--url",
        help="Firewall API URL"
    )
):
    """
    Check if the firewall is reachable.
    
    Example:
        tuya-pip check
        tuya-pip check --url http://localhost:8000
    
    Output:
    ✅ Firewall is reachable at http://127.0.0.1:8000
    ❌ Firewall is not reachable
    """
    # TODO: Implementar
    # - Hacer GET a /simple/ para verificar conectividad
    # - Mostrar resultado con ui.show_success() o ui.show_error()
    pass

@app.callback()
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version",
        is_eager=True
    )
):
    """
    🛡️ tuya-pip: Secure pip wrapper with firewall validation
    
    Validates packages against python-package-firewall before installation.
    """
    if version:
        console.print("tuya-pip version 0.1.0")
        raise typer.Exit()

if __name__ == "__main__":
    app()
```

---

## 6. README.md

```markdown
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
```

---

## 7. Tests (tests/test_cli.py)

```python
"""
Tests para el CLI de tuya-pip.
"""
import pytest
from typer.testing import CliRunner
from tuya_pip.cli import app

runner = CliRunner()

def test_install_command_exists():
    """Verifica que el comando install existe"""
    result = runner.invoke(app, ["install", "--help"])
    assert result.exit_code == 0
    assert "Install packages with security validation" in result.stdout

def test_audit_command_exists():
    """Verifica que el comando audit existe"""
    result = runner.invoke(app, ["audit", "--help"])
    assert result.exit_code == 0
    assert "Check if a package is blocked" in result.stdout

def test_check_command_exists():
    """Verifica que el comando check existe"""
    result = runner.invoke(app, ["check", "--help"])
    assert result.exit_code == 0
    assert "Check if the firewall is reachable" in result.stdout

def test_version_flag():
    """Verifica que --version funciona"""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.stdout

# TODO: Agregar tests con mocks para:
# - test_install_blocked_package()
# - test_install_allowed_package()
# - test_install_with_force()
# - test_audit_blocked_package()
# - test_check_firewall_reachable()
```

---

## 8. .gitignore

```
# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
.Python
build/
dist/
*.egg-info/
.eggs/

# Virtual environments
.venv/
venv/
ENV/

# Testing
.pytest_cache/
.coverage
htmlcov/

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# UV
uv.lock
```

---

## 9. Instrucciones de inicialización

Ejecuta estos comandos para crear el proyecto:

```bash
# Inicializar proyecto con uv
uv init tuya-pip
cd tuya-pip

# Crear estructura de carpetas
mkdir -p src/tuya_pip tests

# Agregar dependencias
uv add httpx rich typer
uv add --dev pytest pytest-asyncio pytest-mock ruff

# Crear archivos base
touch src/tuya_pip/__init__.py
touch src/tuya_pip/cli.py
touch src/tuya_pip/validator.py
touch src/tuya_pip/ui.py
touch tests/__init__.py
touch tests/test_cli.py

# Instalar en modo editable
uv pip install -e .

# Verificar instalación
tuya-pip --help
```

---

## 10. Características adicionales opcionales

Si quieres extender la funcionalidad, considera agregar:

### 10.1. Comando `tuya-pip list-blocked`
Muestra todos los paquetes bloqueados actualmente

### 10.2. Comando `tuya-pip config`
Permite configurar la URL del firewall permanentemente

### 10.3. Integración con `.env`
Cargar configuración desde archivo `.env`:
```env
TUYA_FIREWALL_URL=http://127.0.0.1:8000
TUYA_AUTO_UPGRADE=true
```

### 10.4. Modo batch
Validar múltiples paquetes en paralelo:
```bash
tuya-pip install requests httpx fastapi --parallel
```

### 10.5. Logging
Guardar historial de validaciones:
```bash
tuya-pip install keras  # Logs guardados en ~/.tuya-pip/logs/
```

---

## Notas finales

- **Prioriza la simplicidad**: El MVP debe cubrir solo `install` y `audit`
- **Manejo de errores robusto**: El firewall puede estar caído, manejar ese caso
- **Mensajes claros**: La UX es el valor diferenciador de esta herramienta
- **Tests mínimos**: Al menos smoke tests para los comandos principales
- **Documentación**: README claro con ejemplos visuales

Este proyecto debe integrarse perfectamente con `python-package-firewall` y proporcionar una experiencia de usuario superior al usar pip directamente con el proxy.
