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
    content = f"""
[bold cyan]Package:[/bold cyan] {package}
[bold cyan]Version:[/bold cyan] {version if version else 'any'}

[bold yellow]Reason:[/bold yellow] {reason}

[bold]For details:[/bold] [dim]curl {audit_url}[/dim]
"""
    
    panel = Panel.fit(
        content.strip(),
        title="🚫 [bold red]Installation Blocked[/bold red]",
        border_style="red",
        padding=(1, 2)
    )
    console.print()
    console.print(panel)
    console.print()


def show_success(package: str):
    """
    Muestra mensaje de éxito cuando pasa validación.
    
    Output: ✅ [green]Security checks passed for package[/green]
    """
    console.print(f"✅ [green]Security checks passed for {package}[/green]")


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
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        progress.add_task(
            description=f"🔍 Validating [cyan]{package}[/cyan] against security policies...",
            total=None
        )
        yield


def show_error(message: str):
    """Muestra mensaje de error genérico"""
    console.print(f"[red]❌ {message}[/red]")


def show_info(message: str):
    """Muestra mensaje informativo"""
    console.print(f"[blue]ℹ️  {message}[/blue]")


def show_warning(message: str):
    """Muestra mensaje de advertencia"""
    console.print(f"[yellow]⚠️  {message}[/yellow]")


def show_installing(package: str):
    """Muestra mensaje cuando se está instalando un paquete"""
    console.print(f"📦 [bold]Installing {package}...[/bold]")
