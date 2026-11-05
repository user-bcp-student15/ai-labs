## Why

Issue [#23](https://github.com/user-bcp-student15/ai-labs/issues/23) (hallazgo H-AUTH-01, vulnerabilidad de severidad alta, componente `auth/`): la búsqueda de credenciales del login se arma concatenando `username` y `password` en el SQL (`auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java:32`). Un valor como `' OR '1'='1` altera la consulta y permite iniciar sesión sin conocer la contraseña y obtener un token válido. Como `auth` emite los tokens que consume `api`, esta omisión de autenticación compromete a todo el sistema.

## What Changes

- La verificación de credenciales del login trata `username` y `password` siempre como datos, nunca como parte de la sentencia SQL.
- Un intento de inyección en `username` o `password` se rechaza con 401 y sin `token`.
- Se agrega cobertura de prueba del intento de inyección en `AuthResourceTest`.
- Sin cambios en el contrato de `POST /auth/login` (no es un **BREAKING** change).

## Alcance

- Componente `auth/` únicamente: comportamiento de autenticación de `POST /auth/login` frente a entradas con sintaxis SQL.
- Pruebas de `auth/` (`AuthResourceTest`, `mvn test` desde `auth/`), con cobertura del código modificado de 85% o más.

## Fuera de alcance

- Componentes `api/` y `web/`, y sus secciones en los documentos generales.
- Almacenamiento de contraseñas (hoy en texto plano), formato/firma del token, expiración, campo `debug` y mensaje de error que refleja el usuario enviado: son hallazgos distintos.
- Refactor en capas de `AuthResource`, nuevos endpoints, dependencias o cambios de esquema de base de datos.
- Diseño técnico de la solución (se define en el paso de diseño).

## Comportamiento que debe preservarse

Baseline: [docs/ENDPOINTS.md](../../../docs/ENDPOINTS.md) documenta solo `api/` y no describe `POST /auth/login`; por tanto el baseline de este endpoint es el Issue #23 y el comportamiento actual verificado en `AuthResource`/`AuthResourceTest`. El Issue no cambia ese contrato; solo corrige el rechazo de entradas maliciosas.

- Credenciales válidas (`student` / `Workshop123!`): 200 con `token`, `expiresIn` y `user` (`username`, `displayName`, `role`).
- Cuerpo ausente, `username` o `password` vacíos o en blanco: 400 con `message`.
- Credenciales inexistentes o incorrectas: 401 con `message`.
- Ruta, método, tipo de contenido JSON y formato del token emitido sin cambios.

## Capabilities

### New Capabilities

- `auth-login`: autenticación por credenciales en `POST /auth/login`, incluida su resistencia a inyección SQL.

### Modified Capabilities

(ninguna; `openspec/specs/` no tiene specs previas)

## Impact

- Código afectado (solo `auth/`): acceso a datos de credenciales y `AuthResourceTest`.
- Consumidores (`api/`, `web/`) no requieren cambios: el contrato se mantiene.
- Riesgo: regresión en el login válido; se mitiga con las pruebas de preservación.
