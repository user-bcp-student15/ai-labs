# Plan de corrección de ReqFlow

Plan por componente. Cada apartado corresponde a un hallazgo de `HALLAZGOS.md`; el estado de seguimiento se lleva solo allí.

## api

### Premisas

- Fase: planificación. No se modifica código en este paso. No existe `docs/ENDPOINTS.md`, así que el contrato a preservar es el **comportamiento observado** descrito en `HALLAZGOS.md` (sección api). Todo cambio que altere ese comportamiento se marca como **cambio de contrato**; su aprobación está cubierta por la declaración del usuario descrita en "Estado de la revisión humana".
- Convenciones usadas: solo las de `docs/GOOD_PRACTICES.md` (sección api) y las reglas Clean Code de `AGENTS.md` (una responsabilidad por función, sin duplicación, sin anidamiento profundo, sin valores mágicos: constantes con nombre).
- Se conservan sin cambios: rutas y métodos, `create_app(db_path, upload_dir)`, la variable `app` en `api/app/main.py` (la usan `api/Dockerfile` con `app.main:app` y las pruebas), `WORKSHOP_DB_PATH`, `WORKSHOP_UPLOAD_DIR`, `AUTH_HEALTH_URL`, y los nombres JSON de respuesta (`createdAt`, `byStatus`, `highPriorityOpen`, `fileName`, `storedAt`, `requestedBy`).
- Pruebas desde `api/` (`python tools/lab.py test api` desde la raíz). Meta: 85% del código modificado; el gate de 85% de toda la app se mantiene sin cambios.

### Estructura objetivo (H-API-08)

```
api/app/
  main.py            # create_app + wiring, expone `app`
  config.py          # Settings: env vars y constantes con nombre
  security.py        # verificación del token, dependencia de identidad
  schemas.py         # modelos Pydantic de request/response
  database.py        # conexión, esquema y semillas
  repositories/tasks.py   # SQL parametrizado
  services/tasks.py       # reglas: autorización por identidad, resumen
  services/uploads.py     # validación y guardado de archivos
  services/backend_health.py
  routes/{tasks,requirements,health}.py
```

Se migra en pasos pequeños y revisables (uno por hallazgo), con pruebas verdes entre pasos. Cada función hace una sola cosa: la ruta solo traduce HTTP, el servicio aplica reglas, el repositorio ejecuta SQL.

### Trazabilidad con HALLAZGOS.md

Los 14 hallazgos tienen estado `Aprobado` en `HALLAZGOS.md` (declaración del usuario; ver arriba) y un apartado propio más abajo, con problema, cambio propuesto, archivos y prueba de caracterización previa. Ningún cambio se ha implementado.

| ID | Apartado | Dependencias del orden | Bloqueo |
|---|---|---|---|
| H-API-14 | Pruebas de caracterización | ninguna (va primero) | — |
| H-API-06, H-API-07 | Dependencias | H-API-14 | `pip-audit` sin ejecutar |
| H-API-08 | Capas | H-API-14 | — |
| H-API-03, H-API-04 | SQL parametrizado | H-API-14, H-API-08 | — |
| H-API-11 | Pydantic y calidad | H-API-08 | — |
| H-API-02 | Autorización | H-API-11 | — |
| H-API-01 | Token | H-API-02 | coordinación con auth |
| H-API-05 | Archivos | H-API-11, H-API-06 | — |
| H-API-09, H-API-10, H-API-12, H-API-13 | Errores, CORS, SQLite, lifespan | H-API-08 | CORS: consumo desde web sin verificar |

### Orden de ejecución propuesto

1. H-API-14 (caracterización) → 2. H-API-06/07 (dependencias) → 3. H-API-08 (capas sin cambiar comportamiento) → 4. H-API-03/04 (SQL) → 5. H-API-11 (Pydantic y calidad) → 6. H-API-02 (autorización) → 7. H-API-01 (token) → 8. H-API-05 (archivos) → 9. H-API-09, H-API-10, H-API-12, H-API-13.

