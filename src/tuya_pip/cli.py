"""
CLI principal de tuya-pip.
"""
import typer
import subprocess
import sys
import asyncio
import os
import re
from typing import Optional, List
from pathlib import Path
from .validator import FirewallValidator
from . import ui

app = typer.Typer(
    name="tuya-pip",
    help="🛡️ Secure pip wrapper with firewall validation",
    add_completion=False
)


def get_firewall_url() -> str:
    """Obtiene la URL del firewall desde variable de entorno o usa la por defecto"""
    return os.getenv("TUYA_FIREWALL_URL", "http://127.0.0.1:8000")


def parse_package_spec(package_spec: str) -> tuple[str, Optional[str]]:
    """
    Parsea una especificación de paquete para extraer nombre y versión.
    
    Args:
        package_spec: Especificación del paquete (ej: "requests", "keras==3.11.2", "django>=4.0")
    
    Returns:
        Tuple con (nombre_paquete, versión o None)
    """
    # Manejar diferentes formatos: ==, >=, <=, >, <, ~=
    for separator in ["==", ">=", "<=", ">", "<", "~="]:
        if separator in package_spec:
            parts = package_spec.split(separator)
            return parts[0].strip(), parts[1].strip() if separator == "==" else None
    
    return package_spec.strip(), None


async def validate_packages(packages: List[str], firewall_url: str) -> bool:
    """
    Valida una lista de paquetes contra el firewall.
    
    Args:
        packages: Lista de especificaciones de paquetes
        firewall_url: URL del firewall
    
    Returns:
        True si todos los paquetes pasan, False si alguno es bloqueado
    """
    validator = FirewallValidator(firewall_url)
    
    try:
        for package_spec in packages:
            package_name, version = parse_package_spec(package_spec)
            
            with ui.show_checking_spinner(package_spec):
                result = await validator.validate_package(package_name, version)
            
            if result.status == "block":
                audit_url = f"{firewall_url}/blocked/{package_name}"
                version_str = version if version else "latest"
                ui.show_blocked_panel(
                    package=package_name,
                    version=version_str,
                    reason=result.reason,
                    audit_url=audit_url
                )
                return False
            else:
                ui.show_success(package_spec)
        
        return True
    finally:
        await validator.close()


