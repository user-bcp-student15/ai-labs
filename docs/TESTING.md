# Pruebas de ReqFlow

Evidencia de pruebas por componente. Cada ejecución indica componente, IDs de `HALLAZGOS.md`, comando, directorio, código de salida y resultado real.

## api

### Alcance y método

- Componente `api` (FastAPI). Casos derivados de `docs/ENDPOINTS.md` (sección api): 5 endpoints, más CORS. No se agregaron endpoints ni comportamientos que ese documento no describa.
- Herramientas: Python 3.13.15, pytest 9.0.2, pytest-cov (coverage.py 7.17.0), `TestClient` de Starlette (sin servidor real) y bases de datos temporales (`tmp_path`).
- La consulta al backend de auth (`/api/backend-health`) se simula reemplazando `urllib3.PoolManager.request`; no se probó contra el servicio real.
- Este paso solo agrega pruebas y documentos: no se modificó código de `api/app/`.

### Tabla de casos por endpoint

Tipos: **Feliz** (dato válido), **Borde** (límites, vacíos, extensiones) y **Error** (respuesta de error documentada). "Prueba" es el nombre en `api/tests/`; las marcadas "(existente)" ya estaban de pasos anteriores.

#### GET /api/tasks

| ID | Caso | Tipo | Resultado esperado | Prueba |
|---|---|---|---|---|
| GT-00 | Usuario `student` lista sus tareas | Feliz | 200; 2 tareas de `student` ordenadas por `id`, con los 7 campos | `test_characterization.py::test_list_returns_only_the_token_users_tasks_with_expected_shape` (existente) |
| GT-01 | Usuario `trainer` lista sus tareas | Feliz | 200; solo la tarea `Trainer notes` (id 3) | `test_get_tasks_lists_trainer_tasks_with_trainer_token` |
| GT-02 | Usuario sin tareas | Borde | 200 y `[]` | `test_get_tasks_for_user_without_tasks_is_empty_list` |
| GT-03 | `owner=` vacío | Borde | 200; tareas del usuario del token | `test_get_tasks_empty_owner_parameter_uses_token_user` |
| GT-04 | Orden tras crear tareas | Borde | `id` ascendente; 2 iniciales + 2 nuevas | `test_get_tasks_are_ordered_by_ascending_id` |
| GT-05 | **Un usuario no puede leer tareas de otro `owner`** (en ambos sentidos) | Error | 403 `{"detail": "Forbidden"}`; el cuerpo no contiene tareas ajenas | `test_get_tasks_other_owner_is_forbidden_and_leaks_nothing` |
| GT-06 | Token ausente, mal formado o vencido | Error | 401 `{"detail": "Invalid token"}` (3 variantes) | `test_get_tasks_invalid_token_is_401_with_generic_body` |
| GT-07 | `DELETE /api/tasks` | Error | 405 `{"detail": "Method Not Allowed"}` | `test_get_tasks_method_not_allowed_is_405` |
| GT-08 | `owner` igual al usuario del token | Borde | 200 con sus 2 tareas | `test_findings.py::test_own_owner_query_is_allowed` (existente) |
| GT-09 | `owner` con SQL (`x' OR '1'='1`) como usuario | Error | 200 y `[]`, sin filtrar otras tareas | `test_findings.py::test_list_filter_is_parameterized` (existente) |

#### POST /api/tasks

| ID | Caso | Tipo | Resultado esperado | Prueba |
|---|---|---|---|---|
| PT-01 | Los 4 campos válidos | Feliz | 201; mismos valores, `owner` = `student`, aparece en el listado | `test_post_task_with_all_fields_returns_201_and_is_listed` |
| PT-00 | Solo `title` | Feliz | 201; `description` `""`, `status` `TODO`, `priority` `MEDIUM` | `test_characterization.py::test_create_task_applies_defaults_and_returns_created_task` (existente) |
| PT-02 | Los 4 estados × 3 prioridades | Borde | 201 en las 12 combinaciones | `test_post_task_accepts_every_documented_status_and_priority` |
| PT-03 | `title` de 1, 120 y 121 caracteres | Borde | 201, 201 y 422 | `test_post_task_title_length_boundaries` |
| PT-04 | `description` de 0, 2000 y 2001 caracteres | Borde | 201, 201 y 422 | `test_post_task_description_length_boundaries` |
| PT-05 | Campos desconocidos y `owner` ajeno en el cuerpo | Borde | 201; se ignoran; la tarea es de `student` y no aparece en `trainer` | `test_post_task_ignores_unknown_fields_and_owner` |
| PT-06 | Objeto vacío `{}` | Borde | 422 y no se crea ninguna tarea | `test_post_task_empty_object_is_rejected_not_defaulted` |
| PT-07 | `title` ausente, vacío o largo; `description` larga; `status` o `priority` inválidos; `title` no texto | Error | 422 con un único error de `type` y `loc` documentados | `test_post_task_validation_errors_are_422_with_field_location` (7 casos) |
| PT-08 | Sin cuerpo | Error | 422, `type` `missing`, `loc` `["body"]` | `test_post_task_without_body_is_422` |
| PT-09 | JSON mal formado | Error | 422, `type` `json_invalid` | `test_post_task_malformed_json_is_422` |
| PT-10 | Token ausente, mal formado o vencido | Error | 401 `{"detail": "Invalid token"}` y no se crea la tarea | `test_post_task_invalid_token_is_401_and_creates_nothing` |
| PT-11 | Comillas y SQL en `title` y `description` | Borde | 201; se guardan como texto | `test_findings.py::test_create_stores_quotes_literally`, `::test_create_does_not_run_injected_sql` (existentes) |