### Estado de la revisión humana

- El usuario indicó en la sesión (2026-11-02 16:34) que se tome la revisión humana de este plan como aprobada. Queda registrado como declaración del usuario en la conversación; no hay otra evidencia (PR, revisor o acta) y no se agrega.
- Alcance de esa aprobación: el plan y las propuestas por defecto D1–D7 se consideran aceptados tal como están escritos. Cualquier cambio de contrato respecto del comportamiento observado queda cubierto solo por estas propuestas.
- Sigue pendiente aunque el plan esté aprobado: activar H-API-01 depende de que auth emita el mismo formato de token (componente fuera de alcance); mientras no se confirme, ese hallazgo queda bloqueado por coordinación. Tampoco hay resultados de pruebas ni de `pip-audit`.

### Decisiones (propuestas por defecto, aceptadas con la aprobación anterior)

| # | Decisión | Propuesta por defecto | Hallazgo | Estado |
|---|---|---|---|---|
| D1 | Formato del token y quién lo emite (componente auth, no leído) | JWT HS256 con `iss`, `aud`, `exp`, `sub`, `role`; secreto/iss/aud por env | H-API-01 | Aprobada por el usuario; implementación bloqueada hasta coordinar con auth |
| D2 | `owner` ajeno en consulta/creación | 403 si difiere del usuario del token; el campo `owner` del body se ignora | H-API-02 | Aprobada por el usuario |
| D3 | Rol con acceso a tareas de otros (p. ej. `trainer`) | Ninguno en esta fase | H-API-02 | Aprobada por el usuario |
| D4 | Campos obligatorios, longitudes y valores válidos de tarea | `title` 1–120, `description` 0–2000, `status` y `priority` con enums observados; 422 si no cumplen | H-API-11 | Aprobada por el usuario |
| D5 | Extensiones y tamaño máximo de carga | `.txt`, `.md`, `.pdf`, `.docx`; 5 MiB | H-API-05 | Aprobada por el usuario |
| D6 | Política de colisión de nombres al subir | Mantener nombre normalizado (la prueba actual espera `requirements.txt`); colisión sobrescribe | H-API-05 | Aprobada por el usuario; riesgo residual de sobrescritura |
| D7 | Orígenes CORS y credenciales | `http://localhost:4200` por env; sin credenciales (el token va en header) | H-API-10 | Aprobada por el usuario; pendiente verificar consumo desde web |

---

### H-API-14 — Pruebas de caracterización (primero)

- **Hallazgo:** H-API-14 (Sugerencia, baja), `api/tests/test_api.py:19-58`.
- **Problema:** solo hay 4 pruebas felices; ninguna fija el comportamiento antes de refactorizar ni cubre los riesgos.
- **Cambio propuesto:**
  - Fixtures compartidas en `api/tests/conftest.py`: app con `tmp_path`, `TestClient` con `with` y generador de token de prueba. El secreto de prueba vive en una constante de pruebas aislada, no en la app; mientras exista el token legado el helper lo construye igual que hoy.
  - Pruebas en `api/tests/test_characterization_*.py` que fijan lo observado y que **deben pasar contra el código actual**: 401 sin header, con Base64 inválido y con token vencido; filtro por `owner` por defecto; forma exacta de las respuestas de cada endpoint; 201 de creación; summary (total, `byStatus`, `highPriorityOpen` ignorando `DONE` y `ARCHIVED`); upload devuelve `owner,fileName,storedAt,size`; `backend-health` con `AUTH_HEALTH_URL` inválida devuelve 200 con `status` 0; 405 en métodos no permitidos; 422 en multipart sin `file`.
  - Para cada riesgo, una prueba del comportamiento **objetivo** marcada `@pytest.mark.xfail(strict=True, reason="H-API-NN")`; al implementar el hallazgo se quita el `xfail`. No se marca como logrado nada que no pase.
