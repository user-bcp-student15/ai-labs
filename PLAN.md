# Plan de remediación

## Alcance y prioridad

La planificación inicial seleccionó únicamente H-AUTH-05, entonces el único
hallazgo de auth con estado `Pendiente` en `HALLAZGOS.md`. El 2026-10-27 se
añadió H-API-01 como pendiente para revisión del plan; no se reabren ni
renumeran los hallazgos de auth. La ejecución posterior de H-AUTH-05 queda
registrada en su apartado y en la tabla de ejecuciones; los apartados
históricos de los demás IDs se conservan sin reabrirlos.

### Contrato actual y límites

- **Observado:** `docs/ENDPOINTS.md` documenta `POST /auth/login` con `200` y
  los campos `token`, `expiresIn`, `user` y `debug`; respuestas `400`, `401` y
  `500`; además de `403` y `415` cuyo cuerpo no está fijado. `GET /q/health`
  responde `200` con estado `UP`.
- **Acordado:** no hay un acuerdo externo de contrato registrado. Para este
  plan, el contrato observado es el límite de compatibilidad; H-AUTH-05 no
  propone cambios de endpoint, status ni forma JSON.
- **Riesgos pendientes:** los cuerpos de `403` y `415` y el comportamiento ante
  JSON malformado o vacío siguen abiertos. Tampoco se verificaron consumidores
  de tokens fuera de `auth/`; cualquier cambio de dependencia que afecte el
  token requiere comprobar las pruebas locales y coordinar esa integración.

### Historial del contrato anterior a las correcciones

Antes de las correcciones, el comportamiento observado en
`auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:22-59` era `400`
para request nulo o username/password ausente o vacío, `401` para credenciales
no válidas, `200` para login válido con `token`, `expiresIn`, `user` y `debug`,
y `500` con mensaje y clase de excepción. Las pruebas posteriores confirmaron
los status principales y la forma JSON de éxito. Se restringió CORS y el error
`500` pasó a ser genérico; el formato del token cambió a JWT firmado. No se
inspeccionaron consumidores fuera de `auth/`.

## H-AUTH-02 — Contraseñas almacenadas en texto plano

- **Hallazgo:** H-AUTH-02, ahora `Resuelto` en `HALLAZGOS.md`.
- **Problema:** `LegacyDatabase` crea la columna `password` como texto e inserta
  credenciales legibles (`auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java:23-25`).
- **Cambio propuesto:** almacenar hashes lentos con salt aleatorio y formato
  versionado; verificar el hash después de localizar el usuario. Migrar las filas
  existentes sin doble-hashearlas y mantener `401` para username o contraseña
  incorrectos. Evaluar primero la API criptográfica estándar de Java; cualquier
  dependencia nueva requiere justificación.
- **Archivos a tocar:** `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java`,
  `auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java` y una nueva
  clase de hash bajo `auth/src/main/java/com/bcp/workshop/auth/` con pruebas en
  `auth/src/test/java/com/bcp/workshop/auth/`.
- **Caracterización antes de tocar código:** ampliar las pruebas para comprobar
  login válido de las cuentas de prueba, contraseña incorrecta para un usuario
  existente y usuario desconocido; registrar el formato actual de la respuesta
  de login. Preparar una prueba de migración con una base SQLite temporal que
  compruebe login antes/después y que la migración sea idempotente.
- **Después del cambio:** comprobar que el valor persistido no sea la contraseña
  original, que las contraseñas válidas sigan autenticando y las inválidas
  sigan respondiendo `401`.
- **Resultado:** hash PBKDF2 con salt y migración idempotente de filas antiguas;
  pruebas de hashing, login y migración pasan.

## H-AUTH-03 — Token Base64 con secreto embebido

- **Hallazgo:** H-AUTH-03, ahora `Resuelto` en `HALLAZGOS.md`.
- **Problema:** `LegacyTokenUtil` concatena identidad, rol, expiración y secreto,
  y solo codifica el resultado en Base64
  (`auth/src/main/java/com/bcp/workshop/auth/LegacyTokenUtil.java:8,13-15`).
- **Cambio propuesto:** reemplazar el token casero por un token firmado con
  expiración y claims explícitos; cargar la clave desde configuración externa y
  fallar de forma segura si falta en producción. Elegir una biblioteca mantenida
  tras revisar compatibilidad y justificar cualquier dependencia nueva; no
  implementar criptografía propia. Mantener los campos `token`, `expiresIn` y
  `user` del JSON de éxito.