#### GET /api/summary

| ID | Caso | Tipo | Resultado esperado | Prueba |
|---|---|---|---|---|
| GS-00 | Tareas en varios estados y prioridades | Feliz | total, `byStatus` y `highPriorityOpen` correctos | `test_characterization.py::test_summary_counts_by_status_and_open_high_priority` (existente) |
| GS-02 | Datos iniciales de `student` | Feliz | `{"owner": "student", "total": 2, "byStatus": {"TODO": 1, "IN_PROGRESS": 1}, "highPriorityOpen": 1}` | `test_summary_of_seeded_student_matches_documented_example` |
| GS-01 | Resumen de `trainer` tras crear tareas de `student` | Borde | `trainer` no cambia (total 1) | `test_summary_of_trainer_is_not_affected_by_student_tasks` |
| GS-03 | `owner` vacío o igual al usuario | Borde | 200; `owner` = `student` | `test_summary_accepts_empty_or_own_owner_parameter` |
| GS-04 | Tareas `HIGH` en `DONE` y `ARCHIVED` | Borde | No cuentan en `highPriorityOpen` | `test_summary_high_priority_closed_tasks_are_not_open` |
| GS-07 | Usuario sin tareas | Borde | `{"owner": "nobody", "total": 0, "byStatus": {}, "highPriorityOpen": 0}` | `test_characterization.py::test_summary_of_user_without_tasks_is_empty` (existente) |
| GS-05 | **`owner` de otro usuario** (en ambos sentidos) | Error | 403 `{"detail": "Forbidden"}` | `test_summary_other_owner_is_forbidden_and_leaks_nothing` |
| GS-06 | Token ausente, mal formado o vencido | Error | 401 `{"detail": "Invalid token"}` | `test_summary_invalid_token_is_401_with_generic_body` |

#### POST /api/requirements

| ID | Caso | Tipo | Resultado esperado | Prueba |
|---|---|---|---|---|
| PR-01 | `.txt`, `.md`, `.pdf`, `.docx`, mayúsculas y nombre con espacio y guion | Feliz | 201; cuerpo `{owner, fileName, storedAt, size}`; contenido guardado | `test_upload_accepts_allowed_extensions_and_stores_the_content` (6 casos) |
| PR-02 | Archivo vacío | Borde | 201 con `size` 0 | `test_upload_empty_file_is_accepted_with_size_zero` |
| PR-03 | Exactamente 5 MiB | Borde | 201 con `size` 5 242 880 | `test_upload_exactly_at_size_limit_is_accepted` |
| PR-04 | 5 MiB + 1 byte | Error | 413 `{"detail": "File too large"}` y no se guarda | `test_upload_one_byte_over_the_limit_is_413_and_stores_nothing` |
| PR-05 | Nombre sin extensión válida (`README`, `archivo`, `notes.`) | Borde / Error | 415 `{"detail": "File type not allowed"}` | `test_upload_name_without_allowed_extension_is_415` |
| PR-06 | `.exe`, `.py`, `archive.txt.exe` | Error | 415 | `test_upload_disallowed_extension_is_415` |
| PR-07 | `..`, `bad*name.txt`, `.txt` | Error | 400 `{"detail": "Invalid file name"}` | `test_upload_invalid_name_is_400` |
| PR-07b | `a:b.txt` | Error | 400 `{"detail": "Invalid file name"}` | `test_upload_name_with_colon_is_400` — **falla en Windows (xfail estricto, H-API-16)** |
| PR-08 | Ruta en el nombre (`../x`, `..\x`, `a/b/x`) | Borde | 201 con `fileName` `outside.txt`; nada fuera de la carpeta de cargas | `test_upload_path_in_name_is_reduced_to_the_last_segment` (3 casos) |
| PR-09 | Sin la parte `file` | Error | 422 con el cuerpo documentado | `test_upload_without_file_part_is_422` |
| PR-10 | Token ausente, mal formado o vencido | Error | 401 y no se guarda el archivo | `test_upload_invalid_token_is_401_and_stores_nothing` |

#### GET /api/backend-health

| ID | Caso | Tipo | Resultado esperado | Prueba |
|---|---|---|---|---|
| BH-01 | Backend responde 200 | Feliz | `{"requestedBy": "student", "status": 200, "body": "{\"status\":\"UP\"}"}`; se consulta `AUTH_HEALTH_URL` con `GET` y timeout 3.0 | `test_backend_health_happy_path_uses_configured_url_and_timeout` |
| BH-02 | Usuario `trainer` | Feliz | `requestedBy` = `trainer` | `test_backend_health_reports_the_requesting_user` |
| BH-03 | Backend responde 503 | Borde | 200 con `status` 503 y su cuerpo | `test_backend_health_upstream_error_status_is_passed_through_with_200` |
| BH-04 | Backend responde sin cuerpo | Borde | `body` `""` | `test_backend_health_empty_upstream_body_is_an_empty_string` |
| BH-05 | Error de red, reintentos agotados o tiempo agotado | Borde | 200; `status` 0; `body` `Backend unavailable` | `test_backend_health_unreachable_backend_is_200_with_status_zero` (3 casos) |
| BH-06 | Cuerpo que no es UTF-8 | Borde | 200; `status` 0; `Backend unavailable` | `test_backend_health_non_utf8_body_is_reported_as_unavailable` |
| BH-07 | Token ausente, mal formado o vencido | Error | 401 y no se consulta al backend | `test_backend_health_invalid_token_is_401_and_does_not_call_the_backend` |