- **Archivos a tocar:** `api/tests/conftest.py` (nuevo), `api/tests/test_characterization_*.py` (nuevos), `api/tests/test_api.py` (reutilizar helpers, sin quitar pruebas).
- **Prueba previa:** esta es la prueba previa de todos los demás hallazgos; se ejecuta en verde sobre el código sin modificar y se registra en `docs/TESTING.md` (componente api, IDs H-API-NN).
- **Clean Code:** helpers sin duplicación (token/headers una sola vez), nombres de propósito, sin números mágicos (TTL del token como constante de pruebas).

### H-API-06 — `python-multipart 0.0.21`

- **Hallazgo:** H-API-06 (Vulnerabilidad, alta), `api/requirements.txt:5`.
- **Problema:** versión con advisories en el parseo multipart usado por `/api/requirements`; CVE y versión corregida sin confirmar.
- **Cambio propuesto:** confirmar con `pip-audit` (o GitHub Advisory) la versión corregida (se espera `>=0.0.22`) y fijar la menor versión sin advisories compatible con `fastapi==0.128.2`. No se agregan dependencias nuevas. Sin cambio de contrato.
- **Archivos a tocar:** `api/requirements.txt`.
- **Prueba de caracterización previa:** `test_uploads_requirement` existente más 422 sin `file` y subida de varias extensiones, en verde antes y después del cambio; añadir `pip-audit` al registro de evidencia (no ejecutado todavía).

### H-API-07 — `urllib3 2.5.0`

- **Hallazgo:** H-API-07 (Vulnerabilidad, media), `api/requirements.txt:4`, `api/app/main.py:118`.
- **Problema:** advisories de descompresión (CVE-2025-66418, CVE-2025-66471 corregidos en 2.6.0; CVE-2026-21441 en 2.6.3 según fuentes públicas, por confirmar).
- **Cambio propuesto:** subir a la versión corregida más baja que cierre todos los advisories (se espera `2.6.3`, a validar con `pip-audit`). Opcional y a justificar: acotar el tamaño de respuesta leída en `backend_health`. No se agregan dependencias.
- **Archivos a tocar:** `api/requirements.txt`.
- **Prueba de caracterización previa:** `backend-health` con `urllib3` simulado (monkeypatch de `PoolManager.request`) para respuesta correcta (`status`, `body`) y para fallo (`status` 0); mismas pruebas después.

### H-API-08 — Separación en capas

- **Hallazgo:** H-API-08 (Refactor, media), `api/app/main.py:29-125`.
- **Problema:** `create_app` mezcla configuración, esquema, semillas, SQL, reglas y serialización.
- **Cambio propuesto:** mover a la estructura objetivo sin cambiar comportamiento, en commits separados (API/servicio/repositorio/seguridad):
  1. `config.py` con `Settings` (rutas, `AUTH_HEALTH_URL`, constantes).
  2. `database.py` (esquema y semillas) y `repositories/tasks.py`.
  3. `services/` con reglas y `routes/` delgadas con `APIRouter`.
  4. `main.py` solo ensambla y expone `app` y `create_app` con la misma firma.
  Inyección por `Depends` para repositorio y servicios; funciones pequeñas, sin duplicación (una sola función `row → TaskResponse`), constantes con nombre para tablas, estados y prioridades.
- **Archivos a tocar:** `api/app/main.py`, `api/app/config.py`, `api/app/database.py`, `api/app/security.py`, `api/app/schemas.py`, `api/app/repositories/*`, `api/app/services/*`, `api/app/routes/*` (nuevos). `api/Dockerfile` no cambia (`COPY app ./app` ya los incluye).
- **Prueba de caracterización previa:** toda la suite de H-API-14 en verde antes y después de cada paso; sin modificar aserciones.

