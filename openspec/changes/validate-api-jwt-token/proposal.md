# Proposal

## Why

El [Issue #25 (HU-01)](https://github.com/user-bcp-student15/ai-labs/issues/25) confirma que la API espera un token legado y no verifica criptográficamente el JWT que emite auth. Sin validar firma, expiración e identidad, las rutas protegidas no pueden confiar en la identidad recibida; resolverlo permite interoperar con el login actual y evita aceptar identidades no verificadas.

## What Changes

- Agregar el comportamiento verificable de autenticación de API para aceptar el JWT HS256 emitido conforme al contrato actual de `POST /auth/login`, validar su firma y expiración y usar únicamente la identidad verificada.
- **BREAKING:** dejar de aceptar el formato legado Base64 en las rutas protegidas. Se decidió priorizar la verificación criptográfica sobre la compatibilidad con ese formato.
- Rechazar credenciales ausentes o tokens malformados, alterados o expirados con `401`, preservando el cuerpo JSON 401 observado actualmente en la API.
- Preservar el status y la forma de respuesta exitosa de `GET /api/tasks` y de las rutas existentes que comparten su autenticación.
- Mantener sin cambios el contrato documentado de `POST /auth/login`: respuesta 200 y JSON con `token`, `expiresIn`, `user` y `debug`; JWT HS256 con claims `sub`, `role`, `iat` y `exp`; vigencia actual de 3600 segundos. La web continúa enviando el token con `Authorization: Bearer`.
- La credencial de validación se proporciona externamente; las verificaciones usan exclusivamente valores ficticios.

## Capabilities

### New Capabilities

- `api-token-authentication`: aceptación de JWT autenticados y verificación de identidad en las rutas protegidas de la API.

### Modified Capabilities

- Ninguna.

## Impact

- API: `GET /api/tasks`, `POST /api/tasks`, `GET /api/summary`, `POST /api/requirements` y `GET /api/backend-health`, que comparten la autenticación de identidad.
- Contrato de autenticación emitido por auth y encabezado Bearer de web: protegidos, sin cambios.
- Pruebas y configuración de la API: deberán demostrar los criterios de aceptación usando una clave ficticia, sin incorporar secretos al repositorio.
- `docs/ENDPOINTS.md` documenta el contrato de login, pero no documenta `/api/tasks`; para el éxito de las rutas de API, el Issue exige preservar el comportamiento actual observado. La aceptación del JWT por API es el comportamiento nuevo comprometido por el Issue; no modifica el contrato documentado de login.
