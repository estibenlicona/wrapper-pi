# Especificación de API para python-package-firewall

Este documento describe cómo debe responder el firewall API para que `tuya-pip` funcione correctamente.

## Base URL

Por defecto: `http://127.0.0.1:8000`

Se puede configurar mediante la variable de entorno `TUYA_FIREWALL_URL`.

---

## Endpoints requeridos

### 1. GET `/simple/{package}/`

Retorna el índice de versiones disponibles de un paquete (formato PyPI simple).

#### Respuestas esperadas:

**✅ Paquete permitido (200 OK)**
```html
<!DOCTYPE html>
<html>
<head><title>Links for {package}</title></head>
<body>
<h1>Links for {package}</h1>
<a href="...">package-1.0.0.tar.gz</a><br/>
<a href="...">package-1.0.1.tar.gz</a><br/>
</body>
</html>
```

**❌ Paquete bloqueado (403 Forbidden)**
```json
{
  "error": "Package blocked by security policy",
  "package": "keras",
  "reason": "Vulnerabilities found"
}
```

**❌ Paquete no existe (404 Not Found)**
```json
{
  "error": "Package not found",
  "package": "nonexistent-package"
}
```

---

### 2. GET `/blocked/{package}`

Retorna información detallada sobre por qué un paquete está bloqueado.

#### Respuestas esperadas:

**🚫 Paquete bloqueado (200 OK)**
```json
{
  "package": "keras",
  "status": "blocked",
  "blocked_versions": 2,
  "blocked_versions_list": ["3.11.2", "3.11.1"],
  "reasons": [
    "Version 3.11.2: Vulnerabilities found: CVE-2025-12060, CVE-2025-99999",
    "Version 3.11.1: Unmaintained package"
  ]
}
```

**✅ Paquete permitido (404 Not Found)**
```json
{
  "package": "requests",
  "status": "allowed",
  "message": "Package is not blocked"
}
```

---

### 3. GET `/simple/` (Opcional - para health check)

Endpoint raíz para verificar conectividad del firewall.

#### Respuestas esperadas:

**✅ Firewall activo (200 OK)**
```html
<!DOCTYPE html>
<html>
<head><title>Simple Index</title></head>
<body>
<h1>Simple Index</h1>
</body>
</html>
```

O simplemente:
```json
{
  "status": "ok",
  "service": "python-package-firewall"
}
```

---

## Flujo de validación de tuya-pip

### Escenario 1: Instalación normal
```bash
tuya-pip install requests
```

1. `tuya-pip` hace `GET /blocked/requests`
   - Si retorna 404 → paquete permitido, continuar
   - Si retorna 200 con status "blocked" → mostrar error y abortar

2. Si pasa validación, ejecuta:
   ```bash
   pip install requests
   ```

### Escenario 2: Instalación con índice personalizado
```bash
tuya-pip install keras==3.11.2 --index-url http://127.0.0.1:8000/simple/
```

1. `tuya-pip` hace `GET /blocked/keras`
   - Si `blocked_versions_list` contiene "3.11.2" → mostrar error y abortar
   - Si no está en la lista → continuar

2. Si pasa validación, ejecuta:
   ```bash
   pip install keras==3.11.2 --index-url http://127.0.0.1:8000/simple/
   ```

### Escenario 3: Comando audit
```bash
tuya-pip audit keras
```

1. `tuya-pip` hace `GET /blocked/keras`
2. Muestra la información en un panel formateado con Rich

---

## Formato del panel de error

Cuando un paquete es bloqueado, `tuya-pip` muestra:

```
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

El `reason` se extrae del campo `reasons` de la respuesta JSON (se unen con "; ").

---

## Códigos de estado HTTP

| Endpoint | Status | Significado |
|----------|--------|-------------|
| `/simple/{package}/` | 200 | Paquete existe y está permitido |
| `/simple/{package}/` | 403 | Paquete bloqueado por política |
| `/simple/{package}/` | 404 | Paquete no existe en PyPI |
| `/blocked/{package}` | 200 | Paquete tiene versiones bloqueadas |
| `/blocked/{package}` | 404 | Paquete no tiene bloqueos |

---

## Ejemplos de implementación

### Paquete completamente bloqueado
```json
GET /blocked/malicious-package

{
  "package": "malicious-package",
  "status": "blocked",
  "blocked_versions": 999,
  "blocked_versions_list": ["*"],
  "reasons": ["Package identified as malware"]
}
```

### Bloqueo de versiones específicas
```json
GET /blocked/tensorflow

{
  "package": "tensorflow",
  "status": "blocked",
  "blocked_versions": 3,
  "blocked_versions_list": ["2.0.0", "2.0.1", "2.1.0"],
  "reasons": [
    "Version 2.0.0: CVE-2020-15211",
    "Version 2.0.1: CVE-2020-15211",
    "Version 2.1.0: License violation"
  ]
}
```

### Paquete sin bloqueos
```json
GET /blocked/requests

HTTP 404 Not Found
{
  "package": "requests",
  "status": "allowed",
  "message": "Package is not blocked"
}
```

---

## Notas importantes

1. **Los nombres de paquetes deben ser case-insensitive**: `tuya-pip` convierte todo a lowercase antes de consultar
2. **El campo `blocked_versions_list` es crítico**: Se usa para validar versiones específicas
3. **Los `reasons` deben ser legibles**: Se muestran directamente al usuario
4. **Soportar CORS**: Si el firewall se ejecuta en un servidor diferente
5. **Timeout**: `tuya-pip` espera máximo 30 segundos por respuesta
6. **Bloqueo a nivel de índice vs archivos**:
   - Si un paquete tiene **todas** o la **mayoría** de versiones bloqueadas, considere retornar **403 Forbidden** en `/simple/{package}/` para prevenir que pip descargue metadata
   - Si solo **versiones específicas** están bloqueadas, retorne **200 OK** en `/simple/{package}/` pero bloquee los archivos individuales con **403**
   - Esto evita que los usuarios vean errores técnicos durante la instalación de dependencias

---

## Recomendaciones para bloqueo efectivo

### Escenario 1: Paquete completamente malicioso
```
GET /simple/malicious-package/  → 403 Forbidden
GET /blocked/malicious-package  → 200 OK con todas las versiones bloqueadas
```

### Escenario 2: Solo versiones específicas vulnerables
```
GET /simple/tensorflow/         → 200 OK (permite ver el índice)
GET /blocked/tensorflow         → 200 OK con versiones específicas bloqueadas
GET /pypi/packages/tensorflow-2.0.0-...whl → 403 Forbidden (bloquea archivo específico)
```

### Escenario 3: Dependencia crítica bloqueada
Si `numpy-2.3.5` es la única versión disponible y está bloqueada:
```
GET /simple/numpy/              → 403 Forbidden (evita metadata inútil)
GET /blocked/numpy              → 200 OK con versión bloqueada
```

---

## Testing rápido

```bash
# 1. Verificar conectividad
tuya-pip check

# 2. Auditar un paquete
tuya-pip audit keras

# 3. Intentar instalar paquete bloqueado
tuya-pip install keras==3.11.2 --index-url http://127.0.0.1:8000/simple/

# 4. Instalar paquete permitido
tuya-pip install requests
```