### H-API-03 — SQL de filtros concatenado (listado y resumen)

- **Hallazgo:** H-API-03 (Vulnerabilidad, alta), `api/app/main.py:70`, `api/app/main.py:93`.
- **Problema:** `owner` concatenado en el `WHERE`; inyección SQL.
- **Cambio propuesto:** en `repositories/tasks.py`, `list_by_owner(owner)` y `status_and_priority_by_owner(owner)` con consultas parametrizadas (`WHERE owner = ?`, tupla de parámetros). Sin cambio de contrato.
- **Archivos a tocar:** `api/app/repositories/tasks.py` (o `api/app/main.py` si se hace antes de H-API-08).
- **Prueba de caracterización previa:** `owner` con comilla simple (`o'brien`) devuelve lista vacía sin 500; `owner` con sintaxis SQL (valor ficticio como `x' OR '1'='1`, solo local) debe devolver lista vacía, no todas las tareas (`xfail` hasta el cambio).

### H-API-04 — SQL de creación concatenado

- **Hallazgo:** H-API-04 (Vulnerabilidad, alta), `api/app/main.py:84`, `api/app/main.py:87`.
- **Problema:** INSERT y SELECT con strings concatenados; inyección y 500 con comillas legítimas.
- **Cambio propuesto:** `create(task) -> id` con `INSERT ... VALUES (?,?,?,?,?,datetime('now'))` y `get_by_id(id)` con `WHERE id = ?`; commit en el repositorio. Mantiene 201 y el cuerpo de respuesta.
- **Archivos a tocar:** `api/app/repositories/tasks.py`.
- **Prueba de caracterización previa:** crear tarea con título `Fix "login" & o'brien` y comprobar que se guarda literal y vuelve en la respuesta (hoy falla: `xfail`); crear tarea y verificar que listar la devuelve.

### H-API-11 — Pydantic, tipos y calidad

- **Hallazgo:** H-API-11 (Refactor, media), `api/app/main.py:25`, `:68`, `:72-74`, `:78-83`, `:101-104`, `:120`.
- **Problema:** `dict[str, Any]`, `except Exception`, `if` anidados, bucles/contadores manuales, strings y números mágicos.
- **Cambio propuesto:**
  - `schemas.py`: `TaskCreate` (`title`, `description`, `status`, `priority` con defaults observados `""`/`TODO`/`MEDIUM`; ver D4), `TaskResponse` con alias `createdAt` (`populate_by_name`/`serialization_alias`), `TaskSummary`, `UploadResponse`, `BackendHealthResponse`. Todas las rutas con `response_model`.
  - `StrEnum` `TaskStatus` (`TODO`, `IN_PROGRESS`, `DONE`, `ARCHIVED`) y `TaskPriority` (`HIGH`, `MEDIUM`, `LOW`); `CLOSED_STATUSES` como constante.
  - `summary` sin anidamiento: `collections.Counter` para `byStatus` y una condición combinada `priority is HIGH and status not in CLOSED_STATUSES`.
  - Excepciones concretas (`sqlite3.Error`, `urllib3.exceptions.HTTPError`) en lugar de `except Exception`.
  - Constante con nombre para el timeout de health y el valor por defecto de `AUTH_HEALTH_URL`.
  - Cambio de contrato (D4): valores fuera de los enums o `title` vacío pasan de aceptarse a 422. Sin aprobación se deja la validación laxa (solo `str` con `Field` de longitud máxima) y se documenta como riesgo.
- **Archivos a tocar:** `api/app/schemas.py`, `api/app/services/tasks.py`, `api/app/routes/tasks.py`, `api/app/services/backend_health.py`, `api/app/config.py`.
- **Prueba de caracterización previa:** `summary` con tareas `HIGH` en `TODO`, `IN_PROGRESS`, `DONE`, `ARCHIVED` y verificar `highPriorityOpen`/`byStatus`/`total`; esquema OpenAPI contiene `TaskResponse` con `createdAt`; creación con campos ausentes usa defaults observados; creación con `status` inválido → 422 (solo tras D4).