- **Archivos a tocar:** `auth/src/main/java/com/bcp/workshop/auth/LegacyTokenUtil.java`,
  `auth/src/main/java/com/bcp/workshop/auth/AuthResource.java`,
  `auth/src/main/resources/application.properties`, pruebas de token/login en
  `auth/src/test/java/com/bcp/workshop/auth/` y `auth/pom.xml` solo si la
  biblioteca elegida lo requiere.
- **Caracterización antes de tocar código:** ampliar el test de login válido
  para fijar status, nombres de campos, `expiresIn`, usuario, rol y presencia
  del token; conservar también los casos `400` y `401`. No fijar el token
  Base64 actual como contrato de formato.
- **Después del cambio:** probar firma válida, rechazo de token alterado,
  expiración y ausencia de secretos reales en respuestas o configuración
  versionada.
- **Resultado:** JWT HS256 con `sub`, rol, emisión y expiración; la clave se
  carga desde configuración y se comprueba con pruebas de firma y manipulación.
  La verificación de consumidores externos no forma parte de las pruebas de
  `auth/`.

## H-AUTH-08 — Cuentas demo con credenciales conocidas en producción

- **Hallazgo:** H-AUTH-08, ahora `Resuelto` en `HALLAZGOS.md`.
- **Problema:** `LegacyDatabase.initialize` crea siempre las cuentas `student`
  y `trainer` con contraseñas conocidas, incluso en producción
  (`auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java:22-25,41-53`).
  `trainer` recibe un JWT con rol TRAINER
  (`auth/src/main/java/com/bcp/workshop/auth/AuthService.java:20`), y el perfil
  de producción escucha en todas las interfaces
  (`auth/src/main/resources/application.properties:3`).
- **Cambio propuesto:** habilitar el seed de demostración en dev/test y
  deshabilitarlo en prod mediante configuración de perfil. La corrección no
  borrará ni cambiará cuentas que ya estén en una base existente; esa condición
  queda como riesgo operativo a revisar para cualquier base previamente
  desplegada.
- **Archivos a tocar:** `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java`,
  `auth/src/main/resources/application.properties` y
  `auth/src/test/java/com/bcp/workshop/auth/LegacyDatabaseTest.java`.
- **Caracterización antes de tocar código:** añadir y ejecutar una prueba con
  SQLite temporal que confirme el comportamiento actual de seed de ambas
  cuentas de demostración. Registrar el resultado antes del cambio.
- **Después del cambio:** probar que el modo de seed deshabilitado no crea
  ninguna de esas cuentas y que el modo dev/test conserva el comportamiento
  caracterizado. Ejecutar `mvn verify` y mantener la cobertura del código
  modificado por encima del 85%.
- **Resultado:** el perfil prod establece `auth.seed-demo-users=false` y la
  inicialización omite las cuentas de demostración; dev/test conserva el seed.
  La prueba de caracterización previa pasó con 2 pruebas; después, las pruebas
  del modo habilitado/deshabilitado y del perfil prod pasaron, y la suite final
  alcanzó 23 pruebas correctas. Las cuentas preexistentes no se borran
  automáticamente y requieren revisión operativa si una base ya fue desplegada.

## Item: H-AUTH-05 — Versiones candidatas a revisión SCA

- **Hallazgo de `HALLAZGOS.md`:** H-AUTH-05, tipo Sugerencia, severidad media y
  estado `Resuelto` tras completar el alcance local. El candidato inicial
  pedía revisar dependencias; no confirmaba por sí mismo que existiera una
  vulnerabilidad.
- **Evidencia de línea base:** antes del cambio, `auth/pom.xml` fijaba Quarkus
  3.27.4, SQLite JDBC 3.50.3.0, Commons Text 1.15.0 y Nimbus JOSE+JWT 10.10
  (`auth/pom.xml:13,45-56`). Commons Text se usa para escapar `displayName`
  (`auth/src/main/java/com/bcp/workshop/auth/LoginResponse.java:3,8-15`) y
  Nimbus firma el JWT
  (`auth/src/main/java/com/bcp/workshop/auth/LegacyTokenUtil.java:3-8,37-52`).
  `mvn dependency:tree` resolvió 223 artefactos JAR; la consulta OSV exacta por
  versión encontró 48 advisory IDs en 10 coordenadas de Quarkus, Jackson y
  Netty.
