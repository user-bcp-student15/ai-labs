# Design

## Context

Ver [proposal.md](./proposal.md) para la motivación y [specs/api-token-authentication/spec.md](./specs/api-token-authentication/spec.md) para los requisitos y escenarios.

Estado actual de `api/` (componente afectado):

- `legacy_identity` en [main.py](C:/Users/Usuario/Documents/t09872-pedro-ramirez-guzman/ai-labs/api/app/main.py) decodifica la credencial como Base64 `usuario|rol|exp|secreto`, compara el cuarto campo con `LEGACY_SECRET` (constante en código) y no verifica firma. Ante cualquier fallo lanza `HTTPException(401, detail="Invalid token: " + error)`.
- Todas las rutas protegidas usan `Depends(legacy_identity)`: `GET/POST /api/tasks`, `GET /api/summary`, `POST /api/requirements` y `GET /api/backend-health`. Cambiar esa dependencia cubre el alcance del proposal.
- `api/requirements.txt` no contiene ninguna librería JWT.
- `create_app()` se invoca al importar el módulo (`app = create_app()`), por lo que cualquier configuración obligatoria se evalúa en el arranque.
- auth emite HS256 con los claims `sub`, `role`, `iat` y `exp` (`exp = iat + 3600`) y toma la clave de `AUTH_TOKEN_SECRET`; en `prod` exige al menos 32 bytes. Ver [ENDPOINTS.md](C:/Users/Usuario/Documents/t09872-pedro-ramirez-guzman/ai-labs/docs/ENDPOINTS.md) §4 y §6. (Confirmar en auth si existe un valor por defecto fuera de `prod` antes de implementar.)
- las pruebas actuales en [test_api.py](C:/Users/Usuario/Documents/t09872-pedro-ramirez-guzman/ai-labs/api/tests/test_api.py) generan tokens legados y la prueba `test_rejects_invalid_token` solo cubre la ausencia de un token Base64 válido.

## Goals / Non-Goals

**Goals:**

- Verificar firma HS256, expiración y claims requeridos de la credencial antes de usar cualquier identidad.
- Derivar `username` desde `sub` y `role` desde `role` del token verificado, sin cambiar la forma de las respuestas de las rutas.
- Mantener el status y el cuerpo 401 (`{"detail": "Invalid token: ..."}`) para credenciales rechazadas.
- Obtener la clave desde configuración externa, con fallo cerrado si falta.
- Cubrir con pruebas la regresión de las cinco rutas antes y después del cambio.

**Non-Goals:**

- No modificar `auth/`, `web/`, `docs/ENDPOINTS.md` ni el contrato de `POST /auth/login`.
- No cambiar la autorización por propietario (`owner` como parámetro de consulta), SQL concatenado, carga de archivos ni CORS: son hallazgos distintos.
- No introducir refresh tokens, revocación, listas de bloqueo ni un endpoint de validación en auth.
- No mantener aceptación del formato legado ni un modo dual controlado por bandera (decisión del proposal).

## Contratos protegidos

- `POST /auth/login`: sin cambios en código ni en pruebas de contrato de auth.
- Formato del token emitido: HS256, claims `sub`, `role`, `iat`, `exp`, vigencia de 3600 s.
- Encabezado `Authorization: Bearer <token>` que envía web.
- Respuestas exitosas de `GET/POST /api/tasks`, `GET /api/summary`, `POST /api/requirements` y `GET /api/backend-health` (status y forma).
- Cuerpo 401 `{"detail": "Invalid token: <motivo>"}`; el texto del motivo puede variar, la forma y el prefijo no.

## Componentes afectados

| Ruta | Cambio |
|---|---|
| `api/app/main.py` | Reemplazar `legacy_identity` por un verificador JWT; retirar `LEGACY_SECRET`; leer la clave de configuración en `create_app`. |
| `api/requirements.txt` | Agregar la librería de verificación JWT con versión fijada. |
| `api/tests/test_api.py` | Añadir pruebas de caracterización, de verificación JWT y de configuración; reemplazar el helper de token legado. |
| `api/README.md` y `api/Dockerfile` (si documentan variables) | Documentar `AUTH_TOKEN_SECRET`. |

