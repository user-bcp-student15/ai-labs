# Hallazgos de ReqFlow

Seguimiento general. Cada componente mantiene sus propias filas; este archivo se actualiza hallazgo por hallazgo durante el refactor.

## api

### Alcance y método

- Fase: Discovery (solo lectura, sin cambios de código). Código leído: `api/app/main.py`, `api/tests/test_api.py`, `api/requirements.txt`, `api/Dockerfile`, `api/pyproject.toml`.
- No existe `docs/ENDPOINTS.md`: el contrato de la sección siguiente es **observado** a partir del código, no acordado. Debe confirmarse con el equipo antes de refactorizar.
- No se ejecutó ninguna prueba, escaneo ni la API en este paso. Todo lo indicado es lectura de código; los CVE de dependencias se contrastaron con advisories públicos y quedan por confirmar con `pip-audit` (pendiente).
- Referencias `archivo:línea` desde la raíz del repositorio.

### Contrato observado (no acordado)

Punto de entrada: `api/app/main.py:130` (`app = create_app()`), fábrica en `api/app/main.py:29`. Todas las rutas dependen de `legacy_identity` (`api/app/main.py:17`).

| Método y ruta | Entrada | Salida | Línea |
|---|---|---|---|
| GET `/api/tasks` | query `owner` opcional | lista de tareas (`id,title,description,status,owner,priority,createdAt`), 200 | `api/app/main.py:67` |
| POST `/api/tasks` | JSON libre (`title,description,status,priority,owner`) | tarea creada, 201 | `api/app/main.py:77` |
| GET `/api/summary` | query `owner` opcional | `owner,total,byStatus,highPriorityOpen`, 200 | `api/app/main.py:90` |
| POST `/api/requirements` | multipart `file` | `owner,fileName,storedAt,size`, 201 | `api/app/main.py:107` |
| GET `/api/backend-health` | ninguna | `requestedBy,status,body` (200 incluso si el backend falla, `status` 0) | `api/app/main.py:114` |

- Flujo del token: header `Authorization` → quita `Bearer ` → Base64 → `usuario|rol|exp|secreto` → compara el secreto embebido y `exp` → `{username, role}`; cualquier fallo devuelve 401 con `str(error)` (`api/app/main.py:17-26`). El rol nunca se usa para autorizar.
- Acceso a SQLite: conexión única compartida, creada en `create_app` (`api/app/main.py:35`); esquema y semillas en línea (`api/app/main.py:37-43`); todo el SQL se arma concatenando strings dentro de las rutas (`api/app/main.py:70, 84, 87, 93`).
- Carga de archivos: se guarda en `WORKSHOP_UPLOAD_DIR` con `file.filename` sin tratar y el contenido completo en memoria (`api/app/main.py:109-111`).
- Contrato con auth: el formato del token debe coincidir con el que emite el componente auth (no leído por alcance). Cambiar la validación exige coordinar con auth (pendiente).

### Matriz de seguimiento

Ordenada de mayor a menor severidad. Los 7 casos de `RETO.md` existen en el código (ninguno "No encontrado"); los marcados "adicional" no están en `RETO.md` y se observaron durante la lectura.