- **Evidencia posterior:** el BOM de Quarkus 3.27.6.1 resuelve
  `quarkus-vertx-http` 3.27.6.1, Jackson 2.21.7 y Netty 4.1.139.Final.
  `mvn verify` pasó; la consulta OSV final no encontró coincidencias entre 222
  artefactos JAR. El detalle por coordenada y las ejecuciones están en
  `docs/TESTING.md`.
- **Problema y riesgo:** sin revisar dependencias directas y transitivas no se
  conoce la presencia, aplicabilidad ni ruta de una alerta de seguridad. Una
  actualización sin evidencia también puede romper el escapado del nombre o
  la firma/claims del token.
- **Contrato observado:** según `docs/ENDPOINTS.md`, login devuelve `200` con
  `token`, `expiresIn`, `user` y `debug`, y los errores de aplicación conservan
  `400`, `401` y `500`; `403` y `415` se documentan sin cuerpo JSON acordado.
- **Contrato acordado:** no consta un acuerdo externo independiente. Para este
  cambio, preservar el contrato observado de endpoint y el formato JWT que
  prueban los tests; no cambiar rutas, status, campos ni cuerpos documentados.
- **Riesgos pendientes:** OWASP Dependency-Check no completó la actualización
  de NVD porque `NVD_API_KEY` no estaba configurada; su salida no representa un
  resultado limpio. CodeQL y Dependency Review remotos no se ejecutaron. No se
  inspeccionaron consumidores de tokens fuera de `auth/`; las respuestas de
  runtime `403`/`415` siguen sin cuerpo fijado.
- **Cambio planificado y ejecutado:** se capturó el árbol Maven y se revisaron
  las coordenadas/versiones resueltas con OSV. El candidato Quarkus 3.27.4.1
  corregía el advisory del componente HTTP, pero mantenía Jackson 2.21.2 y
  Netty 4.1.135.Final; no cubría todos los advisories encontrados. Se actualizó
  únicamente el BOM a Quarkus 3.27.6.1, que resolvió las versiones observadas
  como afectadas. No se silenciaron alertas ni se redujeron quality gates.
- **Archivos a tocar:** `auth/pom.xml` si el análisis justifica cambiar
  versiones; `auth/src/main/java/com/bcp/workshop/auth/LoginResponse.java` solo
  si se cambia o retira Commons Text;
  `auth/src/main/java/com/bcp/workshop/auth/LegacyTokenUtil.java` solo si una
  actualización de Nimbus requiere adaptar su API. Antes de tocar esas clases,
  escribir o completar
  `auth/src/test/java/com/bcp/workshop/auth/LoginResponseTest.java` para fijar
  que un `displayName` ficticio `A & <B>` se serializa como
  `A &amp; &lt;B&gt;`; conservar y, si hace falta, ampliar
  `auth/src/test/java/com/bcp/workshop/auth/LegacyTokenUtilTest.java` para
  firma, identidad, rol, expiración y rechazo de firma alterada. Mantener
  `auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java` como prueba
  de contrato HTTP. No se propone modificar `docs/ENDPOINTS.md`.
- **Caracterización antes de tocar dependencias/código:** se creó primero la
  prueba unitaria de `LoginResponse` con `displayName` ficticio `A & <B>` y
  expectativa `A &amp; &lt;B&gt;`. Antes de actualizar el POM, las pruebas
  dirigidas ejecutaron 21 casos y `mvn verify` ejecutó 33; ambas ejecuciones
  terminaron sin fallos, errores ni omisiones. La línea base OSV cubrió 223
  artefactos y encontró advisories; si Commons Text o Nimbus no estaban
  afectados, sus clases no debían cambiarse.
- **Verificación posterior realizada:** tras actualizar el BOM, las pruebas
  dirigidas ejecutaron 21 casos sin fallos; `mvn verify` ejecutó 33 casos sin
  fallos, errores ni omisiones. JaCoCo reportó 152/161 líneas (94.4%) en el
  bundle, 6/6 (100%) en `LoginResponse` y 18/20 (90%) en `LegacyTokenUtil`.
  El árbol final contiene 222 artefactos JAR y la consulta OSV final devolvió
  cero coincidencias. CodeQL y Dependency Review remotos no se reportan como
  ejecutados; Dependency-Check no concluyó por la actualización NVD.