### H-API-02 — Autorización ligada a la identidad

- **Hallazgo:** H-API-02 (Vulnerabilidad, alta), `api/app/main.py:69`, `:83`, `:92`.
- **Problema:** `owner` del cliente prevalece sobre la identidad; lectura y escritura cruzadas; `role` sin uso.
- **Cambio propuesto:** `services/tasks.py` resuelve `resolve_owner(identity, requested_owner)`: sin `owner` usa `identity.username`; con `owner` distinto lanza `HTTPException(403, "Forbidden")` (D2/D3). En creación se ignora `owner` del body y se usa `identity.username`. La respuesta mantiene el campo `owner`. Una sola función reutilizada por listado, resumen y creación (sin duplicación) y retorno anticipado.
- **Archivos a tocar:** `api/app/services/tasks.py`, `api/app/routes/tasks.py`, `api/app/schemas.py`.
- **Prueba de caracterización previa:** hoy `student` con `?owner=trainer` obtiene las tareas de `trainer` y puede crear con `owner` ajeno (fijar con `xfail` del comportamiento objetivo: 403 y owner forzado al del token); sin `owner` y con `owner` igual al propio siguen devolviendo 200 igual que hoy.

### H-API-01 — Token sin firma (verificación real)

- **Hallazgo:** H-API-01 (Vulnerabilidad, alta), `api/app/main.py:14`, `:19-24`, `api/tests/test_api.py:11`.
- **Problema:** Base64 con secreto embebido; sin firma, emisor ni audiencia; comparación no constante.
- **Cambio propuesto:** `security.py` con `decode_token(token) -> Identity` que verifica **firma, emisor, audiencia y expiración** (GOOD_PRACTICES) y exige claims `sub`, `role`, `exp`. Secreto, `iss`, `aud` y algoritmo desde variables de entorno (`config.py`), sin valores por defecto reales; arranque falla o rechaza tokens si no hay secreto. Todo fallo → `HTTPException(401, "Invalid token")` genérico (se une a H-API-09). Cabecera `WWW-Authenticate: Bearer`.
  - Dependencia nueva a justificar (D1): `PyJWT` (verificación estándar con `iss`/`aud`/`exp`), para no implementar criptografía a mano. Alternativa sin dependencia: HMAC-SHA256 con `hmac.compare_digest` y claims propios, con más código a mantener. Se decide con el equipo.
  - **Coordinación:** el emisor es auth (fuera de alcance, no leído). El cambio solo se activa cuando auth emita el mismo formato; hasta entonces se registra como bloqueado, sin inventar la aprobación. No se agrega aceptación del formato Base64 antiguo.
- **Archivos a tocar:** `api/app/security.py`, `api/app/config.py`, `api/requirements.txt` (si se aprueba PyJWT), `api/tests/conftest.py`.
- **Prueba de caracterización previa:** sin header, token mal formado y vencido → 401 (en verde hoy). Objetivo con `xfail`: token Base64 legado → 401; firma alterada, `iss`/`aud` incorrectos y `exp` pasado → 401; token válido → 200. Secreto de prueba generado/inyectado por variable de entorno en `conftest.py`, nunca el secreto del código.
- **Clean Code:** guard clauses, una función para extraer el token, otra para decodificar, otra para construir la identidad.

### H-API-05 — Carga segura de archivos