No cambian `auth/`, `web/` ni los documentos generales del repositorio.

## Decisions

### D1. Librería JWT frente a verificación manual con `hmac`

- **Decisión:** usar una librería JWT madura (PyJWT) con la versión fijada en `requirements.txt`, invocada con `algorithms=["HS256"]`, `options={"require": ["exp", "sub", "iat"]}` y verificación de firma y expiración.
- **Razón:** evita implementar a mano el análisis de JWT y la comparación de firmas; la librería ya cubre `alg=none`, confusión de algoritmos y validación de `exp`.
- **Alternativa considerada:** implementar HS256 con `hmac` y `hashlib` de la biblioteca estándar, sin dependencia nueva. Se descarta por el riesgo de errores criptográficos y de parsing en código propio. Queda como plan B si la política del equipo prohíbe nuevas dependencias.

### D2. Algoritmo fijo y claims obligatorios

- **Decisión:** aceptar únicamente `HS256`; rechazar cualquier otro `alg`, incluido `none`.
- **Razón:** el contrato de auth fija HS256; aceptar una lista abierta de algoritmos amplía la superficie de ataque sin beneficio.

### D3. Origen de la clave: `AUTH_TOKEN_SECRET` compartida

- **Decisión:** la API lee `AUTH_TOKEN_SECRET`, el mismo nombre que usa auth, y debe recibir el mismo valor en el mismo entorno.
- **Razón:** evita un nuevo nombre de variable y deja explícito que ambos servicios comparten el secreto de firma.
- **Trade-off:** si auth usa un valor por defecto fuera de `prod`, la API no lo conoce; en desarrollo ambos servicios deben configurar la variable explícitamente. Esto se documenta en el README de `api/`.

### D4. Fallo cerrado si falta la clave

- **Decisión:** `create_app` lanza error si `AUTH_TOKEN_SECRET` está vacía o tiene menos de 32 bytes, de forma análoga al arranque de auth en `prod`.
- **Alternativa considerada:** arrancar y responder siempre 401 en rutas protegidas. Se descarta porque ocultaría una mala configuración y dejaría una API inutilizable sin señal clara.
- **Consecuencia:** el `app = create_app()` a nivel de módulo fallará sin la variable; las pruebas pasan una clave ficticia de 32 bytes explícitamente.

### D5. Identidad desde el token verificado

- **Decisión:** `identity["username"]` se obtiene de `sub` y `identity["role"]` de `role`, tras la verificación; el mismo diccionario conserva la firma actual de la dependencia para que las rutas no cambien.
- **Razón:** minimiza el cambio en las rutas; el único cambio observable es el origen de la identidad.

### D6. Extracción de la credencial sin cambios de tolerancia

- **Decisión:** conservar la extracción actual: se elimina el prefijo `Bearer ` si existe y se usa el resto como token.
- **Razón:** la tolerancia actual no es parte del contrato del Issue; cambiarla sin necesidad aumentaría el riesgo de regresión. Se valida mediante la prueba de caracterización de encabezado sin prefijo.

### D7. Mensaje del 401

- **Decisión:** mantener `HTTPException(status_code=401, detail="Invalid token: " + motivo)`, donde `motivo` es un texto corto y fijo por categoría (ausente, malformado, firma inválida, expirado), sin volcar excepciones internas.
- **Razón:** conserva la forma del cuerpo y evita filtrar detalles de la librería. Esto reduce la exposición que el hallazgo original también señalaba.

## Estrategia incremental