- **Estado:** H-AUTH-05 queda `Resuelto` para la revisión SCA local y el cambio
  de versiones comprobado. El contrato HTTP y el formato de token no
  cambiaron; Commons Text, Nimbus y SQLite quedaron intactos.

## H-AUTH-04 — CORS acepta cualquier origen

- **Hallazgo:** H-AUTH-04, ahora `Resuelto` en `HALLAZGOS.md`.
- **Problema:** CORS está habilitado y `quarkus.http.cors.origins` permite
  cualquier origen (`auth/src/main/resources/application.properties:4-5`).
- **Cambio propuesto:** externalizar la lista de orígenes de producción mediante
  configuración de entorno y retirar el patrón permisivo. Desarrollo y pruebas
  usan `http://localhost:4200`; producción requiere `AUTH_CORS_ORIGINS`.
- **Archivos a tocar:** `auth/src/main/resources/application.properties` y
  pruebas de configuración/HTTP en `auth/src/test/java/com/bcp/workshop/auth/`.
- **Caracterización antes de tocar código:** capturar la respuesta CORS actual
  para orígenes de prueba y registrar el contrato de éxito/error de login. Antes
  de cambiar la política, confirmar qué orígenes locales y de despliegue deben
  permitirse.
- **Después del cambio:** verificar que un origen aprobado recibe los headers
  esperados y que un origen no aprobado no queda autorizado. La reducción de
  orígenes es un cambio de política intencional; no cambia el endpoint ni su JSON.
- **Resultado:** pruebas HTTP confirman el origen local permitido y el rechazo
  del origen no listado.

## H-AUTH-06 — La respuesta de error expone detalles internos

- **Hallazgo:** H-AUTH-06, ahora `Resuelto` en `HALLAZGOS.md`.
- **Problema:** el `catch` devuelve al cliente el mensaje y la clase de la
  excepción (`auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:54-58`).
- **Cambio propuesto:** responder con mensaje genérico y conservar el status
  `500`; escribir el detalle solo en el log del servidor con el logger del
  proyecto, sin suprimir ni silenciar la excepción.
- **Archivos a tocar:** `auth/src/main/java/com/bcp/workshop/auth/AuthResource.java`
  y `auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java` o una prueba
  unitaria bajo `auth/src/test/java/com/bcp/workshop/auth/`.
- **Caracterización antes de tocar código:** provocar una excepción controlada
  mediante un repositorio de prueba y comprobar status `500` y el body actual;
  guardar además las expectativas de `400`, `401` y `200`.
- **Después del cambio:** comprobar que el cliente recibe el error genérico, que
  no aparecen el mensaje/clase de excepción en el body y que el status se
  mantiene. La simplificación intencional del body conserva el status `500`;
  `docs/ENDPOINTS.md` registra el body genérico observado.
- **Resultado:** la respuesta `500` usa mensaje genérico y los detalles se
  registran en el log del servidor; las pruebas verifican el status y el body.

## H-AUTH-07 — Responsabilidades mezcladas en el recurso

- **Hallazgo:** H-AUTH-07, ahora `Resuelto` en `HALLAZGOS.md`.
- **Problema:** `AuthResource.login` valida, consulta persistencia, genera el
  token y arma la respuesta en un solo método
  (`auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:22-49`).
- **Cambio propuesto:** separar incrementalmente Resource (HTTP), Service
  (autenticación y reglas) y Repository (persistencia); mapear la respuesta a un
  DTO propio. Mantener métodos de responsabilidad única, reutilizar validaciones
  compartidas y sustituir valores mágicos por constantes con nombre.
- **Archivos a tocar:** `auth/src/main/java/com/bcp/workshop/auth/AuthResource.java`,
  `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java`, nuevas clases
  de servicio y DTO bajo `auth/src/main/java/com/bcp/workshop/auth/`, y pruebas
  bajo `auth/src/test/java/com/bcp/workshop/auth/`.
- **Caracterización antes de tocar código:** completar pruebas del flujo HTTP:
  request nulo, username/password ausente, credenciales inválidas y login válido
  con el response completo. El test actual cubre login válido, credenciales
  inválidas y username con comilla; no cubre todas esas respuestas.