- **Hallazgo:** H-API-05 (Vulnerabilidad, alta), `api/app/main.py:109-112`.
- **Problema:** nombre del cliente sin normalizar (path traversal), sin límite de extensión ni tamaño, lectura completa en memoria, ruta absoluta en la respuesta.
- **Cambio propuesto:** `services/uploads.py`:
  - `sanitize_filename(raw)`: `Path(raw).name`, rechaza vacío, `.`/`..`, separadores y caracteres de control; conserva el nombre válido (la prueba actual espera `requirements.txt`).
  - Extensión permitida en `ALLOWED_EXTENSIONS` (constante, D5) → 415 si no; tamaño máximo `MAX_UPLOAD_BYTES` (D5) leyendo por bloques con constante `READ_CHUNK_BYTES` → 413 si excede, sin escribir el archivo parcial.
  - Comprobar que `target.resolve()` queda dentro de `upload_dir.resolve()`.
  - Respuesta `UploadResponse(owner, fileName, storedAt, size)` con `fileName` normalizado y `storedAt` sin exponer la ruta absoluta del servidor (cambio de contrato menor, requiere aprobación; sin ella se mantiene la ruta y queda como riesgo).
  - Errores 4xx genéricos. D6: colisión sobrescribe como hoy.
- **Archivos a tocar:** `api/app/services/uploads.py`, `api/app/routes/requirements.py`, `api/app/config.py`, `api/app/schemas.py`.
- **Prueba de caracterización previa:** archivo válido se guarda con su nombre y devuelve 201 y `size` (en verde hoy). Objetivo con `xfail`: nombre `../fuera.txt` no escribe fuera de `upload_dir`; extensión `.exe` → 415; archivo mayor al máximo → 413 sin archivo creado; respuesta sin ruta absoluta.

### H-API-09 — Errores con detalles internos

- **Hallazgo:** H-API-09 (Vulnerabilidad, media), `api/app/main.py:26`, `api/app/main.py:119-121`.
- **Problema:** `str(error)` devuelto al cliente (token, URL/red del backend).
- **Cambio propuesto:** 401 con `detail="Invalid token"`; `backend_health` en fallo devuelve `status` 0 y `body` genérico (`"Backend unavailable"`) y registra el detalle con `logging` (sin datos sensibles). Mantiene el 200 y la forma de la respuesta observada.
- **Archivos a tocar:** `api/app/security.py`, `api/app/services/backend_health.py`.
- **Prueba de caracterización previa:** `backend-health` hacia puerto cerrado devuelve 200 con `status` 0 (verde hoy); objetivo `xfail`: `body` no contiene la URL ni el texto de la excepción, y el 401 no contiene `str(error)`; `caplog` verifica que el detalle va al log.

### H-API-10 — CORS abierto con credenciales

- **Hallazgo:** H-API-10 (Vulnerabilidad, media), `api/app/main.py:48-54`.
- **Problema:** `*` con credenciales y métodos/headers sin límite.
- **Cambio propuesto:** `Settings.cors_allowed_origins` desde env `CORS_ALLOWED_ORIGINS` (lista separada por comas, default `http://localhost:4200`, D7); `allow_credentials=False`; métodos `GET, POST, OPTIONS`; headers `Authorization, Content-Type`. Sin comodines. Falta verificar cómo consume el frontend (web no leído): coordinación pendiente, sin ampliar AMBITO.
- **Archivos a tocar:** `api/app/config.py`, `api/app/main.py`.
- **Prueba de caracterización previa:** preflight `OPTIONS` con `Origin: http://localhost:4200` devuelve `access-control-allow-origin` (en verde hoy); objetivo `xfail`: origen no permitido no recibe el header y no se devuelve `*`.

### H-API-12 — Conexión SQLite compartida entre hilos

- **Hallazgo:** H-API-12 (Bug, baja, hipótesis), `api/app/main.py:35`, `:71`, `:85`.
- **Problema:** una conexión con `check_same_thread=False` usada desde el pool de hilos; posible concurrencia insegura.
- **Cambio propuesto:** conexión por solicitud (`Depends` que abre y cierra en `finally`) en `database.py`, sin `check_same_thread=False`; esquema y semillas se ejecutan una vez al iniciar. Contrato sin cambios.
- **Archivos a tocar:** `api/app/database.py`, `api/app/routes/*` (dependencia).
- **Prueba de caracterización previa:** prueba de creación concurrente (varios hilos con `TestClient`/`ThreadPoolExecutor`) comprobando que todos los inserts quedan y que no hay errores; se registra el resultado real, la hipótesis se confirma o descarta con esa evidencia.

