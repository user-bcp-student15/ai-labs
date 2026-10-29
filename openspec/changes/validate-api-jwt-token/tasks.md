# Tasks

Alcance: componente `api/` del Issue #25 (HU-01). Comandos desde la raíz de ai-labs; pruebas con `python tools/lab.py test api`. Sin tocar `auth/`, `web/` ni `docs/ENDPOINTS.md`. Las tareas no se marcan como hechas hasta que su verificación pase.

## 1. Preparación y línea base

- [x] 1.1 Confirmar en [ENDPOINTS.md](../../../docs/ENDPOINTS.md) §4 y §6 si `AUTH_TOKEN_SECRET` tiene valor por defecto fuera de `prod`, y registrar el resultado en la nota de contexto de [design.md](./design.md). Si no está documentado, detenerse y preguntar al usuario antes de implementar. Verificación: nota registrada en `design.md` o consulta respondida.
- [x] 1.2 Ejecutar `python tools/lab.py test api` sobre el código actual y registrar la línea base. Verificación: suite en verde antes de cualquier cambio.

## 2. Caracterización antes del cambio funcional

- [ ] 2.1 Parametrizar en `api/tests/test_api.py` las cinco rutas protegidas (`GET/POST /api/tasks`, `GET /api/summary`, `POST /api/requirements`, `GET /api/backend-health`) con el token legado vigente, afirmando status y claves de la respuesta. Verificación: las pruebas pasan sobre el código sin modificar.
- [ ] 2.2 Caracterizar los 401 de encabezado ausente, encabezado sin prefijo `Bearer` y Base64 inválido: status 401 y `detail` que empieza por `Invalid token: `. Verificación: las pruebas pasan sobre el código sin modificar.
- [x] 2.3 Caracterizar `GET /api/backend-health` con la llamada a `AUTH_HEALTH_URL` simulada, para éxito y fallo (`status: 0`). Verificación: las pruebas pasan sobre el código sin modificar. Evidencia: pruebas en copia temporal de `9838e3d`, exit 0; no están en `api/tests/test_api.py`.
- [x] 2.4 Caracterizar la creación de tarea (`POST /api/tasks`, 201) y el archivo guardado en `POST /api/requirements` (201). Verificación: las pruebas pasan sobre el código sin modificar.

## 3. Pruebas nuevas que deben fallar (rojo)

- [x] 3.1 Agregar `PyJWT` a `api/requirements.txt` con versión fijada y verificar que `pip install -r api/requirements-dev.txt` termina sin errores. Verificación: instalación exitosa.
- [x] 3.2 Añadir fixture con clave ficticia de 32 bytes y un generador de tokens HS256 con `sub`, `role`, `iat` y `exp = iat + 3600`. Verificación: el generador produce un token decodificable con la clave ficticia.
- [x] 3.3 Añadir pruebas de verificación: token válido aceptado con identidad de `sub` y `role`; firma con otra clave, token alterado, token expirado, `alg` distinto de HS256 (incluido `none`), `sub` ausente y formato legado Base64 rechazados con 401 y prefijo `Invalid token: `. Verificación: las pruebas nuevas fallan con el código actual por la razón esperada.
- [x] 3.4 Añadir pruebas de configuración: `create_app` falla si `AUTH_TOKEN_SECRET` falta o tiene menos de 32 bytes. Verificación: fallan con el código actual.

## 4. Implementación incremental

- [x] 4.1 Implementar en `api/app/main.py` el verificador JWT con algoritmo fijo `HS256`, `exp`, `sub` e `iat` obligatorios, y constantes con nombre para algoritmo, bytes mínimos de clave y prefijo `Bearer `. Verificación: pruebas 3.3 pasan.
- [x] 4.2 Leer `AUTH_TOKEN_SECRET` en `create_app` y fallar cerrado si falta o es corta. Verificación: pruebas 3.4 pasan.
- [x] 4.3 Sustituir `legacy_identity` por el verificador en todas las rutas protegidas, mapeando `username` desde `sub` y `role` desde `role`, sin cambiar la forma de la dependencia. Verificación: pruebas 2.1 a 2.4 pasan con el token JWT del helper.
- [x] 4.4 Eliminar `LEGACY_SECRET` y el helper de token Base64 de `api/app/main.py` y `api/tests/test_api.py`. Verificación: `grep` de `LEGACY_SECRET` y `WORKSHOP_SECRET_2026` en `api/` sin resultados, y suite en verde.
- [x] 4.5 Confirmar que el formato legado produce 401 en las cinco rutas protegidas. Verificación: pruebas de 3.3 pasan en todas las rutas.

## 5. Documentación y configuración del componente

- [x] 5.1 Documentar `AUTH_TOKEN_SECRET` en el README de `api/` (nombre, requisito de 32 bytes, debe coincidir con auth, sin valor real). Verificación: `grep AUTH_TOKEN_SECRET api/README.md` encuentra la entrada.
- [x] 5.2 Si `api/Dockerfile` o un compose del componente `api` define variables de entorno, añadir `AUTH_TOKEN_SECRET` con marcador ficticio; si no las define, no modificarlo. Verificación: `grep` en esos archivos coincide con lo decidido.

## 6. Verificación de integración

- [x] 6.1 Ejecutar `python tools/lab.py test api` con cobertura y confirmar 85% o más en las líneas modificadas de `api/app/main.py`. Verificación: suite en verde y reporte de cobertura registrado.
- [x] 6.2 Añadir una prueba de interoperabilidad que genere un token con el mismo formato que emite auth (HS256, `sub`, `role`, `iat`, `exp = iat + 3600`) y clave ficticia compartida, y compruebe que la API lo acepta. Verificación: prueba en verde.
- [x] 6.3 Confirmar que el cambio no toca `auth/`, `web/` ni `docs/ENDPOINTS.md`, revisando `git status` desde la raíz. Verificación: solo aparecen `api/` y `openspec/changes/validate-api-jwt-token/`, además de los cambios previos ya existentes.
- [x] 6.4 Ejecutar `openspec validate validate-api-jwt-token --strict` desde la raíz. Verificación: el cambio es válido.

## Workflow follow-up

- Revisión humana y aprobación del cambio antes de integrarlo, según las reglas del Día 1 (sin push ni PR sin aprobación).
- Archivar el cambio con `openspec-archive-change` solo después de la aprobación y de que todas las tareas estén marcadas.
