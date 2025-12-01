"""
Tests para el validador de tuya-pip.
"""
import pytest
from tuya_pip.validator import FirewallValidator, ValidationResult


@pytest.mark.asyncio
async def test_validator_initialization():
    """Verifica que el validador se inicializa correctamente"""
    validator = FirewallValidator("http://localhost:8000")
    assert validator.firewall_url == "http://localhost:8000"
    await validator.close()


@pytest.mark.asyncio
async def test_validator_strips_trailing_slash():
    """Verifica que el validador elimina slashes al final de la URL"""
    validator = FirewallValidator("http://localhost:8000/")
    assert validator.firewall_url == "http://localhost:8000"
    await validator.close()


# TODO: Agregar tests con mocks para:
# - test_validate_package_allowed()
# - test_validate_package_blocked()
# - test_validate_package_not_found()
# - test_get_blocked_info()
# - test_check_connectivity()