### H-API-13 — `on_event` y creación de `app` al importar

- **Hallazgo:** H-API-13 (Refactor, baja), `api/app/main.py:123-125`, `api/app/main.py:130`.
- **Problema:** `on_event("shutdown")` en desuso; importar `app.main` crea carpetas y DB como efecto secundario.
- **Cambio propuesto:** `lifespan` en `create_app` para inicialización (carpetas, esquema, semillas) y cierre; se mantiene `app = create_app()` en `main.py` porque `api/Dockerfile` usa `app.main:app`. Las pruebas usan `with TestClient(app)` (ya es así), que ejecuta el `lifespan`.
- **Archivos a tocar:** `api/app/main.py`, `api/app/database.py`.
- **Prueba de caracterización previa:** tras `with TestClient(app)` existen DB y carpeta de cargas y se listan las 2 tareas semilla del usuario `student` (verde hoy); al salir del contexto la conexión queda cerrada; importar el módulo no debe fallar con rutas de entorno de prueba (`monkeypatch` de `WORKSHOP_DB_PATH`).

---

### Registro de ejecuciones (implementación, 2026-11-02)

Rama local `day1/prompting` (creada desde `main`). Pruebas con cwd `api/`; comando de componente: `python tools/lab.py test api` desde la raíz. Sin commits ni push.

| Ejecución | Componente | IDs | Resultado real |
|---|---|---|---|
| Línea base `python tools/lab.py test api` (código original) | api | H-API-14 | 4 pasaron; cobertura 91.07% de `app` |
| `pip-audit -r api/requirements.txt` (antes) | api | H-API-06, H-API-07 | 22 vulnerabilidades en `urllib3 2.5.0` (corrección hasta 2.8.0) y `python-multipart 0.0.21` (hasta 0.0.31) |
| `pytest tests/test_characterization.py tests/test_api.py` (código original) | api | H-API-14 | 19 pasaron; la prueba concurrente falló y pasó a `test_findings.py` |
| `pytest tests/test_findings.py` (código original) | api | H-API-02 a H-API-13 | 22 fallaron y 1 pasó (`own_owner_query`, caracterización); confirma los hallazgos, incluida la hipótesis de H-API-12 |
| Tras H-API-06/07: `pip-audit`, `pytest -k advisories`, caracterización | api | H-API-06, H-API-07 | sin vulnerabilidades conocidas; 2 y 19 pasaron |
| Tras H-API-08: caracterización | api | H-API-08 | 19 pasaron |
| Tras H-API-03/04: `pytest -k "parameterized or quotes or injected_sql"` y caracterización | api | H-API-03, H-API-04 | 4 y 19 pasaron |
| Tras H-API-11, 02, 05, 09: pruebas por hallazgo y caracterización | api | H-API-11, H-API-02, H-API-05, H-API-09 | todas pasaron |
| Tras H-API-10, 12, 13: `pytest tests` | api | H-API-10, H-API-12, H-API-13 | 42 pasaron |
| Concurrencia repetida 8 veces | api | H-API-12 | 8 de 8 pasaron |
| `python tools/lab.py test api` (final) | api | H-API-02 a H-API-14 | 48 pasaron; cobertura 100% de `app` (275 sentencias, 16 ramas, 0 sin cubrir; gate de 85% cumplido); `pip check` sin conflictos |
| `python tools/lab.py test api` (paso de pruebas por endpoint, 2026-11-02) | api | H-API-14, H-API-16 | 137 pasaron y 1 xfail esperado (H-API-16); cobertura 100%; detalle en `docs/TESTING.md` |
| `pip-audit --path api/.venv/Lib/site-packages` (revisión, entorno completo) | api | H-API-06, H-API-07, H-API-15 | `urllib3` y `python-multipart` sin hallazgos; `starlette 0.50.0` y `pytest 9.0.2` con advisories (H-API-15, Pendiente). Corrige la afirmación anterior de "sin vulnerabilidades", que venía de `--no-deps` |
| Verificación manual con `TestClient` (revisión, solo lectura) | api | H-API-05, H-API-12, H-API-14 | `trainer` sobrescribe el `a.txt` de `student` (201); `nul.txt` aceptado en Windows; POST sin token devuelve 401; sin `check_same_thread=False` 30 de 30 POST dieron 201 en `TestClient` (no prueba el caso con `uvicorn`) |