| id | componente | hallazgo | tipo | explicacion | evidencia (archivo:linea) | severidad | estado |
|---|---|---|---|---|---|---|---|
| H-API-01 | api | Token Base64 con secreto embebido (RETO: Auth) | Vulnerabilidad | El token no está firmado: quien conozca el formato y el secreto (publicado en el código y en las pruebas) puede fabricar cualquier usuario y rol. No se verifica emisor ni audiencia; el secreto está hardcodeado y se compara sin tiempo constante. | `api/app/main.py:14`, `api/app/main.py:19-24`, `api/tests/test_api.py:11` | alta | Aprobado: pendiente, bloqueado hasta coordinar con auth el formato del token |
| H-API-02 | api | El cliente puede consultar o crear tareas de otro `owner` (RETO: Autorización) | Vulnerabilidad | `owner` llega del cliente y prevalece sobre la identidad del token: cualquier usuario autenticado lee tareas y resumen de otros, y crea tareas a nombre de otros. No hay control por rol (`role` no se usa). | `api/app/main.py:69`, `api/app/main.py:83`, `api/app/main.py:92` | alta | Resuelto: `resolve_owner` (`api/app/dependencies.py`) usa la identidad del token; `owner` ajeno devuelve 403 y el `owner` del body se ignora |
| H-API-03 | api | SQL con filtro concatenado en listado y resumen (RETO: SQL) | Vulnerabilidad | `owner` se concatena en la consulta: inyección SQL que permite leer o alterar datos fuera del filtro previsto. | `api/app/main.py:70`, `api/app/main.py:93` | alta | Resuelto: consultas con parámetros `?` en `api/app/repositories/tasks.py` |
| H-API-04 | api | SQL con INSERT y SELECT concatenados al crear tareas (RETO: SQL) | Vulnerabilidad | `title`, `description`, `status`, `owner` y `priority` van sin parametrizar: inyección SQL y fallos con comillas en datos legítimos (500). | `api/app/main.py:84`, `api/app/main.py:87` | alta | Resuelto: INSERT y SELECT parametrizados en `api/app/repositories/tasks.py` |
| H-API-05 | api | Carga de archivos usa `upload.filename` directo, sin límite de extensión ni tamaño (RETO: Files) | Vulnerabilidad | Un nombre como `../x` escribe fuera del directorio de cargas; se sobrescriben archivos existentes; cualquier extensión es aceptada; el archivo se lee entero en memoria (DoS por tamaño). La respuesta revela la ruta absoluta del servidor. | `api/app/main.py:109-112` | alta | Pendiente (revisión 2026-11-02): corregidos traversal, extensión, tope de 5 MiB y ruta en `storedAt` (`api/app/services/uploads.py:27-45`), pero un archivo con el mismo nombre de otro usuario lo sobrescribe (verificado: `trainer` pisó el `a.txt` de `student`, `api/app/services/uploads.py:52`) y el límite se aplica después de que Starlette recibe y vuelca el cuerpo completo a disco (`fastapi/routing.py:295`) |
| H-API-06 | api | `python-multipart 0.0.21` con advisories (RETO: SCA) | Vulnerabilidad | Parsea los multipart de `/api/requirements`; versiones anteriores a la corregida tienen advisories de path traversal en el manejo de nombres de archivo. Versión corregida y CVE exacto por confirmar con `pip-audit`/GitHub Advisory. | `api/requirements.txt:5`, `api/app/main.py:108` | alta | Resuelto: `python-multipart` 0.0.31; `pip-audit` sin vulnerabilidades en este paquete |
| H-API-07 | api | `urllib3 2.5.0` con advisories (RETO: SCA) | Vulnerabilidad | Advisories públicos de bombas de descompresión (CVE-2025-66418, CVE-2025-66471, corregidos en 2.6.0; CVE-2026-21441 en 2.6.3). Uso acotado: cliente hacia `AUTH_HEALTH_URL`; riesgo si ese backend responde con contenido malicioso. Versión objetivo por confirmar. | `api/requirements.txt:4`, `api/app/main.py:118` | media | Resuelto: `urllib3` 2.8.0; `pip-audit` sin vulnerabilidades en este paquete |
| H-API-08 | api | Rutas, DB, reglas y serialización en un solo archivo (RETO: Arquitectura) | Refactor | Esquema, semillas, SQL, reglas de resumen y serialización viven dentro de `create_app` y de las rutas: difícil de probar y de cambiar de forma aislada; impide aplicar las buenas prácticas de capas. | `api/app/main.py:29-125` | media | Resuelto: separado en `config`, `database`, `security`, `schemas`, `dependencies`, `repositories/`, `services/` y `routes/`; `main.py` solo ensambla |
| H-API-09 | api | Errores exponen detalles internos (adicional) | Vulnerabilidad | `str(error)` se devuelve al cliente en 401 y en `/api/backend-health` (URL interna, errores de red, cuerpo del backend). Facilita reconocimiento del entorno. | `api/app/main.py:26`, `api/app/main.py:119-121` | media | Resuelto: 401 con `Invalid token` y health con `Backend unavailable`; el detalle va al log |
| H-API-10 | api | CORS abierto con credenciales (adicional) | Vulnerabilidad | `allow_origins=["*"]` con `allow_credentials=True` y métodos/headers `*`: política permisiva sin lista de orígenes. Hay que acordar el origen del frontend. | `api/app/main.py:48-54` | media | Resuelto: orígenes por `CORS_ALLOWED_ORIGINS` (default `http://localhost:4200`), sin credenciales, métodos y headers acotados; falta verificar el consumo desde web |
| H-API-11 | api | Calidad: `dict[str, Any]` crudo, excepciones amplias, condicionales anidados y duplicación (RETO: Calidad) | Refactor | Sin modelos Pydantic no hay validación de `status`/`priority`/longitudes ni esquema en `/docs`. `except Exception` oculta errores reales. Tres `if` anidados y contadores manuales en `summary`; bucles que repiten `as_task`; strings mágicos (`HIGH`, `DONE`, `ARCHIVED`, `TODO`, `MEDIUM`, timeout 3.0). | `api/app/main.py:68`, `api/app/main.py:78-83`, `api/app/main.py:25`, `api/app/main.py:101-104`, `api/app/main.py:72-74`, `api/app/main.py:120` | media | Resuelto: modelos Pydantic y enums en `api/app/schemas.py`, `except` específicos, resumen sin anidamiento y constantes con nombre |
| H-API-12 | api | Conexión SQLite única compartida entre hilos (adicional) | Bug | `check_same_thread=False` con rutas síncronas que FastAPI ejecuta en un pool de hilos: posible acceso concurrente sin control (hipótesis, no comprobada). | `api/app/main.py:35`, `api/app/main.py:71`, `api/app/main.py:85` | baja | Resuelto: confirmado (la prueba concurrente fallaba con `cannot commit - no transaction is active`); ahora hay una conexión por solicitud (`get_connection`) |
| H-API-13 | api | `on_event("shutdown")` obsoleto y `app` creado al importar (adicional) | Refactor | `create_app()` a nivel de módulo crea carpetas y base de datos como efecto secundario del import; `on_event` está en desuso a favor de `lifespan`. | `api/app/main.py:123-125`, `api/app/main.py:130` | baja | Resuelto: `lifespan` prepara carpetas y base de datos; importar `app.main` ya no tiene efectos secundarios |
| H-API-14 | api | Pruebas sin casos de autorización, errores ni archivos hostiles (adicional) | Sugerencia | Solo 4 pruebas felices; no hay caracterización de `owner` ajeno, tokens vencidos/mal formados, nombres de archivo peligrosos, `/api/backend-health` ni 404/422. Se necesitan antes de refactorizar (meta 85% del código modificado). | `api/tests/test_api.py:19-58` | baja | Resuelto: `api/tests/test_characterization.py` y `api/tests/test_findings.py` cubren los casos de seguridad y errores; 48 pruebas, cobertura 100% de `app`. Revisión: faltan pruebas de POST sin token y de límites de longitud |
| H-API-15 | api | Dependencias transitivas y de desarrollo con advisories: `starlette 0.50.0` (corregido en 1.3.1) y `pytest 9.0.2` (9.0.3) (adicional, revisión) | Vulnerabilidad | `pip-audit` sobre el entorno instalado reporta 12 entradas. El código no usa `StaticFiles`, `HTTPEndpoint`, `request.url` ni formularios urlencoded (sin coincidencias en `api/app`), así que el impacto práctico es bajo; subir `fastapi` (arrastra `starlette`) queda fuera del plan aprobado. | `api/requirements.txt:1`, `api/requirements-dev.txt:1` | baja | Pendiente |
| H-API-16 | api | Nombre de archivo con `:` (p. ej. `a:b.txt`) se acepta en Windows y se rechaza en Linux (adicional, pruebas) | Bug | `Path(...).name` trata `a:` como unidad de disco en Windows y devuelve `b.txt`, así que la API responde 201 con `fileName` `b.txt` en vez de 400 `Invalid file name` (regla de `docs/ENDPOINTS.md`). No saca el archivo de la carpeta de cargas; el comportamiento depende del sistema operativo. Detectado por `test_upload_name_with_colon_is_400` (xfail estricto en Windows). | `api/app/services/uploads.py:28` | baja | Pendiente |

