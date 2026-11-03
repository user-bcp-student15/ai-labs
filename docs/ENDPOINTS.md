# Endpoints de ReqFlow

Contratos de los servicios. Cada componente mantiene su propia sección; no se mezclan.

## api

API FastAPI de tareas y requerimientos (`api/`). Este documento describe el **contrato observado en el código actual** de la rama `day1/prompting`, verificado contra `api/app/` y con respuestas reales obtenidas ejecutando la aplicación con `TestClient` sobre una base de datos temporal. No hay un contrato acordado distinto de este: los cambios aprobados respecto del comportamiento original están en [Estado del contrato](#estado-del-contrato).

### Datos generales

| Dato | Valor | Origen |
|---|---|---|
| URL base local | `http://localhost:8000` (puerto de `uvicorn` y de Compose) | `README.md`, `api/Dockerfile` |
| Prefijo de rutas | `/api` | `api/app/routes/tasks.py:8` |
| Formato | JSON (`application/json`), salvo la carga de archivos (`multipart/form-data`) | rutas |
| Documentación interactiva | `/docs`, `/redoc` y `/openapi.json` responden 200 | comprobado |
| Nombres JSON | camelCase en respuestas (`createdAt`, `byStatus`, `highPriorityOpen`, `fileName`, `storedAt`, `requestedBy`) | `api/app/schemas.py:26-27` |
| Fechas | `createdAt` tiene formato `AAAA-MM-DD HH:MM:SS`, sin zona; es la hora UTC del servidor (`datetime('now')` de SQLite) | `api/app/repositories/tasks.py:19`, comprobado |

#### Autenticación (aplica a los 5 endpoints)

- Header exacto: `Authorization: Bearer <token>` (`api/app/security.py:17-19`). Observado: el token también se acepta sin el prefijo `Bearer ` (comprobado con 200); se recomienda enviar siempre el prefijo.
- Formato del token (legado, sigue vigente): texto en Base64 (UTF-8) de cuatro campos separados por `|`: `usuario|rol|expiración|secreto`. La expiración es un entero en segundos Unix; el secreto es compartido con el emisor y no se documenta aquí. La API rechaza usuario vacío o compuesto solo por espacios, roles distintos de `TRAINER`, tokens vencidos y expiraciones a más de 5 segundos en el futuro (`api/app/security.py`). La API no firma ni verifica emisor ni audiencia: ver riesgos pendientes (H-API-01).
- Quién emite el token es el componente auth; no se verificó desde `api/` que el formato coincida (pregunta abierta 1).
- La identidad es el campo `usuario` del token. Se acepta solo el rol `TRAINER`; el rol no concede permisos adicionales ni se usa para autorizar recursos.
- En los ejemplos, `<token>` es un token válido del usuario indicado (`student` o `trainer`).

#### Formatos de error

| Forma | Cuándo | Ejemplo |
|---|---|---|
| `{"detail": "<mensaje>"}` | Errores de la aplicación (401, 403, 400, 413, 415) y 404/405 | `{"detail": "Forbidden"}` |
| `{"detail": [ {...} ]}` | Validación de la solicitud (422), formato estándar de FastAPI/Pydantic con `type`, `loc`, `msg`, `input` y, a veces, `ctx` | ver cada endpoint |

Los mensajes de error de la aplicación son genéricos. El detalle técnico se registra en el log del servidor, no en la respuesta. La respuesta 422 sí incluye el valor enviado en `input`.

#### Error común a los 5 endpoints: token ausente o inválido

- **401** cuando falta `Authorization`, el token no es Base64/UTF-8 válido, no tiene 4 campos, el secreto no coincide, usuario o rol no cumplen las reglas anteriores, la expiración no es un entero, ya venció o está a más de 5 segundos en el futuro (`api/app/security.py`).

```json
{"detail": "Invalid token"}
```

En todos los endpoints la autenticación se evalúa antes que la validación del contenido: sin token válido se recibe 401 aunque falten campos o el archivo tenga una extensión no permitida (comprobado en `POST /api/tasks` y `POST /api/requirements`). Excepción observada: un cuerpo JSON mal formado en `POST /api/tasks` devuelve 422 aunque no haya token.

---

### GET /api/tasks

**1. Qué hace.** Lista las tareas del usuario autenticado, ordenadas por `id` ascendente (`api/app/routes/tasks.py:11-16`, `api/app/repositories/tasks.py:10-12`).

**2. Autenticación.** Obligatoria: `Authorization: Bearer <token>`.

**3. Request.**

| Parámetro | Ubicación | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `Authorization` | header | string | Sí | `Bearer <token>` |
| `owner` | query | string | No | Dueño de las tareas. Vacío u omitido: se usa el usuario del token. Si se envía, debe ser igual al usuario del token; si es distinto, 403 (`api/app/dependencies.py:25-28`) |

Ejemplo completo:

```http
GET /api/tasks HTTP/1.1
Host: localhost:8000
Authorization: Bearer <token>
```

**4. Respuesta exitosa: 200.** Cuerpo: arreglo de tareas (vacío si el usuario no tiene tareas).

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | integer | Identificador autogenerado |
| `title` | string | Título |
| `description` | string | Descripción (puede ser `""`) |
| `status` | string | Estado de la tarea; valores creados por la API: `TODO`, `IN_PROGRESS`, `DONE`, `ARCHIVED` |
| `owner` | string | Usuario dueño de la tarea |
| `priority` | string | Prioridad; valores creados por la API: `HIGH`, `MEDIUM`, `LOW` |
| `createdAt` | string | Fecha de creación en UTC, `AAAA-MM-DD HH:MM:SS` |

Respuesta real (base de datos nueva, usuario `student`; los datos iniciales son 2 tareas de `student` y 1 de `trainer`, `api/app/database.py:11-15`):

```json
[
  {"id": 1, "title": "Refactor login", "description": "Separar responsabilidades en frontend", "status": "TODO", "owner": "student", "priority": "HIGH", "createdAt": "2026-11-02 22:12:37"},
  {"id": 2, "title": "Review API", "description": "Revisar seguridad de endpoints", "status": "IN_PROGRESS", "owner": "student", "priority": "MEDIUM", "createdAt": "2026-11-02 22:12:37"}
]
```

**5. Errores.**

| Código | Cuándo | Cuerpo de ejemplo |
|---|---|---|
| 401 | Token ausente, mal formado, con otro secreto o vencido | `{"detail": "Invalid token"}` |
| 403 | `owner` distinto del usuario del token, p. ej. `GET /api/tasks?owner=trainer` con el token de `student` | `{"detail": "Forbidden"}` |

Otros códigos observados para la ruta: 405 si se usa un método no permitido (`DELETE`): `{"detail": "Method Not Allowed"}`.

**6. Notas de seguridad.**
- La autorización depende de la identidad del token, no de `owner`: `owner` solo puede repetir la identidad (H-API-02).
- La consulta usa parámetros (`WHERE owner = ?`), sin concatenar datos del cliente (H-API-03).
- Mientras el token siga siendo falsificable (H-API-01), un tercero que conozca el formato y el secreto puede hacerse pasar por cualquier usuario.

---

### POST /api/tasks

**1. Qué hace.** Crea una tarea a nombre del usuario autenticado y devuelve la tarea creada (`api/app/routes/tasks.py:19-25`).

**2. Autenticación.** Obligatoria: `Authorization: Bearer <token>`.

**3. Request.** Cuerpo JSON (`Content-Type: application/json`).

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `title` | string | Sí | De 1 a 120 caracteres (un texto de solo espacios se acepta) |
| `description` | string | No | Hasta 2000 caracteres. Por defecto `""` |
| `status` | string | No | Uno de `TODO`, `IN_PROGRESS`, `DONE`, `ARCHIVED`. Por defecto `TODO` |
| `priority` | string | No | Uno de `HIGH`, `MEDIUM`, `LOW`. Por defecto `MEDIUM` |

Cualquier otro campo se ignora, incluido `owner`: el dueño siempre es el usuario del token (`api/app/schemas.py:37-41`).

Ejemplo completo:

```http
POST /api/tasks HTTP/1.1
Host: localhost:8000
Authorization: Bearer <token>
Content-Type: application/json

{"title": "Add tests", "description": "Improve coverage", "status": "IN_PROGRESS", "priority": "HIGH"}
```

**4. Respuesta exitosa: 201.** Cuerpo: la tarea creada, con los mismos campos que en `GET /api/tasks`.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | integer | Identificador asignado |
| `title` | string | Título recibido |
| `description` | string | Descripción recibida o `""` |
| `status` | string | Estado recibido o `TODO` |
| `owner` | string | Usuario del token |
| `priority` | string | Prioridad recibida o `MEDIUM` |
| `createdAt` | string | Fecha de creación UTC, `AAAA-MM-DD HH:MM:SS` |

Respuesta real (base de datos nueva, usuario `student`):

```json
{"id": 4, "title": "Add tests", "description": "Improve coverage", "status": "IN_PROGRESS", "owner": "student", "priority": "HIGH", "createdAt": "2026-11-02 22:12:37"}
```

Con solo `{"title": "Only title"}` la respuesta real es `{"id": 5, "title": "Only title", "description": "", "status": "TODO", "owner": "student", "priority": "MEDIUM", "createdAt": "2026-11-02 22:12:37"}` (el `id` depende de las tareas ya creadas).

**5. Errores.**

| Código | Cuándo | Cuerpo de ejemplo |
|---|---|---|
| 401 | Token ausente, mal formado, con otro secreto o vencido | `{"detail": "Invalid token"}` |
| 422 | `title` ausente (`{}`) | `{"detail": [{"type": "missing", "loc": ["body", "title"], "msg": "Field required", "input": {}}]}` |
| 422 | `title` vacío | `{"detail": [{"type": "string_too_short", "loc": ["body", "title"], "msg": "String should have at least 1 character", "input": "", "ctx": {"min_length": 1}}]}` |
| 422 | `title` de más de 120 o `description` de más de 2000 caracteres | `{"detail": [{"type": "string_too_long", "loc": ["body", "title"], "msg": "String should have at most 120 characters", "input": "<texto enviado>", "ctx": {"max_length": 120}}]}` |
| 422 | `status` fuera de los valores permitidos | `{"detail": [{"type": "enum", "loc": ["body", "status"], "msg": "Input should be 'TODO', 'IN_PROGRESS', 'DONE' or 'ARCHIVED'", "input": "WHATEVER", "ctx": {"expected": "'TODO', 'IN_PROGRESS', 'DONE' or 'ARCHIVED'"}}]}` |
| 422 | `priority` fuera de los valores permitidos | `{"detail": [{"type": "enum", "loc": ["body", "priority"], "msg": "Input should be 'HIGH', 'MEDIUM' or 'LOW'", "input": "URGENT", "ctx": {"expected": "'HIGH', 'MEDIUM' or 'LOW'"}}]}` |
| 422 | Campo con tipo incorrecto, p. ej. `{"title": 5}` | `{"detail": [{"type": "string_type", "loc": ["body", "title"], "msg": "Input should be a valid string", "input": 5}]}` |
| 422 | Cuerpo ausente | `{"detail": [{"type": "missing", "loc": ["body"], "msg": "Field required", "input": null}]}` |
| 422 | JSON mal formado | `{"detail": [{"type": "json_invalid", "loc": ["body", 1], "msg": "JSON decode error", "input": {}, "ctx": {"error": "Expecting property name enclosed in double quotes"}}]}` |

**6. Notas de seguridad.**
- El dueño de la tarea sale del token; enviar `owner` en el cuerpo no tiene efecto (comprobado: `{"title": "x", "owner": "trainer"}` crea la tarea con `owner` igual a `student`) (H-API-02).
- La inserción usa parámetros; las comillas y el SQL enviados en `title` o `description` se guardan como texto (H-API-04).
- Los valores de `status` y `priority` se validan contra listas cerradas.

---

### GET /api/summary

**1. Qué hace.** Devuelve el resumen de las tareas del usuario autenticado: cuántas tiene, cuántas por estado y cuántas de prioridad alta siguen abiertas (`api/app/routes/tasks.py:28-33`, `api/app/services/tasks.py:27-33`).

**2. Autenticación.** Obligatoria: `Authorization: Bearer <token>`.

**3. Request.**

| Parámetro | Ubicación | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `Authorization` | header | string | Sí | `Bearer <token>` |
| `owner` | query | string | No | Igual que en `GET /api/tasks`: vacío u omitido usa el usuario del token; si es distinto, 403 |

Ejemplo completo:

```http
GET /api/summary HTTP/1.1
Host: localhost:8000
Authorization: Bearer <token>
```

**4. Respuesta exitosa: 200.**

| Campo | Tipo | Descripción |
|---|---|---|
| `owner` | string | Usuario al que corresponde el resumen |
| `total` | integer | Cantidad de tareas del usuario |
| `byStatus` | objeto (string → integer) | Cantidad de tareas por estado; solo aparecen los estados con al menos una tarea |
| `highPriorityOpen` | integer | Tareas con prioridad `HIGH` cuyo estado no es `DONE` ni `ARCHIVED` |

Respuesta real (base de datos nueva, usuario `student`):

```json
{"owner": "student", "total": 2, "byStatus": {"TODO": 1, "IN_PROGRESS": 1}, "highPriorityOpen": 1}
```

Un usuario sin tareas recibe `{"owner": "nobody", "total": 0, "byStatus": {}, "highPriorityOpen": 0}` (comprobado).

**5. Errores.**

| Código | Cuándo | Cuerpo de ejemplo |
|---|---|---|
| 401 | Token ausente, mal formado, con otro secreto o vencido | `{"detail": "Invalid token"}` |
| 403 | `owner` distinto del usuario del token | `{"detail": "Forbidden"}` |

**6. Notas de seguridad.** Igual que `GET /api/tasks`: el resumen depende de la identidad del token y no de un `owner` enviado por el cliente (H-API-02); la consulta está parametrizada (H-API-03).

---

### POST /api/requirements

**1. Qué hace.** Sube un archivo de requerimientos del usuario autenticado y lo guarda en el servidor (`api/app/routes/requirements.py:10-20`).

**2. Autenticación.** Obligatoria: `Authorization: Bearer <token>`.

**3. Request.** Cuerpo `multipart/form-data`.

| Campo | Ubicación | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `Authorization` | header | string | Sí | `Bearer <token>` |
| `file` | parte del formulario | archivo | Sí | Archivo a subir. Hasta 5 MiB (5 242 880 bytes); se acepta uno de exactamente ese tamaño y también uno vacío |

Reglas del nombre del archivo (`api/app/services/uploads.py:8-36`):
- Se descartan las rutas: solo cuenta el último segmento (`../a.txt` y `..\a.txt` pasan a `a.txt`).
- Debe empezar con letra, dígito o `_` y contener solo letras, dígitos, `_`, espacio, `.` y `-`.
- Extensión permitida, sin distinguir mayúsculas: `.txt`, `.md`, `.pdf`, `.docx`.

Ejemplo completo:

```http
POST /api/requirements HTTP/1.1
Host: localhost:8000
Authorization: Bearer <token>
Content-Type: multipart/form-data; boundary=----boundary

------boundary
Content-Disposition: form-data; name="file"; filename="requirements.txt"
Content-Type: text/plain

Login must be accessible
------boundary--
```

Equivalente con curl: `curl -X POST http://localhost:8000/api/requirements -H "Authorization: Bearer <token>" -F "file=@requirements.txt"`.

**4. Respuesta exitosa: 201.**

| Campo | Tipo | Descripción |
|---|---|---|
| `owner` | string | Usuario del token |
| `fileName` | string | Nombre con el que se guardó, ya normalizado |
| `storedAt` | string | Ubicación dentro de la carpeta de cargas del servidor; hoy es igual a `fileName` (no se expone la ruta absoluta) |
| `size` | integer | Tamaño en bytes |

Respuesta real:

```json
{"owner": "student", "fileName": "requirements.txt", "storedAt": "requirements.txt", "size": 24}
```

Con el nombre `../outside.txt` la respuesta real es `{"owner": "student", "fileName": "outside.txt", "storedAt": "outside.txt", "size": 24}`. La API no ofrece un endpoint para descargar los archivos.

**5. Errores.**

| Código | Cuándo | Cuerpo de ejemplo |
|---|---|---|
| 401 | Token ausente, mal formado, con otro secreto o vencido | `{"detail": "Invalid token"}` |
| 400 | Nombre inválido, p. ej. `bad*name.txt` o `..` | `{"detail": "Invalid file name"}` |
| 415 | Extensión no permitida, p. ej. `payload.exe` | `{"detail": "File type not allowed"}` |
| 413 | Archivo de más de 5 MiB (5 242 881 bytes o más) | `{"detail": "File too large"}` |
| 422 | Falta la parte `file` | `{"detail": [{"type": "missing", "loc": ["body", "file"], "msg": "Field required", "input": null}]}` |

**6. Notas de seguridad.**
- El nombre del cliente se normaliza y se restringe la extensión y el tamaño antes de guardar (H-API-05); el nombre ya no puede sacar el archivo de la carpeta de cargas.
- **Riesgo pendiente (H-API-05, `Pendiente`):** un archivo con el mismo nombre sobrescribe al anterior, incluso si lo subió otro usuario (comprobado: `trainer` sustituyó el `a.txt` de `student`). Además el límite de 5 MiB se aplica cuando el servidor ya recibió todo el cuerpo.
- Los archivos no se separan por usuario; `owner` en la respuesta solo informa quién subió el último.

---

### GET /api/backend-health

**1. Qué hace.** Consulta el estado del servicio de autenticación (backend de auth) y lo devuelve junto con quién lo pidió (`api/app/routes/health.py:10-13`, `api/app/services/backend_health.py:20-26`).

**2. Autenticación.** Obligatoria: `Authorization: Bearer <token>`.

**3. Request.**

| Parámetro | Ubicación | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `Authorization` | header | string | Sí | `Bearer <token>` |

No recibe parámetros ni cuerpo. La URL consultada sale de la variable de entorno `AUTH_HEALTH_URL` del servidor (por defecto `http://localhost:8080/q/health`) y el tiempo máximo de espera es de 3 segundos (`api/app/config.py:6,8`).

Ejemplo completo:

```http
GET /api/backend-health HTTP/1.1
Host: localhost:8000
Authorization: Bearer <token>
```

**4. Respuesta exitosa: 200.** Se devuelve 200 siempre que el token sea válido, aunque el backend no responda.

| Campo | Tipo | Descripción |
|---|---|---|
| `requestedBy` | string | Usuario del token |
| `status` | integer | Código HTTP devuelto por el backend de auth, o `0` si no se pudo consultar |
| `body` | string | Texto devuelto por el backend, o `Backend unavailable` si no se pudo consultar |

Backend que responde (respuesta real con una respuesta simulada del backend):

```json
{"requestedBy": "student", "status": 200, "body": "{\"status\":\"UP\",\"checks\":[]}"}
```

Backend caído, error de red, tiempo agotado o respuesta que no es UTF-8 (respuesta real con el backend inaccesible):

```json
{"requestedBy": "student", "status": 0, "body": "Backend unavailable"}
```

Si el backend responde con un código de error, también es 200 con ese código en `status` (comprobado con 503: `{"requestedBy": "student", "status": 503, "body": "{\"status\":\"DOWN\"}"}`).

**5. Errores.**

| Código | Cuándo | Cuerpo de ejemplo |
|---|---|---|
| 401 | Token ausente, mal formado, con otro secreto o vencido | `{"detail": "Invalid token"}` |

Un fallo del backend de auth **no** es un error de este endpoint: se informa con `status` `0`.

**6. Notas de seguridad.**
- El detalle del fallo (URL interna, texto de la excepción) se registra solo en el log del servidor; el cliente recibe el mensaje genérico `Backend unavailable` (H-API-09).
- El cliente no controla la URL consultada, solo el servidor.
- Cuando el backend responde, `body` reenvía su texto completo sin límite de tamaño (pregunta abierta 3).

---

### CORS

Aplica a todos los endpoints (`api/app/main.py:35-41`, `api/app/config.py:7,9-10`).

- Orígenes permitidos: los de la variable `CORS_ALLOWED_ORIGINS` (lista separada por comas); por defecto `http://localhost:4200`.
- Métodos: `GET`, `POST`, `OPTIONS`. Headers: `Authorization`, `Content-Type`. Sin credenciales (no se permiten cookies).
- Comprobado: un preflight desde `http://localhost:4200` responde 200 con `access-control-allow-origin: http://localhost:4200`; desde `http://evil.example` responde 400 con el texto `Disallowed CORS origin`.

### Estado del contrato

**Contrato observado.** Todo lo anterior, verificado en el código y con ejecuciones reales. No se verificó contra el consumidor (web), que no se leyó por el alcance.

**Cambios respecto del comportamiento original (aprobados en `PLAN.md`: D2, D4, D5, D7 y H-API-09).** Un cliente escrito contra la versión anterior debe revisar:

| Antes | Ahora |
|---|---|
| `owner` en la query leía tareas o resumen de cualquier usuario | 403 si es distinto del usuario del token |
| `owner` en el cuerpo de `POST /api/tasks` fijaba el dueño | Se ignora; el dueño es el usuario del token |
| `POST /api/tasks` aceptaba título vacío y estados o prioridades cualesquiera | 422 por título vacío o ausente, valores fuera de las listas y textos demasiado largos |
| `POST /api/requirements` aceptaba cualquier nombre, extensión y tamaño | 400, 415 o 413; el nombre se normaliza |
| `storedAt` devolvía la ruta absoluta del servidor | Devuelve solo el nombre del archivo |
| 401 con `Invalid token: <detalle>`; `body` de health con el texto de la excepción | `Invalid token` y `Backend unavailable` |
| CORS abierto a cualquier origen con credenciales | Solo los orígenes configurados, sin credenciales |

**Riesgos pendientes** (seguimiento en `HALLAZGOS.md`):

| ID | Riesgo |
|---|---|
| H-API-01 | El token no está firmado, no verifica emisor ni audiencia y su secreto está en el código. Bloqueado hasta coordinar con auth el formato. |
| H-API-05 | Sobrescritura de archivos entre usuarios y límite de tamaño aplicado tras recibir el cuerpo. |
| H-API-15 | Dependencias transitivas con advisories (`starlette 0.50.0`, `pytest 9.0.2` de desarrollo). |
| H-API-16 | Un nombre de archivo con `:` (p. ej. `a:b.txt`) se acepta en Windows (201 con `fileName` `b.txt`); en Linux el código debería responder 400 (no ejecutado); la regla de nombres del contrato debería ser igual en ambos sistemas. |

### Preguntas abiertas

La API aplica un máximo de 5 segundos al tiempo restante hasta `exp`, y acepta solo el rol `TRAINER`; queda pendiente confirmar con auth que sus tokens cumplen estas reglas. El formato legado no incluye `issued-at`.

1. ¿El componente auth emite exactamente el formato de token descrito (`usuario|rol|expiración|secreto` en Base64)? No se pudo verificar desde `api/`.
2. ¿Debe rechazarse un `title` formado solo por espacios? Hoy se acepta (comprobado con `{"title": " "}`, 201).
3. ¿Debe limitarse el tamaño de `body` en `GET /api/backend-health`? Hoy se reenvía completo.
4. ¿Qué devuelve la API ante un error interno inesperado (p. ej. base de datos bloqueada)? No se probó; sería la respuesta 500 por defecto de FastAPI, sin verificar.
5. ¿Qué rol, si lo hay, puede ver tareas de otros usuarios (p. ej. `trainer`)? Hoy ninguno (decisión D3 de `PLAN.md`).
6. ¿Debe aceptarse el token sin el prefijo `Bearer `? Hoy se acepta por cómo se procesa el header (`api/app/security.py:19`).