1. **Caracterización antes de cambiar (sin modificar `main.py`):** en `test_api.py`, parametrizar las cinco rutas con el token legado actual y registrar status, claves y tipos de la respuesta, y el 401 para credencial ausente y para Base64 inválido. Estas pruebas deben pasar en el estado actual.
2. **Pruebas nuevas en rojo:** agregar casos JWT (válido, firma con otra clave, alterado, expirado, `alg` distinto de HS256, claim `sub` ausente, formato legado). Deben fallar con el código actual.
3. **Implementación:** añadir el verificador y la lectura de `AUTH_TOKEN_SECRET`; sustituir `legacy_identity`. Las pruebas de caracterización de la paso 1 deben seguir pasando, cambiando solo el helper de token a JWT.
4. **Retirar legado:** eliminar `LEGACY_SECRET` y el helper Base64; comprobar que el formato legado produce 401 en las cinco rutas.
5. **Documentar y configurar:** README y Dockerfile con `AUTH_TOKEN_SECRET`, sin valor real.
6. **Verificación de interoperabilidad:** generar un token con el mismo formato que auth (HS256, `sub`, `role`, `iat`, `exp = iat + 3600`) usando una clave ficticia y comprobar que la API lo acepta. Una verificación manual contra el auth en ejecución queda como opcional, con clave ficticia y fuera de CI.

Cobertura objetivo: 85% o más del código modificado (`api/app/main.py`), según las instrucciones del componente `api`.

## Pruebas de caracterización necesarias

Antes de modificar el comportamiento crítico, deben existir pruebas que fijen:

- Para cada una de las cinco rutas protegidas: status exitoso y forma de la respuesta con credencial válida (usando el token legado vigente).
- Para `POST /api/tasks`: la creación y el `201`; para `POST /api/requirements`: el archivo almacenado y el `201`.
- Para `GET /api/backend-health`: la forma de la respuesta con `AUTH_HEALTH_URL` simulada, tanto para éxito como para fallo (`status: 0`).
- 401 para encabezado ausente, para encabezado sin prefijo `Bearer` y para Base64 inválido: status 401 y clave `detail` con prefijo `Invalid token: `.

Estas pruebas son el criterio de no regresión de los escenarios de "rutas protegidas conservan sus respuestas exitosas".

## Riesgos / Trade-offs

- **[Dependencia nueva]** → versión fijada y revisión de la librería en la PR; alternativa documentada en D1.
- **[Clave ausente o distinta entre servicios]** → fallo al arrancar la API (D4) y pruebas de integración con clave ficticia compartida; documentación explícita en README.
- **[Clave por defecto de auth fuera de `prod`]** → la API no puede inferirla; el equipo debe definir `AUTH_TOKEN_SECRET` en desarrollo. Riesgo de fricción, no de seguridad.
- **[Consumidores legados fuera de web]** → el proposal rechaza explícitamente el formato legado; si aparece un consumidor, debe migrar a JWT antes de desplegar.
- **[Tokens ya emitidos con secreto anterior]** → no aplica: los tokens legados nunca fueron válidos fuera de la API; los JWT de auth siguen siendo válidos mientras la clave no cambie.
- **[Mayor superficie de errores 401]** → la forma del cuerpo se conserva (D7) y las pruebas cubren cada categoría.
- **[Vigencia de 3600 s sin revocación]** → fuera de alcance; un token robado sigue válido hasta expirar.

## Migration Plan y rollback

- **Despliegue:** antes de desplegar la API, definir `AUTH_TOKEN_SECRET` en su entorno con el mismo valor que auth. Si falta, la API no arranca (D4).
- **Orden:** desplegar auth sin cambios; luego la API; la web no requiere cambios.
- **Rollback:** revertir el commit o PR de la API. Esto restaura el verificador anterior y **reabre H-API-01**, por lo que el rollback debe ser excepcional y registrarse en `HALLAZGOS.md`. No se implementa una bandera de compatibilidad, porque el proposal descarta aceptar el formato legado.
- **Datos:** no hay migración de datos; la tabla `tasks` no cambia.

## Open Questions

Ninguna que afecte specs, enfoque o desglose de tareas.

## Decisiones de implementación

- Tarea 1.1: auth conserva su valor por defecto de `%dev`; la API exige `AUTH_TOKEN_SECRET` explícita en todos los entornos.
- Tolerancia a `Bearer` (D6) se mantiene: la tarea 2.2 se caracteriza como aceptación de un token válido sin prefijo, y 401 para token inválido sin prefijo.
- `role` es claim obligatorio junto con `sub`, `iat` y `exp`.
- Las pruebas fijan `AUTH_TOKEN_SECRET` en `tests/conftest.py` antes de importar `app.main`.