### Discovery 2026-11-03: candidatos nuevos (api)

En la fase de descubrimiento, los hallazgos fueron candidatos; no se crearon issues y no se modificó código. H-API-17 fue seleccionado y aprobado por el usuario para implementación; H-API-18 a H-API-20 siguen como candidatos pendientes de revisión humana. El análisis se limitó a `api/`, `docs/ENDPOINTS.md`, `compose.yaml` y `.github/workflows/ci.yml`. Se ejecutó una sonda en proceso con una base temporal (sin tocar `api/data`). Las prioridades propuestas siguen sujetas a revisión.

### H-API-17 — La identidad del token no se valida más allá del secreto y la expiración
- Estado: Resuelto localmente en la API; pendiente confirmar con auth los roles y la vigencia que emite.
- Evidencia inicial (pre-cambio): `api/app/security.py:22,24` aceptaba campos de identidad sin validar; `api/app/schemas.py:33` declaraba `username: str` sin restricciones. Sonda con token de secreto válido: `usuario` vacío → `POST /api/tasks` 201 con `owner: ""`; `usuario` `"  "` y rol arbitrario → 200; `exp` = 10^12 (año ~33658) → 200. Implementación actual en `api/app/security.py:13-14,26,30`.
- Impacto: se crean tareas con dueño vacío o en blanco, y un token sin vencimiento práctico es válido. Complementa H-API-01 (no depende de que se fabrique el token: un emisor defectuoso produciría lo mismo).
- Prioridad propuesta: media
- Contrato potencialmente afectado: 401 común a los 5 endpoints (`docs/ENDPOINTS.md`, sección «Error común»); formato de token compartido con auth. El límite implementado es de cinco segundos restantes hasta `exp`; el formato legado no permite verificar tiempo de emisión. Se acepta solo `TRAINER`, según el conjunto indicado por el usuario; los tokens con rol `STUDENT` pasan a ser rechazados.
- Cómo validarlo: `python tools/lab.py test api` desde la raíz: 144 pasaron, 1 xfail esperado, cobertura 100% (gate 85% cumplido). Las pruebas verifican usuario vacío/en blanco, roles `STUDENT` y desconocidos, expiración lejana y rechazo en los cinco endpoints. Confirmar con auth la compatibilidad de rol y vigencia antes de integrar.

