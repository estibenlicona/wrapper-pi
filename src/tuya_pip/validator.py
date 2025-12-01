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
        self.firewall_url = firewall_url.rstrip('/')
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
        1. Consulta GET /simple/{package}/ para verificar acceso
        2. Si retorna 403 -> paquete bloqueado por firewall
        3. Si retorna 404 -> paquete no existe en PyPI
        4. Si retorna 200 -> consultar /blocked/{package} para detalles
        """
        package_name = package.lower()
        
        try:
            # Primero intentamos obtener el índice del paquete
            response = await self.client.get(f"{self.firewall_url}/simple/{package_name}/")
            
            if response.status_code == 403:
                # Paquete bloqueado - obtener detalles del bloqueo
                blocked_info = await self.get_blocked_info(package_name)
                reasons = blocked_info.get("reasons", [])
                reason_text = "; ".join(reasons) if reasons else "Package is blocked by firewall policy"
                
                return ValidationResult(
                    status="block",
                    reason=reason_text,
                    details=blocked_info
                )
            elif response.status_code == 404:
                return ValidationResult(
                    status="block",
                    reason="Package not found in PyPI",
                    details={"package": package_name, "error": "not_found"}
                )
            elif response.status_code == 200:
                # Paquete existe, verificar si hay versiones específicas bloqueadas
                if version:
                    blocked_info = await self.get_blocked_info(package_name)
                    if blocked_info.get("status") == "blocked":
                        blocked_versions = blocked_info.get("blocked_versions_list", [])
                        if version in blocked_versions or "*" in blocked_versions:
                            reasons = blocked_info.get("reasons", [])
                            version_reason = next(
                                (r for r in reasons if version in r), 
                                f"Version {version} is blocked"
                            )
                            return ValidationResult(
                                status="block",
                                reason=version_reason,
                                details=blocked_info
                            )
                
                return ValidationResult(
                    status="allow",
                    reason="Package passed security validation",
                    details={"package": package_name}
                )
            else:
                return ValidationResult(
                    status="block",
                    reason=f"Unexpected response from firewall: {response.status_code}",
                    details={"package": package_name, "status_code": response.status_code}
                )
                
        except httpx.ConnectError:
            return ValidationResult(
                status="block",
                reason=f"Cannot connect to firewall at {self.firewall_url}",
                details={"package": package_name, "error": "connection_error"}
            )
        except httpx.TimeoutException:
            return ValidationResult(
                status="block",
                reason="Firewall validation timeout",
                details={"package": package_name, "error": "timeout"}
            )
        except Exception as e:
            return ValidationResult(
                status="block",
                reason=f"Validation error: {str(e)}",
                details={"package": package_name, "error": str(e)}
            )
    
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
        package_name = package.lower()
        
        try:
            response = await self.client.get(f"{self.firewall_url}/blocked/{package_name}")
            
            if response.status_code == 404:
                # Paquete no está bloqueado
                return {
                    "package": package_name,
                    "status": "allowed",
                    "blocked_versions": 0,
                    "reasons": []
                }
            elif response.status_code == 200:
                data = response.json()
                # Parsear la respuesta para extraer información útil
                return {
                    "package": package_name,
                    "status": "blocked",
                    "blocked_versions": data.get("blocked_versions", 0),
                    "blocked_versions_list": data.get("blocked_versions_list", []),
                    "reasons": data.get("reasons", []),
                    "raw_data": data
                }
            else:
                return {
                    "package": package_name,
                    "status": "unknown",
                    "error": f"Unexpected status code: {response.status_code}"
                }
                
        except httpx.ConnectError:
            return {
                "package": package_name,
                "status": "error",
                "error": f"Cannot connect to firewall at {self.firewall_url}"
            }
        except Exception as e:
            return {
                "package": package_name,
                "status": "error",
                "error": str(e)
            }
    
    async def check_connectivity(self) -> bool:
        """
        Verifica si el firewall es accesible.
        
        Returns:
            bool: True si el firewall responde, False en caso contrario
        """
        try:
            response = await self.client.get(f"{self.firewall_url}/simple/", timeout=5.0)
            return response.status_code in (200, 404)  # Ambos indican que el servidor responde
        except Exception:
            return False
    
    async def close(self):
        """Cierra el cliente HTTP"""
        await self.client.aclose()