#### CORS (todos los endpoints)

| ID | Caso | Tipo | Resultado esperado | Prueba |
|---|---|---|---|---|
| CO-01 | Preflight desde `http://localhost:4200` | Feliz | 200; `allow-origin` igual al origen; métodos `GET, POST, OPTIONS`; sin credenciales | `test_cors_preflight_from_allowed_origin_is_200_with_documented_policy` |
| CO-02 | Preflight desde `http://evil.example` | Error | 400 y texto `Disallowed CORS origin`; sin `allow-origin` | `test_cors_preflight_from_unknown_origin_is_400` |
| CO-03 | Orígenes por `CORS_ALLOWED_ORIGINS` | Borde | Se aceptan los configurados | `test_findings.py::test_cors_origins_come_from_environment` (existente) |

Los `404` para rutas inexistentes están en `test_characterization.py::test_unknown_route_and_method_not_allowed` (existente).

### Ejecuciones realizadas

Todas con Python 3.13.15 sobre Windows. "Raíz" es `ai-labs/`; `api/` es el directorio del componente.

| # | Comando | Directorio | Código de salida | Resultado real | IDs |
|---|---|---|---|---|---|
| 1 | `.venv\Scripts\python.exe -m pytest tests/test_endpoints.py` | `api/` | 1 | 87 pasaron, 1 falló: `test_upload_invalid_name_is_400[a:b.txt]` (201 en vez de 400). Ver [Fallos](#fallos-y-bugs-encontrados) | PR-07, H-API-16 |
| 2 | `python tools/lab.py test api` | raíz | 0 | 135 pasaron, 1 xfail esperado; cobertura 100% (gate de 85% cumplido). Antes de agregar CO-01 y CO-02 | todos, H-API-16 |
| 3 | `.venv\Scripts\python.exe -m pytest --cov=app --cov-branch --cov-report=json` | `api/` | no registrado | 135 pasaron, 1 xfail; números de la sección de cobertura | todos |
| 4 | `.venv\Scripts\python.exe -m pytest tests/test_endpoints.py --cov=app --cov-branch` | `api/` | no registrado | 87 pasaron, 1 xfail; cobertura 99% con solo estas pruebas (275 sentencias, 0 sin cubrir; 16 ramas, 1 parcial) | GT, PT, GS, PR, BH |
| 5 | `python tools/lab.py test api` | raíz | 0 | **137 pasaron, 1 xfail**; cobertura 100.00% (gate de 85% cumplido); 1 aviso (`DeprecationWarning` de `starlette/testclient.py:45`, no de `api/app`) | todos |
| 6 | `pytest` por archivo | `api/` | no registrado | `test_api.py` 4 pasaron; `test_characterization.py` 15; `test_findings.py` 29; `test_endpoints.py` 89 pasaron y 1 xfail | todos |

El resultado vigente es el de la ejecución 5 (código de salida 0, comprobado). La ejecución 1 terminó con 1; en las ejecuciones 2 y 5 se registró 0; en 3, 4 y 6 no se registró el código de salida, solo el resultado de pytest.

Ejecuciones de pasos anteriores (resultados de `PLAN.md`): línea base 4 pruebas, 91.07%; 48 pruebas tras el refactor, 100%. No se repiten aquí.

### Cobertura

- **Método:** `pytest-cov` (coverage.py 7.17.0) con `branch = true` y `source = ["app"]` (`api/pyproject.toml`). Porcentaje = (sentencias cubiertas + ramas cubiertas) / (sentencias + ramas). Gate del repositorio: `--cov-fail-under=85` sobre todo `app` (`tools/lab.py`), sin cambios.
- **Cobertura del código modificado:** este paso no modificó código de `api/app/`. El código modificado por el refactor es todo `api/app/` (`main.py` modificado; el resto, archivos nuevos), así que coincide con el total:

| Medida | Numerador | Denominador | Porcentaje |
|---|---|---|---|
| Sentencias | 275 | 275 | 100% |
| Ramas | 16 | 16 | 100% |
| Sentencias + ramas (cobertura reportada) | 291 | 291 | 100.00% |

- **Cobertura global (aparte):** la medición solo incluye `app`, y es la misma del cuadro: 100.00% (ejecución 5). No hay cobertura global de `tests/` ni de `.venv/`.
- **Por archivo** (sentencias cubiertas / total; ramas cubiertas / total; ejecución 3):

| Archivo | Sentencias | Ramas |
|---|---|---|
| `app/config.py` | 19 / 19 | 0 / 0 |
| `app/database.py` | 14 / 14 | 2 / 2 |
| `app/dependencies.py` | 19 / 19 | 2 / 2 |
| `app/main.py` | 26 / 26 | 2 / 2 |
| `app/repositories/tasks.py` | 16 / 16 | 0 / 0 |
| `app/routes/health.py` | 9 / 9 | 0 / 0 |
| `app/routes/requirements.py` | 12 / 12 | 0 / 0 |
| `app/routes/tasks.py` | 15 / 15 | 0 / 0 |
| `app/schemas.py` | 48 / 48 | 0 / 0 |
| `app/security.py` | 21 / 21 | 2 / 2 |
| `app/services/backend_health.py` | 18 / 18 | 0 / 0 |
| `app/services/tasks.py` | 19 / 19 | 0 / 0 |
| `app/services/uploads.py` | 39 / 39 | 8 / 8 |

- **Límites:** la cobertura mide qué líneas se ejecutan, no la calidad de las aserciones. No se hizo prueba de mutación. El informe HTML queda en `api/htmlcov/index.html` (generado por el comando, no versionado). La medición del diff contra `main` no se calculó aparte porque todo `api/app/` es nuevo o modificado.

### Fallos y bugs encontrados

| ID | Qué falla | Evidencia | Tratamiento |
|---|---|---|---|
| H-API-16 (nuevo, `Pendiente`) | `POST /api/requirements` con nombre `a:b.txt` devuelve 201 con `fileName` `b.txt` en Windows; `docs/ENDPOINTS.md` indica que el nombre debe contener solo letras, dígitos, `_`, espacio, `.` y `-` (400 si no). Causa: `Path("a:b.txt").name` en Windows trata `a:` como unidad (`api/app/services/uploads.py:28`). En Linux se espera 400 (no ejecutado) | Ejecución 1: `assert (201, {'fileName'...'b.txt'}) == (400, ...)` | La prueba conserva la expectativa de 400 y está marcada `xfail(strict=True)` solo en Windows con el motivo H-API-16. No se cambió el resultado esperado para que pase. Cuando se corrija el código, `strict` fallará y obligará a quitar el marcador. Registrado en `HALLAZGOS.md` |

### Pendientes (sin prueba ejecutada)

| Tema | Por qué falta |
|---|---|
| H-API-01 (token sin firma) | Bloqueado hasta coordinar con auth; no hay contrato de token nuevo que probar. |
| H-API-05 (abierto) | Sobrescritura de archivos entre usuarios y rechazo de archivos grandes antes de recibirlos: `docs/ENDPOINTS.md` los declara riesgo pendiente, no comportamiento esperado, así que no hay prueba de aceptación. Hoy no se fija con una prueba el comportamiento defectuoso para no darlo por bueno. |
| H-API-15 | Dependencias transitivas (`starlette`, `pytest`); se resuelve con `pip-audit`, no con pruebas de endpoints. |
| Preguntas abiertas de `docs/ENDPOINTS.md` (título solo con espacios, token sin `Bearer`, tamaño de `body` en health, error 500 interno, rol `trainer`) | No se prueban: el documento no fija un comportamiento esperado. Al decidirlas, agregar el caso. |
| Ejecución en Linux (Docker, sistema del contenedor) | No ejecutada; el resultado de PR-07b allí es esperado, no comprobado. |
| `uvicorn` real | Las pruebas usan `TestClient`; no se probó el servidor, el `lifespan` ni la concurrencia con `uvicorn`. |
| Backend de auth real | `backend-health` se probó con respuestas simuladas, salvo el caso inaccesible comprobado a mano en pasos anteriores. |

### Pruebas propuestas (no implementadas ni ejecutadas)

1. Cuando se decida H-API-05: dos usuarios suben el mismo nombre y el segundo no debe modificar el archivo del primero.
2. Cuando se decida H-API-05: rechazo por `Content-Length` mayor a 5 MiB sin guardar el cuerpo.
3. Cuando exista el token firmado (H-API-01): firma alterada, emisor, audiencia y expiración inválidos devuelven 401; token legado rechazado.
4. Ejecutar la suite en Linux para confirmar PR-07b y la ausencia de diferencias por sistema operativo.
5. Prueba contra `uvicorn` con solicitudes concurrentes de escritura (H-API-12) y contra un backend de auth real o un servidor HTTP local de prueba.
6. Prueba de mutación (p. ej. con `mutmut`, que sería una dependencia de desarrollo nueva a justificar) para medir la calidad de las aserciones.

### Cómo ejecutar

```powershell
# Desde la raíz (ai-labs/): suite completa con el gate de 85%
python tools/lab.py test api

# Desde api/: solo las pruebas por endpoint, sin gate
.venv\Scripts\python.exe -m pytest tests/test_endpoints.py
```

### Código de las pruebas

Archivos en `api/tests/`: `helpers.py` y `conftest.py` (tokens y fixtures compartidos), `test_api.py`, `test_characterization.py` y `test_findings.py` (pasos anteriores) y `test_endpoints.py` (este paso). Se copia el archivo nuevo tal como se ejecutó; los demás se conservan en el repositorio.

`api/tests/helpers.py`

```python
import base64
import time

TEST_TOKEN_SECRET = "WORKSHOP_SECRET_2026"
TEST_TOKEN_TTL_SECONDS = 3600


def build_token(username: str = "student", role: str = "STUDENT", ttl_seconds: int = TEST_TOKEN_TTL_SECONDS) -> str:
    raw = f"{username}|{role}|{int(time.time()) + ttl_seconds}|{TEST_TOKEN_SECRET}"
    return base64.b64encode(raw.encode()).decode()


def auth_headers(username: str = "student", role: str = "STUDENT") -> dict[str, str]:
    return {"Authorization": f"Bearer {build_token(username, role)}"}
```

`api/tests/conftest.py`

```python
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def upload_dir(tmp_path: Path) -> Path:
    return tmp_path / "uploads"


@pytest.fixture
def client(tmp_path: Path, upload_dir: Path) -> Iterator[TestClient]:
    app = create_app(str(tmp_path / "workshop.db"), str(upload_dir))
    with TestClient(app) as test_client:
        yield test_client
```

`api/tests/test_endpoints.py`

```python
"""Pruebas por endpoint según docs/ENDPOINTS.md: camino feliz, casos borde y errores.

Cada prueba cita entre paréntesis el caso de la tabla de docs/TESTING.md.
"""
import sys
from types import SimpleNamespace

import pytest
import urllib3
from fastapi.testclient import TestClient
from helpers import auth_headers, build_token

from app.main import create_app

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
TITLE_MAX_LENGTH = 120
DESCRIPTION_MAX_LENGTH = 2000
STUDENT_SEEDED_TASKS = 2
UPSTREAM_TIMEOUT_SECONDS = 3.0
INVALID_TOKEN_BODY = {"detail": "Invalid token"}
FORBIDDEN_BODY = {"detail": "Forbidden"}
TRAINER = {"username": "trainer", "role": "TRAINER"}

INVALID_TOKEN_HEADERS = {
    "missing": {},
    "malformed": {"Authorization": "Bearer not-base64"},
    "expired": {"Authorization": f"Bearer {build_token(ttl_seconds=-10)}"},
}


def post_task(client: TestClient, payload: dict, **headers_args: str):
    return client.post("/api/tasks", headers=auth_headers(**headers_args), json=payload)


def upload(client: TestClient, name: str, content: bytes = b"x"):
    return client.post("/api/requirements", headers=auth_headers(), files={"file": (name, content, "text/plain")})


@pytest.fixture
def fake_backend(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Sustituye la consulta HTTP al backend de auth y registra los argumentos recibidos."""
    backend = SimpleNamespace(response=SimpleNamespace(status=200, data=b"UP"), error=None, calls=[])

    def request(self, method, url, **kwargs):
        backend.calls.append((method, url, kwargs))
        if backend.error:
            raise backend.error
        return backend.response

    monkeypatch.setattr(urllib3.PoolManager, "request", request)
    return backend


# ---------------------------------------------------------------- GET /api/tasks


def test_get_tasks_lists_trainer_tasks_with_trainer_token(client: TestClient) -> None:  # GT-01
    body = client.get("/api/tasks", headers=auth_headers(**TRAINER)).json()
    assert [(task["id"], task["owner"], task["title"]) for task in body] == [(3, "trainer", "Trainer notes")]


def test_get_tasks_for_user_without_tasks_is_empty_list(client: TestClient) -> None:  # GT-02
    response = client.get("/api/tasks", headers=auth_headers("nobody"))
    assert (response.status_code, response.json()) == (200, [])


def test_get_tasks_empty_owner_parameter_uses_token_user(client: TestClient) -> None:  # GT-03
    response = client.get("/api/tasks", params={"owner": ""}, headers=auth_headers())
    assert response.status_code == 200
    assert {task["owner"] for task in response.json()} == {"student"}
    assert len(response.json()) == STUDENT_SEEDED_TASKS


def test_get_tasks_are_ordered_by_ascending_id(client: TestClient) -> None:  # GT-04
    post_task(client, {"title": "first"})
    post_task(client, {"title": "second"})
    ids = [task["id"] for task in client.get("/api/tasks", headers=auth_headers()).json()]
    assert ids == sorted(ids)
    assert len(ids) == STUDENT_SEEDED_TASKS + 2


def test_get_tasks_other_owner_is_forbidden_and_leaks_nothing(client: TestClient) -> None:  # GT-05
    as_student = client.get("/api/tasks", params={"owner": "trainer"}, headers=auth_headers())
    as_trainer = client.get("/api/tasks", params={"owner": "student"}, headers=auth_headers(**TRAINER))

    assert (as_student.status_code, as_student.json()) == (403, FORBIDDEN_BODY)
    assert (as_trainer.status_code, as_trainer.json()) == (403, FORBIDDEN_BODY)
    assert "Trainer notes" not in as_student.text
    assert "Refactor login" not in as_trainer.text


@pytest.mark.parametrize("headers", INVALID_TOKEN_HEADERS.values(), ids=INVALID_TOKEN_HEADERS.keys())
def test_get_tasks_invalid_token_is_401_with_generic_body(client: TestClient, headers: dict) -> None:  # GT-06
    response = client.get("/api/tasks", headers=headers)
    assert (response.status_code, response.json()) == (401, INVALID_TOKEN_BODY)


def test_get_tasks_method_not_allowed_is_405(client: TestClient) -> None:  # GT-07
    response = client.delete("/api/tasks", headers=auth_headers())
    assert (response.status_code, response.json()) == (405, {"detail": "Method Not Allowed"})


# --------------------------------------------------------------- POST /api/tasks


def test_post_task_with_all_fields_returns_201_and_is_listed(client: TestClient) -> None:  # PT-01
    payload = {"title": "Add tests", "description": "Improve coverage", "status": "IN_PROGRESS", "priority": "HIGH"}
    response = post_task(client, payload)

    assert response.status_code == 201
    created = response.json()
    assert {key: created[key] for key in payload} == payload
    assert created["owner"] == "student"
    assert created in client.get("/api/tasks", headers=auth_headers()).json()


@pytest.mark.parametrize("status", ["TODO", "IN_PROGRESS", "DONE", "ARCHIVED"])
@pytest.mark.parametrize("priority", ["HIGH", "MEDIUM", "LOW"])
def test_post_task_accepts_every_documented_status_and_priority(client: TestClient, status: str, priority: str) -> None:  # PT-02
    response = post_task(client, {"title": "t", "status": status, "priority": priority})
    assert response.status_code == 201
    assert (response.json()["status"], response.json()["priority"]) == (status, priority)


@pytest.mark.parametrize("length,expected", [(1, 201), (TITLE_MAX_LENGTH, 201), (TITLE_MAX_LENGTH + 1, 422)])
def test_post_task_title_length_boundaries(client: TestClient, length: int, expected: int) -> None:  # PT-03
    assert post_task(client, {"title": "a" * length}).status_code == expected


@pytest.mark.parametrize("length,expected", [(0, 201), (DESCRIPTION_MAX_LENGTH, 201), (DESCRIPTION_MAX_LENGTH + 1, 422)])
def test_post_task_description_length_boundaries(client: TestClient, length: int, expected: int) -> None:  # PT-04
    assert post_task(client, {"title": "t", "description": "d" * length}).status_code == expected


def test_post_task_ignores_unknown_fields_and_owner(client: TestClient) -> None:  # PT-05
    response = post_task(client, {"title": "t", "owner": "trainer", "unknown": 1})

    assert response.status_code == 201
    assert response.json()["owner"] == "student"
    assert "unknown" not in response.json()
    assert "t" not in [task["title"] for task in client.get("/api/tasks", headers=auth_headers(**TRAINER)).json()]


def test_post_task_empty_object_is_rejected_not_defaulted(client: TestClient) -> None:  # PT-06
    assert post_task(client, {}).status_code == 422
    assert len(client.get("/api/tasks", headers=auth_headers()).json()) == STUDENT_SEEDED_TASKS


@pytest.mark.parametrize(
    "payload,error_type,location",
    [
        ({}, "missing", ["body", "title"]),
        ({"title": ""}, "string_too_short", ["body", "title"]),
        ({"title": "a" * (TITLE_MAX_LENGTH + 1)}, "string_too_long", ["body", "title"]),
        ({"title": "t", "description": "d" * (DESCRIPTION_MAX_LENGTH + 1)}, "string_too_long", ["body", "description"]),
        ({"title": "t", "status": "WHATEVER"}, "enum", ["body", "status"]),
        ({"title": "t", "priority": "URGENT"}, "enum", ["body", "priority"]),
        ({"title": 5}, "string_type", ["body", "title"]),
    ],
    ids=["missing-title", "empty-title", "long-title", "long-description", "bad-status", "bad-priority", "title-not-string"],
)
def test_post_task_validation_errors_are_422_with_field_location(
    client: TestClient, payload: dict, error_type: str, location: list
) -> None:  # PT-07
    response = post_task(client, payload)

    assert response.status_code == 422
    (detail,) = response.json()["detail"]
    assert (detail["type"], detail["loc"]) == (error_type, location)


def test_post_task_without_body_is_422(client: TestClient) -> None:  # PT-08
    response = client.post("/api/tasks", headers=auth_headers())
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "missing"
    assert response.json()["detail"][0]["loc"] == ["body"]


def test_post_task_malformed_json_is_422(client: TestClient) -> None:  # PT-09
    headers = {**auth_headers(), "Content-Type": "application/json"}
    response = client.post("/api/tasks", headers=headers, content="{bad")
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "json_invalid"


@pytest.mark.parametrize("headers", INVALID_TOKEN_HEADERS.values(), ids=INVALID_TOKEN_HEADERS.keys())
def test_post_task_invalid_token_is_401_and_creates_nothing(client: TestClient, headers: dict) -> None:  # PT-10
    response = client.post("/api/tasks", headers=headers, json={"title": "t"})

    assert (response.status_code, response.json()) == (401, INVALID_TOKEN_BODY)
    assert len(client.get("/api/tasks", headers=auth_headers()).json()) == STUDENT_SEEDED_TASKS


# ------------------------------------------------------------- GET /api/summary


def test_summary_of_trainer_is_not_affected_by_student_tasks(client: TestClient) -> None:  # GS-01
    post_task(client, {"title": "t", "priority": "HIGH"})
    body = client.get("/api/summary", headers=auth_headers(**TRAINER)).json()
    assert body == {"owner": "trainer", "total": 1, "byStatus": {"TODO": 1}, "highPriorityOpen": 0}


def test_summary_of_seeded_student_matches_documented_example(client: TestClient) -> None:  # GS-02
    body = client.get("/api/summary", headers=auth_headers()).json()
    assert body == {"owner": "student", "total": 2, "byStatus": {"TODO": 1, "IN_PROGRESS": 1}, "highPriorityOpen": 1}


@pytest.mark.parametrize("owner", ["", "student"])
def test_summary_accepts_empty_or_own_owner_parameter(client: TestClient, owner: str) -> None:  # GS-03
    response = client.get("/api/summary", params={"owner": owner}, headers=auth_headers())
    assert response.status_code == 200
    assert response.json()["owner"] == "student"


def test_summary_high_priority_closed_tasks_are_not_open(client: TestClient) -> None:  # GS-04
    post_task(client, {"title": "done", "priority": "HIGH", "status": "DONE"})
    post_task(client, {"title": "archived", "priority": "HIGH", "status": "ARCHIVED"})
    body = client.get("/api/summary", headers=auth_headers()).json()
    assert body["highPriorityOpen"] == 1
    assert body["total"] == STUDENT_SEEDED_TASKS + 2


def test_summary_other_owner_is_forbidden_and_leaks_nothing(client: TestClient) -> None:  # GS-05
    as_student = client.get("/api/summary", params={"owner": "trainer"}, headers=auth_headers())
    as_trainer = client.get("/api/summary", params={"owner": "student"}, headers=auth_headers(**TRAINER))

    assert (as_student.status_code, as_student.json()) == (403, FORBIDDEN_BODY)
    assert (as_trainer.status_code, as_trainer.json()) == (403, FORBIDDEN_BODY)


@pytest.mark.parametrize("headers", INVALID_TOKEN_HEADERS.values(), ids=INVALID_TOKEN_HEADERS.keys())
def test_summary_invalid_token_is_401_with_generic_body(client: TestClient, headers: dict) -> None:  # GS-06
    response = client.get("/api/summary", headers=headers)
    assert (response.status_code, response.json()) == (401, INVALID_TOKEN_BODY)


# ------------------------------------------------------- POST /api/requirements


@pytest.mark.parametrize("name", ["notes.txt", "notes.md", "notes.pdf", "notes.docx", "NOTES.TXT", "my req-1.md"])
def test_upload_accepts_allowed_extensions_and_stores_the_content(client: TestClient, upload_dir, name: str) -> None:  # PR-01
    response = upload(client, name, b"contenido")

    assert response.status_code == 201
    assert response.json() == {"owner": "student", "fileName": name, "storedAt": name, "size": 9}
    assert (upload_dir / name).read_bytes() == b"contenido"


def test_upload_empty_file_is_accepted_with_size_zero(client: TestClient, upload_dir) -> None:  # PR-02
    response = upload(client, "empty.txt", b"")
    assert response.status_code == 201
    assert response.json()["size"] == 0
    assert (upload_dir / "empty.txt").read_bytes() == b""


def test_upload_exactly_at_size_limit_is_accepted(client: TestClient) -> None:  # PR-03
    response = upload(client, "max.txt", b"0" * MAX_UPLOAD_BYTES)
    assert (response.status_code, response.json()["size"]) == (201, MAX_UPLOAD_BYTES)


def test_upload_one_byte_over_the_limit_is_413_and_stores_nothing(client: TestClient, upload_dir) -> None:  # PR-04
    response = upload(client, "big.txt", b"0" * (MAX_UPLOAD_BYTES + 1))
    assert (response.status_code, response.json()) == (413, {"detail": "File too large"})
    assert not (upload_dir / "big.txt").exists()


@pytest.mark.parametrize("name", ["README", "archivo", "notes."])
def test_upload_name_without_allowed_extension_is_415(client: TestClient, name: str) -> None:  # PR-05
    response = upload(client, name)
    assert (response.status_code, response.json()) == (415, {"detail": "File type not allowed"})


@pytest.mark.parametrize("name", ["payload.exe", "script.py", "archive.txt.exe"])
def test_upload_disallowed_extension_is_415(client: TestClient, name: str) -> None:  # PR-06
    response = upload(client, name)
    assert (response.status_code, response.json()) == (415, {"detail": "File type not allowed"})


@pytest.mark.parametrize("name", ["..", "bad*name.txt", ".txt"])
def test_upload_invalid_name_is_400(client: TestClient, name: str) -> None:  # PR-07
    response = upload(client, name)
    assert (response.status_code, response.json()) == (400, {"detail": "Invalid file name"})


@pytest.mark.xfail(
    sys.platform == "win32",
    strict=True,
    reason="H-API-16: en Windows Path('a:b.txt').name devuelve 'b.txt' y la API responde 201 en vez de 400",
)
def test_upload_name_with_colon_is_400(client: TestClient) -> None:  # PR-07b
    response = upload(client, "a:b.txt")
    assert (response.status_code, response.json()) == (400, {"detail": "Invalid file name"})


@pytest.mark.parametrize("raw_name", ["../outside.txt", "..\\outside.txt", "a/b/outside.txt"])
def test_upload_path_in_name_is_reduced_to_the_last_segment(client: TestClient, tmp_path, upload_dir, raw_name: str) -> None:  # PR-08
    response = upload(client, raw_name)

    assert response.status_code == 201
    assert response.json()["fileName"] == "outside.txt"
    assert (upload_dir / "outside.txt").exists()
    assert not (tmp_path / "outside.txt").exists()


def test_upload_without_file_part_is_422(client: TestClient) -> None:  # PR-09
    response = client.post("/api/requirements", headers=auth_headers())
    assert response.status_code == 422
    assert response.json() == {"detail": [{"type": "missing", "loc": ["body", "file"], "msg": "Field required", "input": None}]}


@pytest.mark.parametrize("headers", INVALID_TOKEN_HEADERS.values(), ids=INVALID_TOKEN_HEADERS.keys())
def test_upload_invalid_token_is_401_and_stores_nothing(client: TestClient, upload_dir, headers: dict) -> None:  # PR-10
    response = client.post("/api/requirements", headers=headers, files={"file": ("a.txt", b"x", "text/plain")})

    assert (response.status_code, response.json()) == (401, INVALID_TOKEN_BODY)
    assert not (upload_dir / "a.txt").exists()


# ------------------------------------------------------------------------- CORS


def test_cors_preflight_from_allowed_origin_is_200_with_documented_policy(client: TestClient) -> None:  # CO-01
    response = client.options(
        "/api/tasks",
        headers={
            "Origin": "http://localhost:4200",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:4200"
    assert response.headers["access-control-allow-methods"] == "GET, POST, OPTIONS"
    assert "access-control-allow-credentials" not in response.headers


def test_cors_preflight_from_unknown_origin_is_400(client: TestClient) -> None:  # CO-02
    response = client.options(
        "/api/tasks", headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "GET"}
    )

    assert (response.status_code, response.text) == (400, "Disallowed CORS origin")
    assert "access-control-allow-origin" not in response.headers


# ------------------------------------------------------ GET /api/backend-health


def test_backend_health_happy_path_uses_configured_url_and_timeout(
    monkeypatch: pytest.MonkeyPatch, tmp_path, fake_backend: SimpleNamespace
) -> None:  # BH-01
    monkeypatch.setenv("AUTH_HEALTH_URL", "http://auth.test:8080/q/health")
    fake_backend.response = SimpleNamespace(status=200, data=b'{"status":"UP"}')

    with TestClient(create_app(str(tmp_path / "w.db"), str(tmp_path / "u"))) as client:
        response = client.get("/api/backend-health", headers=auth_headers())

    assert response.json() == {"requestedBy": "student", "status": 200, "body": '{"status":"UP"}'}
    ((method, url, kwargs),) = fake_backend.calls
    assert (method, url, kwargs["timeout"]) == ("GET", "http://auth.test:8080/q/health", UPSTREAM_TIMEOUT_SECONDS)


def test_backend_health_reports_the_requesting_user(client: TestClient, fake_backend: SimpleNamespace) -> None:  # BH-02
    body = client.get("/api/backend-health", headers=auth_headers(**TRAINER)).json()
    assert body["requestedBy"] == "trainer"


def test_backend_health_upstream_error_status_is_passed_through_with_200(client: TestClient, fake_backend: SimpleNamespace) -> None:  # BH-03
    fake_backend.response = SimpleNamespace(status=503, data=b'{"status":"DOWN"}')

    response = client.get("/api/backend-health", headers=auth_headers())

    assert response.status_code == 200
    assert response.json() == {"requestedBy": "student", "status": 503, "body": '{"status":"DOWN"}'}


def test_backend_health_empty_upstream_body_is_an_empty_string(client: TestClient, fake_backend: SimpleNamespace) -> None:  # BH-04
    fake_backend.response = SimpleNamespace(status=204, data=b"")
    assert client.get("/api/backend-health", headers=auth_headers()).json()["body"] == ""


@pytest.mark.parametrize(
    "error",
    [
        urllib3.exceptions.HTTPError("down"),
        urllib3.exceptions.MaxRetryError(None, "/q/health"),
        urllib3.exceptions.ReadTimeoutError(None, "/q/health", "timed out"),
    ],
    ids=["http-error", "max-retries", "timeout"],
)
def test_backend_health_unreachable_backend_is_200_with_status_zero(
    client: TestClient, fake_backend: SimpleNamespace, error: Exception
) -> None:  # BH-05
    fake_backend.error = error

    response = client.get("/api/backend-health", headers=auth_headers())

    assert response.status_code == 200
    assert response.json() == {"requestedBy": "student", "status": 0, "body": "Backend unavailable"}


def test_backend_health_non_utf8_body_is_reported_as_unavailable(client: TestClient, fake_backend: SimpleNamespace) -> None:  # BH-06
    fake_backend.response = SimpleNamespace(status=200, data=b"\xff\xfe")
    body = client.get("/api/backend-health", headers=auth_headers()).json()
    assert (body["status"], body["body"]) == (0, "Backend unavailable")


@pytest.mark.parametrize("headers", INVALID_TOKEN_HEADERS.values(), ids=INVALID_TOKEN_HEADERS.keys())
def test_backend_health_invalid_token_is_401_and_does_not_call_the_backend(
    client: TestClient, fake_backend: SimpleNamespace, headers: dict
) -> None:  # BH-07
    response = client.get("/api/backend-health", headers=headers)

    assert (response.status_code, response.json()) == (401, INVALID_TOKEN_BODY)
    assert fake_backend.calls == []
```