### H-API-18 — `/api/backend-health` crea un `PoolManager` por llamada y reenvía el cuerpo completo del backend
- Estado: CANDIDATO
- Evidencia: `api/app/services/backend_health.py:22` (`urllib3.PoolManager().request(...)` nuevo en cada llamada, nunca cerrado) y `:23` (`response.data.decode("utf-8")` sin tope de tamaño); `api/app/routes/health.py:12-13` (el cuerpo va a la respuesta; cualquier usuario autenticado, sin mirar el rol). `docs/ENDPOINTS.md` pregunta abierta 3: «Hoy se reenvía completo».
- Impacto: cada solicitud deja un pool con conexiones abiertas hasta que el recolector lo libera (posible agotamiento de descriptores bajo carga; no medido) y un backend que responda mucho consume memoria de la API y del cliente. El origen es una variable de entorno, no entrada del usuario, por eso no se propone severidad alta.
- Prioridad propuesta: baja
- Contrato potencialmente afectado: `GET /api/backend-health` (`requestedBy,status,body`; 200 incluso si falla). Truncar `body` cambia el cuerpo devuelto.
- Cómo validarlo: prueba con un backend simulado que devuelva un cuerpo grande y comprobar el tamaño de `body`; repetir 200 llamadas y contar sockets abiertos del proceso (`psutil`/`netstat`) antes y después; decidir el tope con el equipo (pregunta abierta 3).

