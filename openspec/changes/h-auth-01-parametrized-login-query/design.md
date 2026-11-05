# Design

## Context

Motivación y alcance: ver [proposal.md](./proposal.md) (Issue #23, H-AUTH-01). Requisitos: ver [specs/auth-login/spec.md](./specs/auth-login/spec.md).

Estado actual en `auth/` (Quarkus, SQLite vía `sqlite-jdbc`, JaCoCo configurado en `pom.xml`):

- `AuthResource.login` valida el cuerpo (400), llama a `LegacyDatabase.findByCredentials(username, password)`, responde 401 si devuelve `null` o arma el 200 con `token`, `expiresIn`, `user` y `debug`. Cualquier excepción se traduce en 500.
- `LegacyDatabase.findByCredentials` concatena ambos valores en el SQL y usa `Statement` (vulnerabilidad). Abre su propia conexión con `DriverManager` y `AUTH_DB_URL`; ante una excepción de SQL imprime la traza y devuelve `null`, lo que `AuthResource` convierte en 401.
- La tabla `legacy_users` guarda `username` (UNIQUE) y `password` en texto plano; `initialize()` siembra `student` y `trainer`.
- `AuthResourceTest` solo cubre el login válido de `student`. Usa la base `./data/workshop.db` real, no una aislada.
- `docs/ENDPOINTS.md` no documenta `/auth/login`; el baseline es el Issue y el comportamiento actual observado.

## Goals / Non-Goals

**Goals:**

- Que `username` y `password` lleguen a la base solo como parámetros enlazados, nunca como parte del texto SQL.
- Cambio mínimo y localizable en un único método, revisable por separado de las pruebas.
- Dejar el contrato HTTP de `POST /auth/login` idéntico, verificado con pruebas antes y después.

**Non-Goals:**

- Hashing o migración de contraseñas, firma/expiración del token, eliminación del campo `debug`, o dejar de reflejar el usuario en el mensaje 401 (hallazgos aparte).
- Refactor en capas de `AuthResource` (regla de clean code del componente): se hará en otro cambio; mezclarlo ocultaría el diff de seguridad.
- Cambiar `initialize()`, el esquema, la URL de la base o el manejo de excepciones (500 / `printStackTrace`).
- Introducir un ORM, pool de conexiones o dependencias nuevas.

## Contratos protegidos

| Contrato | Valor que debe conservarse |
|---|---|
| `POST /auth/login` válido (`student` / `Workshop123!`) | 200; `token`, `expiresIn` (3600), `user.username`, `user.displayName`, `user.role`, `debug` |
| Cuerpo ausente / `username` o `password` vacíos o en blanco | 400 con `message` |
| Credenciales desconocidas o incorrectas | 401 con `message` y sin `token` |
| Firma pública de `LegacyDatabase.findByCredentials(String, String)` → `UserRecord` o `null` | Sin cambios; `AuthResource` no se modifica |
| Formato del token (`LegacyTokenUtil`), esquema de `legacy_users`, `AUTH_DB_URL` | Sin cambios |

Cambio de comportamiento permitido (único): entradas con sintaxis SQL que hoy autentican pasan a responder 401.

## Componentes afectados

- Modifica: `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java` (solo el cuerpo de `findByCredentials`).
- Modifica: `auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java` (nuevas pruebas).
- No se tocan: `AuthResource`, `LegacyTokenUtil`, `LoginRequest`, `UserRecord`, `pom.xml`, `api/`, `web/`, ni los documentos generales de otros componentes.

## Decisions

### D1. `PreparedStatement` con parámetros enlazados en `findByCredentials`

SQL constante `... WHERE username = ? AND password = ?`, con `setString(1, username)` y `setString(2, password)`. Es lo que exige el Issue y la corrección estándar para este tipo de inyección: el driver envía los valores como datos, por lo que `'`, `--` o `OR` pierden significado sintáctico.

Alternativas descartadas:

- *Escapar comillas manualmente*: frágil, depende del dialecto y se olvida fácil; no cumple el criterio del Issue.
- *Lista de caracteres prohibidos / validación de entrada en `AuthResource`*: rechazaría contraseñas legítimas con símbolos y no elimina la causa.
- *Leer el usuario por `username` y comparar la contraseña en Java*: también evita la inyección, pero cambia la semántica de acceso a datos y anticipa el rediseño de contraseñas (non-goal); además el Issue pide parametrizar ambos valores.
- *ORM / JPA (Panache)*: dependencia y cambio arquitectónico desproporcionados.

### D2. Mantener el manejo de errores y la firma existentes

Se conserva `try-with-resources`, la conexión por `DriverManager` y el retorno `null` ante "no encontrado" o error. Así no cambia ningún código HTTP existente y el diff queda en pocas líneas. El `PreparedStatement` y el `ResultSet` se declaran en el mismo `try-with-resources` para evitar fugas de recursos.

### D3. Pruebas a nivel HTTP con `@QuarkusTest`

Se amplía `AuthResourceTest` (ya exigido por el Issue) con RestAssured, que ejercita el flujo completo. No se agrega prueba unitaria aislada de `LegacyDatabase` salvo que la cobertura del código modificado (meta ≥ 85 %, JaCoCo) lo requiera.

## Estrategia incremental

Cada paso es un commit revisable, en la rama `feature/hu-auth-01`:

1. **Caracterización (sin tocar código de producción)**: añadir pruebas que fijan el comportamiento actual que debe preservarse (ver sección siguiente). Deben pasar sobre el código vulnerable actual.
2. **Prueba de inyección en rojo**: añadir las pruebas de inyección (usuario, usuario con comentario SQL, contraseña, ambos) y confirmar que fallan exactamente tres contra el código actual (devuelven 200): usuario con comentario SQL, contraseña y ambos. La de usuario simple pasa y queda como regresión. Esto demuestra que las pruebas detectan la vulnerabilidad.
3. **Corrección**: cambiar `findByCredentials` a `PreparedStatement` (D1). Las pruebas de inyección pasan a verde y las de caracterización siguen en verde.
4. **Verificación**: `mvn test` desde `auth/`, revisión del informe JaCoCo del código modificado (≥ 85 %), y comprobar que no queda concatenación de `username` o `password` en SQL.

## Pruebas de caracterización necesarias (antes de modificar)

Hoy solo existe el caso de login válido. Antes del cambio se necesitan, en `AuthResourceTest`:

| Prueba | Entrada | Resultado esperado hoy y después |
|---|---|---|
| Login válido, forma completa | `student` / `Workshop123!` | 200; `token` no nulo, `expiresIn`, `user.username`, `user.displayName`, `user.role` |
| Contraseña incorrecta | `student` / contraseña errónea | 401 con `message`, sin `token` |
| Usuario inexistente | usuario desconocido / cualquier contraseña | 401 con `message`, sin `token` |
| Cuerpo con campos vacíos o en blanco | `username` o `password` vacío / `"   "` | 400 con `message` |
| Contraseña con comillas o símbolos legítimos pero incorrecta (p. ej. `it's`) | `student` / `it's` | 401 (hoy puede producir un error de SQL tratado como 401; debe seguir siendo 401 y no 500) |

Pruebas nuevas de inyección, todas con 401 y sin `token`:

- Rojas antes (200 con el código vulnerable), verdes después: `' OR '1'='1` en contraseña, `' OR '1'='1` en ambos campos y `' OR '1'='1' --` en usuario con una contraseña cualquiera.
- Verde antes y después (regresión): `' OR '1'='1` en usuario con una contraseña cualquiera. Hoy ya responde 401 porque `AND` precede a `OR`: `username='' OR ('1'='1' AND password='x')` es falso. La prueba no detecta la vulnerabilidad por sí sola; el comentario `--` anula la condición de contraseña y sí la explota.

Nota: el caso de la comilla simple debe verificarse empíricamente antes del cambio para registrar el comportamiento real; si hoy devolviera 500, se documenta y no se considera contrato.

## Risks / Trade-offs

- [Regresión en el login válido] → las pruebas de caracterización corren antes y después; el cambio se limita a un método.
- [Las pruebas usan la base real `./data/workshop.db`, compartida y con estado] → solo hacen lecturas con `student`; no se escriben datos nuevos. Aislar la base de pruebas queda fuera de este cambio.
- [Fallo silencioso: el error de SQL se traga y se devuelve `null`, enmascarando problemas con la consulta parametrizada] → la prueba de login válido (200) detecta cualquier error de sintaxis o de enlace de parámetros.
- [La vulnerabilidad se corrige solo en este punto; las contraseñas siguen en texto plano y el 401 refleja el usuario] → se declara como non-goal y se deja como hallazgos separados para no ampliar el alcance.
- [Cobertura del código modificado] → el método cambiado queda cubierto por los casos de éxito y rechazo; se confirma con JaCoCo.

## Migration Plan / Rollback

No hay migración de datos ni de esquema; no cambia configuración ni contrato. El despliegue es el de `auth/` habitual.

Rollback: revertir el commit de la corrección (paso 3) con `git revert`; el contrato HTTP no cambia, así que ningún consumidor (`api/`, `web/`) se ve afectado. Revertirlo restaura la vulnerabilidad, por lo que solo debe hacerse ante una regresión funcional comprobada y con un nuevo intento de corrección priorizado. Las pruebas de caracterización pueden permanecer.