- **Después del cambio:** ejecutar los mismos casos contra el Resource separado
  y comprobar que status, claves y valores observables del contrato se mantienen.
- **Resultado:** `AuthService` y `LoginResponse` separan la autenticación y el
  DTO; las pruebas de contrato HTTP pasan.

## Item: H-API-01 — Token de auth incompatible con el verificador de API

- **Hallazgo:** H-API-01, estado `Pendiente` en `HALLAZGOS.md`. El usuario
  confirmó en esta conversación la aprobación del issue, la spec y la
  arquitectura. Este plan queda pendiente de revisión humana antes de editar
  código.
- **Problema:** `auth` crea un JWT HS256 con `sub`, `role`, `iat` y `exp`
  (`auth/src/main/java/com/bcp/workshop/auth/LegacyTokenUtil.java:38-51`).
  `web` envía ese token como Bearer
  (`web/src/app/dashboard/dashboard.component.ts:43`), mientras que `api`
  espera un formato Base64 legado y no verifica firma
  (`api/app/main.py:14,17-26`). Esto impide la interoperabilidad del flujo y
  deja la identidad sin validación criptográfica.
- **Cambio propuesto:** hacer que el límite de autenticación de `api` valide
  el token firmado que emite `auth`, incluyendo firma, expiración e identidad
  verificada. Mantener el contrato existente de login y el encabezado Bearer.
  No conservar aceptación dual del formato legado sin una decisión explícita.
- **Archivos previstos:** `api/app/main.py`,
  `api/tests/test_api.py`, `api/requirements.txt` si la biblioteca aprobada lo
  requiere, `compose.yaml` para pasar configuración externa sin versionar
  secretos, y las secciones de API en `docs/ENDPOINTS.md` y `docs/TESTING.md`.
  No se prevén cambios de código en `auth/` ni `web/`.
- **Caracterización antes de tocar código:** añadir una prueba con un JWT
  firmado conforme al contrato actual de `auth` y enviarlo a `GET /api/tasks`.
  Ejecutar `python tools/lab.py test api` antes del cambio y registrar el
  resultado real de línea base. Conservar pruebas del status y la forma de
  respuesta de login y de la API.
- **Después del cambio:** probar aceptación del token válido emitido por auth
  y rechazo con `401` de tokens malformados, alterados y expirados. Verificar
  que las rutas que comparten la dependencia de identidad mantienen su
  comportamiento exitoso. Ejecutar `python tools/lab.py test auth`,
  `python tools/lab.py test api` y `python tools/lab.py test web`, además de
  una prueba integrada local con Compose y una clave de prueba externa.
  Registrar resultados y cobertura reales en `docs/TESTING.md`, sin reducir
  los quality gates.
- **Decisiones pendientes antes de implementar:** elegir y revisar la
  biblioteca JWT y su versión; confirmar el suministro seguro de
  `AUTH_TOKEN_SECRET` para ambos servicios; confirmar si hay consumidores del
  formato legado fuera de `web`; y acordar si se preserva el cuerpo actual de
  error `401`, que no está documentado como contrato.
- **Límites:** no cambiar claims, algoritmo, vigencia ni JSON de
  `POST /auth/login`; no incorporar cambios de autorización por `owner`,
  consultas SQL ni carga de archivos, que son hallazgos independientes.

## Estado y límites de verificación

- `docs/ENDPOINTS.md` existe y separa el contrato observado, la ausencia de
  acuerdo externo registrado y los riesgos pendientes de auth.
- H-AUTH-05 quedó resuelto con SCA local OSV sobre el árbol completo. OWASP
  Dependency-Check no completó NVD por falta de `NVD_API_KEY`; no se interpreta
  como resultado limpio.
- CodeQL y Dependency Review remotos no se ejecutaron en este recorrido local.
- No se inspeccionaron consumidores externos al componente `auth/`.

### Historial de aprobaciones humanas

- **Antes de implementar:** el plan exigía aprobación humana antes de editar
  código; al comprobarlo inicialmente, no había aprobación registrada y la
  implementación se detuvo.
- **Antes de reanudar:** el usuario aprobó H-AUTH-02 a H-AUTH-07 en esta
  conversación el 2026-10-26. Esto registra la aprobación expresada por el
  usuario, no una revisión independiente.