La cobertura del diff no se midió por separado: como cubre el 100% de `app` (todo el código modificado o nuevo), se cumple la meta de 85%. Método: `pytest-cov` con ramas; no demuestra por sí solo la calidad de las aserciones.

### Cambios de contrato aplicados (aprobados con D2, D4, D5, D7)

- `?owner=<otro>` en `/api/tasks` y `/api/summary` devuelve 403; el `owner` del body se ignora (D2/D3).
- `POST /api/tasks` devuelve 422 con `title` vacío o ausente, `status`/`priority` fuera de los enums o textos demasiado largos (D4).
- `POST /api/requirements` devuelve 400/415/413 por nombre inválido, extensión no permitida o tamaño mayor a 5 MiB; `storedAt` ahora es el nombre del archivo, no la ruta absoluta (D5).
- 401 con `Invalid token` y `/api/backend-health` con `Backend unavailable` en fallo (H-API-09).
- CORS limitado a `CORS_ALLOWED_ORIGINS` (default `http://localhost:4200`), sin credenciales (D7).

### Desviaciones respecto del plan

- H-API-01 no se implementó (bloqueado por auth, como se acordó); el token legado y su secreto siguen en `api/app/security.py`.
- Las pruebas de corrección no llevan `xfail(strict)`: se ejecutaron sobre el código original para registrar el fallo previo y se dejaron como pruebas normales en verde.
- H-API-12: la conexión por solicitud mantiene `check_same_thread=False`. Hipótesis no comprobada: FastAPI puede ejecutar la dependencia y la ruta en hilos distintos del pool; en `TestClient` el parámetro no hizo falta (revisión). Cada conexión la usa una sola solicitud.
- H-API-12: la hipótesis se confirmó (error `cannot commit - no transaction is active` bajo escritura concurrente).
- H-API-13: la inicialización pasa al `lifespan`; hay que usar `with TestClient(app)` para que se ejecute (las pruebas existentes ya lo hacían).
- `AUTH_HEALTH_URL` y `CORS_ALLOWED_ORIGINS` se leen al crear la app, no en cada solicitud.
- `python-multipart` 0.0.31 y `urllib3` 2.8.0 salen de `pip-audit`; el plan estimaba 0.0.22 y 2.6.3.
- Se mantuvo `except ValueError` en el token y `except (HTTPError, UnicodeDecodeError)` en health, en lugar de `sqlite3.Error` previsto en el plan (no hay captura de errores SQL en las rutas).
- Se agregó la prueba `test_restarting_on_an_existing_database_does_not_reseed` y casos de nombres inseguros para cubrir las ramas nuevas.
- No se agregaron dependencias nuevas.

### Registro de riesgos residuales

- `docs/TESTING.md` y `docs/ENDPOINTS.md` no se crean todavía (su paso de documentación).
- Riesgos a revisar antes de cerrar: sobrescritura de archivos (D6), rol sin política (D3), compatibilidad del token con auth (D1, H-API-01 abierto), consumo de CORS por web.
- Sin revisión humana del diff ni PR: la aprobación registrada es la del plan.