### H-API-19 — La imagen de la API corre como root y sin `HEALTHCHECK`
- Estado: CANDIDATO
- Evidencia: `api/Dockerfile:1-9`: no hay `USER`, `CMD` en la línea 9 arranca `uvicorn` con el usuario por defecto (root) y `/data` y `/uploads` (línea 7) se crean sin propietario; sin `HEALTHCHECK`. `compose.yaml` monta esos directorios como volúmenes (`api-data`, `api-uploads`) y publica `127.0.0.1:8000`.
- Impacto: un fallo en la carga de archivos o en una dependencia se ejecuta con privilegios de root dentro del contenedor y puede escribir en los volúmenes sin límite de permisos; sin healthcheck `depends_on` no espera a una API lista. No hay evidencia local de explotación; es endurecimiento.
- Prioridad propuesta: media-baja
- Contrato potencialmente afectado: ninguno de los endpoints; sí despliegue (`compose.yaml`, rutas `WORKSHOP_DB_PATH`/`WORKSHOP_UPLOAD_DIR`, permisos de los volúmenes ya creados).
- Cómo validarlo: `docker compose build api` y `docker compose run --rm api id` (hoy `uid=0`); tras el cambio, comprobar que la API escribe en `/data` y `/uploads` y que `GET /api/tasks` responde 200 con un token válido.

### H-API-20 — Listado de tareas sin límite ni paginación y creación sin cuota por usuario
- Estado: CANDIDATO
- Evidencia: `api/app/repositories/tasks.py:10-12` (`SELECT ... WHERE owner = ? ORDER BY id` sin `LIMIT`), `api/app/services/tasks.py:20-21` (convierte todas las filas en `TaskResponse`), `api/app/routes/tasks.py:12-17` (sin parámetros de página); `POST /api/tasks` (`api/app/routes/tasks.py:20-26`) acepta tareas ilimitadas por usuario (solo hay límite de longitud por campo, `api/app/schemas.py:6-7`).
- Impacto: un usuario autenticado puede inflar su propia lista hasta que `GET /api/tasks` y `/api/summary` consuman mucha memoria y tiempo. Efecto acotado a un usuario y a un entorno de laboratorio.
- Prioridad propuesta: baja
- Contrato potencialmente afectado: `GET /api/tasks` devuelve hoy un arreglo completo que consume web; paginar cambiaría el formato o requeriría parámetros opcionales con valor por defecto compatible (necesita revisar el consumo en web, fuera de alcance).
- Cómo validarlo: crear N tareas (p. ej. 10 000) con el token de un usuario y medir latencia y tamaño de `GET /api/tasks` en una base temporal; confirmar con web si usa todo el listado antes de proponer un tope.

Observación documental (no es hallazgo de código): el «Alcance y método» de este archivo dice que no existe `docs/ENDPOINTS.md`, pero el archivo está versionado (`git ls-files docs`) y fue verificado; conviene actualizar esa frase en la revisión.

### Pendientes y coordinación

- Estado `Aprobado`: el usuario indicó en la sesión (2026-11-02) que la revisión humana del plan está aprobada; se registra como declaración del usuario, sin otra evidencia (PR, revisor). Significa plan aprobado, no corregido. `Resuelto` indica implementado y con pruebas ejecutadas en local (sin revisión de código ni PR). Detalle en `PLAN.md`.
- Resuelto el 2026-11-02 (ver ejecuciones en `PLAN.md`): H-API-02 a H-API-14. Sigue pendiente solo H-API-01 (bloqueado por auth).
- H-API-17 está implementado localmente; su integración queda pendiente de confirmar con auth que emite rol `TRAINER` y tokens con un máximo de cinco segundos restantes hasta `exp`.
- `pip-audit -r api/requirements.txt --no-deps` (solo paquetes fijados) quedó sin vulnerabilidades para `urllib3` y `python-multipart`. Corrección de la revisión: esa ejecución no auditó dependencias transitivas; `pip-audit --path api/.venv/Lib/site-packages` encontró `starlette 0.50.0` y `pytest 9.0.2` con advisories (ver H-API-15).
- Acordar y registrar `docs/ENDPOINTS.md` (contrato acordado) en su paso de documentación; hoy solo existe el contrato observado de arriba, con los cambios de contrato aprobados listados en `PLAN.md`.
- Coordinar con auth el formato del token (H-API-01): auth no fue leído por alcance.
- Pendiente verificar con web el origen CORS y que no necesite credenciales.
- Riesgo residual: un archivo subido con el mismo nombre sobrescribe al anterior (decisión D6).