- **H-AUTH-08:** el usuario eligió corregir el hallazgo de cuentas demo en
  producción el 2026-10-26.
- **Después de implementar:** por solicitud del usuario, la aprobación dejó de
  ser un requisito activo del plan. Se conserva aquí únicamente este historial.
- **H-API-01, 2026-10-27:** el usuario confirmó la aprobación del issue, la
  spec y la arquitectura, y autorizó registrar el hallazgo y este plan. La
  revisión humana de este plan y la autorización para editar código siguen
  pendientes.

## Ejecuciones registradas

| Fecha | Componente | IDs | Comando / cwd | Resultado |
|---|---|---|---|---|
| 2026-10-26 | auth | H-AUTH-02, H-AUTH-03, H-AUTH-04, H-AUTH-05, H-AUTH-06, H-AUTH-07 | `mvn test` / `auth/` (línea base previa a la caracterización nueva) | 3 pruebas, 0 fallos, 0 errores, 0 omitidas |
| 2026-10-26 | auth | H-AUTH-02, H-AUTH-03, H-AUTH-04, H-AUTH-05, H-AUTH-06, H-AUTH-07 | `mvn test` / `auth/` (caracterización antes de modificar producción) | 8 pruebas, 0 fallos, 0 errores, 0 omitidas; incluye contrato de login, respuestas 400/401/500 y CORS permisivo actual |
| 2026-10-26 | auth | H-AUTH-02 | `mvn test` / `auth/` | 12 pruebas, 0 fallos, 1 error: el test JDBC aislado no registró el driver SQLite |
| 2026-10-26 | auth | H-AUTH-02 | `mvn '-Dtest=LegacyDatabaseTest,PasswordHasherTest' test` / `auth/` | 4 pruebas, 0 fallos, 0 errores, 0 omitidas; corrección del test para cargar explícitamente el driver |
| 2026-10-26 | auth | H-AUTH-02, H-AUTH-03, H-AUTH-04, H-AUTH-05, H-AUTH-06, H-AUTH-07 | `mvn test` / `auth/` | 12 pruebas, 0 fallos, 0 errores, 0 omitidas tras la migración de contraseñas |
| 2026-10-26 | auth | H-AUTH-02, H-AUTH-03, H-AUTH-04, H-AUTH-05, H-AUTH-06, H-AUTH-07 | `mvn verify` / `auth/` | 17 pruebas, 0 fallos, 0 errores, 0 omitidas; JaCoCo: 131/149 líneas (87.9%) en las clases de producción modificadas |
| 2026-10-26 | auth | H-AUTH-02, H-AUTH-03, H-AUTH-04, H-AUTH-05, H-AUTH-06, H-AUTH-07 | `mvn verify` / raíz `ai-labs/` | Falló: Maven no encontró POM en el directorio; repetido correctamente desde `auth/` |
| 2026-10-26 | auth | H-AUTH-02, H-AUTH-03, H-AUTH-04, H-AUTH-05, H-AUTH-06, H-AUTH-07 | `mvn verify` / `auth/` | 20 pruebas, 0 fallos, 0 errores, 0 omitidas; JaCoCo: 141/151 líneas (93.4%) en las clases de producción modificadas |
| 2026-10-26 | auth | H-AUTH-02, H-AUTH-03, H-AUTH-04, H-AUTH-05, H-AUTH-06, H-AUTH-07 | `git diff --check` / raíz `ai-labs/` | Correcto; sin errores de espacios en blanco tras normalizar finales de línea |
| 2026-10-26 | auth | H-AUTH-02, H-AUTH-03, H-AUTH-04, H-AUTH-05, H-AUTH-06, H-AUTH-07 | `mvn verify` / `auth/` (revalidación sin cambios de código) | 20 pruebas, 0 fallos, 0 errores, 0 omitidas; JaCoCo: 138/149 líneas (92.6%) en las clases de producción modificadas |
| 2026-10-26 | auth | H-AUTH-02, H-AUTH-03, H-AUTH-04, H-AUTH-05, H-AUTH-06, H-AUTH-07 | `git diff --check` / raíz `ai-labs/` | Correcto; sin errores de espacios en blanco |
| 2026-10-26 | auth | H-AUTH-02, H-AUTH-03, H-AUTH-04, H-AUTH-05, H-AUTH-06, H-AUTH-07 | `mvn clean verify` / `auth/` | Falló durante `clean`: no pudo borrar `auth/target/workshop-auth-backend-dev.jar` porque otro proceso lo tenía abierto; las pruebas no se ejecutaron |
| 2026-10-26 | auth | H-AUTH-08 | `mvn '-Dtest=LegacyDatabaseTest' test` / `auth/` (caracterización antes del cambio) | 2 pruebas, 0 fallos, 0 errores; confirma el seed de `student` y `trainer` en el modo actual |
| 2026-10-26 | auth | H-AUTH-08 | `mvn test` / `auth/` (primera ejecución tras el cambio) | 22 pruebas; 1 error por no registrar el driver SQLite en la nueva prueba de seed; se corrigió el test para cargarlo explícitamente |
| 2026-10-26 | auth | H-AUTH-08 | `mvn '-Dtest=LegacyDatabaseTest' test` / `auth/` (tras corregir el test) | 3 pruebas, 0 fallos, 0 errores |
| 2026-10-26 | auth | H-AUTH-08 | `mvn '-Dtest=LegacyDatabaseProductionProfileTest' test` / `auth/` | Dos intentos iniciales fallaron porque la prueba leía el campo de un proxy CDI; se cambió a comprobar la propiedad de configuración inyectada |
| 2026-10-26 | auth | H-AUTH-08 | `mvn '-Dtest=LegacyDatabaseProductionProfileTest' test` / `auth/` (prueba corregida) | 1 prueba, 0 fallos, 0 errores; perfil prod activa `auth.seed-demo-users=false` |
| 2026-10-26 | auth | H-AUTH-02, H-AUTH-03, H-AUTH-04, H-AUTH-05, H-AUTH-06, H-AUTH-07, H-AUTH-08 | `mvn verify` / `auth/` | 23 pruebas, 0 fallos, 0 errores, 0 omitidas; JaCoCo: 141/151 líneas (93.4%) en las clases de producción modificadas |
| 2026-10-26 | auth | H-AUTH-02, H-AUTH-03, H-AUTH-04, H-AUTH-05, H-AUTH-06, H-AUTH-07, H-AUTH-08 | `git diff --check` / raíz `ai-labs/` | Correcto; sin errores de espacios en blanco |
| 2026-10-26 | auth | H-AUTH-01, H-AUTH-02, H-AUTH-03, H-AUTH-04, H-AUTH-06 | `mvn '-Dtest=AuthResourceTest,HealthEndpointTest' test` / `auth/` (preliminar, antes de añadir la prueba HTTP de 500) | 18 pruebas, 0 fallos, 0 errores, 0 omitidas; 16 de login y 2 de health |
| 2026-10-26 | auth | H-AUTH-01, H-AUTH-02, H-AUTH-03, H-AUTH-04, H-AUTH-06, H-AUTH-08 | `mvn verify` / `auth/` (preliminar, antes de añadir la prueba HTTP de 500) | 31 pruebas, 0 fallos, 0 errores, 0 omitidas; JaCoCo: 146/156 líneas (93.6%) del bundle y `AuthResource` 18/18 (100%) |
| 2026-10-26 | auth | H-AUTH-01, H-AUTH-02, H-AUTH-03, H-AUTH-04, H-AUTH-06 | `mvn '-Dtest=AuthResourceTest,HealthEndpointTest' test` / `auth/` | 19 pruebas, 0 fallos, 0 errores, 0 omitidas; 17 de login y 2 de health |
| 2026-10-26 | auth | H-AUTH-01, H-AUTH-02, H-AUTH-03, H-AUTH-04, H-AUTH-06, H-AUTH-08 | `mvn verify` / `auth/` | 32 pruebas, 0 fallos, 0 errores, 0 omitidas; JaCoCo: 146/156 líneas (93.6%) del bundle y `AuthResource` 18/18 (100%) |
| 2026-10-26 | auth | H-AUTH-01, H-AUTH-02, H-AUTH-03, H-AUTH-04, H-AUTH-06, H-AUTH-08 | `git diff --check` / raíz `ai-labs/` | Sin errores de espacios en blanco en cambios seguidos; los documentos nuevos se revisaron además con búsqueda de espacios finales, sin coincidencias |
| 2026-10-26 | auth | H-AUTH-05 | `mvn '-Dtest=LoginResponseTest,LegacyTokenUtilTest,AuthResourceTest' test` / `auth/` (caracterización previa al cambio de BOM) | Código 0; 21 pruebas, 0 fallos, 0 errores, 0 omitidas |
| 2026-10-26 | auth | H-AUTH-05 | `mvn verify` / `auth/` (línea base antes del cambio de BOM) | Código 0; 33 pruebas, 0 fallos, 0 errores, 0 omitidas; JaCoCo generó el reporte |
| 2026-10-26 | auth | H-AUTH-05 | `mvn dependency:tree -DoutputFile=target\auth-dependency-tree.txt -DoutputType=text` / `auth/` | Código 0; árbol de línea base capturado, 223 coordenadas Maven JAR para SCA |
| 2026-10-26 | auth | H-AUTH-05 | `mvn org.owasp:dependency-check-maven:13.0.0:check -Dformat=JSON` / `auth/` | Código 1; la actualización NVD falló porque `NVD_API_KEY` no estaba configurada; no se produjo un análisis completo |
| 2026-10-26 | auth | H-AUTH-05 | `python -` con `urllib.request` y OSV API `v1/querybatch` / raíz `ai-labs/` | Código 0; consulta de línea base de 223 coordenadas, 48 advisory IDs en 10 coordenadas |
| 2026-10-26 | auth | H-AUTH-05 | `python -` para presentar detalles de `/v1/vulns/{id}` / raíz `ai-labs/` | Código 1 por `UnicodeEncodeError` en la consola; se repitió escapando la salida a ASCII y se recuperaron los 48 detalles |
| 2026-10-26 | auth | H-AUTH-05 | `python -` con `urllib.request` y `/v1/vulns/{id}` (salida escapada a ASCII) / raíz `ai-labs/` | Código 0; detalles de los 48 advisory IDs recuperados |
| 2026-10-26 | auth | H-AUTH-05 | `mvn "-Dquarkus.platform.version=3.27.4.1" dependency:tree -DoutputFile=target\auth-dependency-tree-3.27.4.1.txt -DoutputType=text` / `auth/` | Código 0; candidato descartado: mantenía Jackson 2.21.2 y Netty 4.1.135.Final |
| 2026-10-26 | auth | H-AUTH-05 | `mvn "-Dquarkus.platform.version=3.27.6.1" dependency:tree -DoutputFile=target\auth-dependency-tree-3.27.6.1.txt -DoutputType=text` / `auth/` | Código 0; resolvió Jackson 2.21.7, Netty 4.1.139.Final y `quarkus-vertx-http` 3.27.6.1 |
| 2026-10-26 | auth | H-AUTH-05 | `python -` con consulta OSV del árbol candidato desde la raíz `ai-labs/` | Código 1 por `FileNotFoundError`: se buscó `target/` en el directorio incorrecto; se repitió desde `auth/` |
| 2026-10-26 | auth | H-AUTH-05 | `python -` con `urllib.request` y OSV API `v1/querybatch` / `auth/` (árbol candidato 3.27.6.1) | Código 0; 222 coordenadas, 0 coincidencias |
| 2026-10-26 | auth | H-AUTH-05 | `mvn '-Dtest=LoginResponseTest,LegacyTokenUtilTest,AuthResourceTest' test` / `auth/` (después del cambio de BOM) | Código 0; 21 pruebas, 0 fallos, 0 errores, 0 omitidas |
| 2026-10-26 | auth | H-AUTH-05 | `mvn verify` / `auth/` (después del cambio de BOM) | Código 0; 33 pruebas, 0 fallos, 0 errores, 0 omitidas; JaCoCo: 152/161 líneas (94.4%) en el bundle, `LoginResponse` 6/6 (100%) |
| 2026-10-26 | auth | H-AUTH-05 | `mvn dependency:tree -DoutputFile=target\auth-dependency-tree-final.txt -DoutputType=text` / `auth/` | Código 0; árbol final capturado, 222 coordenadas Maven JAR |
| 2026-10-26 | auth | H-AUTH-05 | `python -` con `urllib.request` y OSV API `v1/querybatch` / `auth/` (árbol final) | Código 0; 222 coordenadas, 0 coincidencias y 0 advisory IDs |