def parse_requirements_file(requirements_file: str) -> List[str]:
    """
    Lee un archivo requirements.txt y extrae los paquetes.
    
    Args:
        requirements_file: Ruta al archivo requirements.txt
    
    Returns:
        Lista de especificaciones de paquetes
    """
    packages = []
    
    try:
        with open(requirements_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Ignorar líneas vacías y comentarios
                if line and not line.startswith('#'):
                    # Remover comentarios inline
                    if '#' in line:
                        line = line.split('#')[0].strip()
                    packages.append(line)
    except FileNotFoundError:
        ui.show_error(f"Requirements file not found: {requirements_file}")
        sys.exit(1)
    except Exception as e:
        ui.show_error(f"Error reading requirements file: {str(e)}")
        sys.exit(1)
    
    return packages


@app.command()
def install(
    packages: List[str] = typer.Argument(None, help="Package(s) to install"),
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
    index_url: Optional[str] = typer.Option(
        None,
        "--index-url",
        "-i",
        help="Base URL of the Python Package Index"
    ),
    extra_index_url: Optional[str] = typer.Option(
        None,
        "--extra-index-url",
        help="Extra URLs of package indexes to use in addition to --index-url"
    ),
    trusted_host: Optional[str] = typer.Option(
        None,
        "--trusted-host",
        help="Mark this host as trusted"
    ),
    no_deps: bool = typer.Option(
        False,
        "--no-deps",
        help="Don't install package dependencies"
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
        tuya-pip install keras --index-url http://127.0.0.1:8000/simple/
    """
    # Determinar lista de paquetes a instalar
    packages_to_install = []
    
    if requirement:
        # Instalación desde requirements.txt
        packages_to_install = parse_requirements_file(requirement)
    elif packages:
        # Paquetes especificados directamente
        packages_to_install = list(packages)
    else:
        ui.show_error("No packages specified. Use 'tuya-pip install <package>' or '-r requirements.txt'")
        sys.exit(1)
    
    if not packages_to_install:
        ui.show_error("No packages to install")
        sys.exit(1)
    
    # Si --force, saltar validación
    if force:
        ui.show_warning("Skipping security validation (--force flag used)")
    else:
        # Validar paquetes contra el firewall
        firewall_url = get_firewall_url()
        all_passed = asyncio.run(validate_packages(packages_to_install, firewall_url))
        
        if not all_passed:
            ui.show_error("Installation aborted due to security policy violations")
            sys.exit(1)
    
    # Construir comando pip
    ui.show_installing(", ".join(packages_to_install))
    
    pip_args = ["pip", "install"]
    
    if requirement:
        pip_args.extend(["-r", requirement])
    else:
        pip_args.extend(packages_to_install)
    
    if upgrade:
        pip_args.append("--upgrade")
    
    if index_url:
        pip_args.extend(["--index-url", index_url])
    
    if extra_index_url:
        pip_args.extend(["--extra-index-url", extra_index_url])
    
    if trusted_host:
        pip_args.extend(["--trusted-host", trusted_host])
    
    if no_deps:
        pip_args.append("--no-deps")
    
    # Ejecutar pip install con streaming para capturar errores en tiempo real
    try:
        process = subprocess.Popen(
            pip_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        blocked_packages = []
        
        # Leer la salida línea por línea
        for line in process.stdout:
            print(line, end='')
            
            # Detectar errores 403 y extraer el nombre del paquete bloqueado con su versión
            if "HTTP error 403" in line or "403 Client Error: Forbidden" in line:
                # Extraer nombre y versión del paquete de la URL
                # Ejemplo: http://127.0.0.1:8000/pypi/packages/numpy-2.3.5-cp313-cp313-win_amd64.whl.metadata
                match = re.search(r'/packages/([a-zA-Z0-9_-]+)-([\d\.]+[a-zA-Z0-9\.]*)', line)
                if match:
                    pkg_name = match.group(1).lower()
                    pkg_version = match.group(2)
                    pkg_info = f"{pkg_name}=={pkg_version}"
                    if pkg_info not in blocked_packages:
                        blocked_packages.append(pkg_info)
        
        process.wait()
        
        # Si hubo paquetes bloqueados, mostrar mensaje informativo
        if blocked_packages and process.returncode != 0:
            ui.console.print()
            ui.show_error(f"Firewall blocked {len(blocked_packages)} package(s)")
            
            for pkg in blocked_packages:
                ui.console.print(f"  [red]✗[/red] {pkg}")
            
            ui.console.print()
            ui.show_info(f"For details, run: tuya-pip audit {blocked_packages[0]}")
        
        sys.exit(process.returncode)
    except Exception as e:
        ui.show_error(f"Failed to execute pip: {str(e)}")
        sys.exit(1)


@app.command()
def audit(
    package: str = typer.Argument(..., help="Package name to audit")
):
    """
    Check if a package is blocked and why.
    
    Examples:
        tuya-pip audit keras
        tuya-pip audit tensorflow
        tuya-pip audit numpy==2.3.5
    """
    # Extraer solo el nombre del paquete (remover versión si existe)
    package_name, _ = parse_package_spec(package)
    
    firewall_url = get_firewall_url()
    validator = FirewallValidator(firewall_url)
    
    async def run_audit():
        try:
            with ui.show_checking_spinner(package_name):
                blocked_info = await validator.get_blocked_info(package_name)
            
            if blocked_info.get("status") == "blocked":
                reasons = blocked_info.get("reasons", [])
                reason_text = "; ".join(reasons) if reasons else "No specific reason provided"
                blocked_count = blocked_info.get("blocked_versions", 0)
                
                ui.show_blocked_panel(
                    package=package_name,
                    version=f"{blocked_count} version(s)",
                    reason=reason_text,
                    audit_url=f"{firewall_url}/blocked/{package_name}"
                )
                
                # Mostrar detalles adicionales si están disponibles
                if "blocked_versions_list" in blocked_info:
                    versions = blocked_info["blocked_versions_list"]
                    if versions:
                        ui.console.print(f"\n[bold]Blocked versions:[/bold] {', '.join(versions)}")
                
            elif blocked_info.get("status") == "allowed":
                ui.console.print(f"\n✅ [green]Package '{package_name}' is allowed[/green]")
                ui.console.print(f"[dim]No versions are currently blocked by the firewall[/dim]")
            elif blocked_info.get("status") == "error":
                error_msg = blocked_info.get("error", "Unknown error")
                ui.show_error(f"Error checking package: {error_msg}")
            else:
                ui.show_info(f"Package status: {blocked_info.get('status', 'unknown')}")
        finally:
            await validator.close()
    
    asyncio.run(run_audit())


@app.command()
def check(
    firewall_url: Optional[str] = typer.Option(
        None,
        "--url",
        help="Firewall API URL (defaults to TUYA_FIREWALL_URL env var or http://127.0.0.1:8000)"
    )
):
    """
    Check if the firewall is reachable.
    
    Examples:
        tuya-pip check
        tuya-pip check --url http://localhost:8000
    """
    url = firewall_url or get_firewall_url()
    validator = FirewallValidator(url)
    
    async def run_check():
        try:
            with ui.show_checking_spinner("firewall connectivity"):
                is_reachable = await validator.check_connectivity()
            
            if is_reachable:
                ui.console.print(f"\n✅ [green]Firewall is reachable at {url}[/green]")
            else:
                ui.console.print(f"\n❌ [red]Firewall is not reachable at {url}[/red]")
                ui.console.print(f"[dim]Make sure python-package-firewall is running[/dim]")
                sys.exit(1)
        finally:
            await validator.close()
    
    asyncio.run(run_check())


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        help="Show version"
    )
):
    """
    🛡️ tuya-pip: Secure pip wrapper with firewall validation
    
    Validates packages against python-package-firewall before installation.
    """
    if version:
        ui.console.print("tuya-pip version 0.1.0")
        raise typer.Exit(0)


if __name__ == "__main__":
    app()
