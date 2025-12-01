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
    # Typer puede retornar exit code 0 o usar Exit(0)
    # Verificamos que el output contenga la versión
    assert "0.1.0" in result.stdout or "0.1.0" in str(result.output)


def test_help_command():
    """Verifica que el help principal funciona"""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "tuya-pip" in result.stdout.lower()
    assert "firewall" in result.stdout.lower()


# TODO: Agregar tests con mocks para:
# - test_install_blocked_package()
# - test_install_allowed_package()
# - test_install_with_force()
# - test_audit_blocked_package()
# - test_check_firewall_reachable()
