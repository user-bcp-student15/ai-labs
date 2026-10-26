# Hallazgos

## Seguimiento — auth

Estados actualizados tras implementar y verificar las correcciones de auth.
El candidato SQL conserva el ID H-AUTH-01 previamente usado en el historial
de esta conversación.

| id | componente | hallazgo | tipo | explicacion | evidencia (archivo:linea) | severidad | estado |
|---|---|---|---|---|---|---|---|
| H-AUTH-01 | auth | Concatenación de credenciales en SQL de login | Vulnerabilidad | El candidato histórico no aparece en el código actual: la consulta usa marcadores y enlaza los valores mediante `PreparedStatement`. Se registra como no encontrado en esta lectura, no como resuelto ni aprobado. | `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java:60-65` | alta | No encontrado |
| H-AUTH-02 | auth | Contraseña almacenada en texto plano | Vulnerabilidad | Resuelto: las contraseñas se almacenan con PBKDF2 y salt; las filas preexistentes se migran de forma idempotente. | `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java:60-69,98-116`; `auth/src/main/java/com/bcp/workshop/auth/PasswordHasher.java:23-60` | alta | Resuelto |
| H-AUTH-03 | auth | Token codificado en Base64 con secreto embebido y sin firma | Vulnerabilidad | Resuelto: el token ahora es JWT HS256 con claims y expiración, y la clave de firma procede de configuración externa. | `auth/src/main/java/com/bcp/workshop/auth/LegacyTokenUtil.java:23-52`; `auth/src/main/resources/application.properties:10-12` | alta | Resuelto |
| H-AUTH-08 | auth | Cuentas demo con credenciales conocidas creadas también en producción | Vulnerabilidad | Resuelto: el seed de demostración se habilita en dev/test y queda deshabilitado en prod. No se eliminan cuentas demo que ya existan en una base desplegada; esa condición requiere revisión operativa. | `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java:34-35,61-64`; `auth/src/main/resources/application.properties:10-11`; `auth/src/test/java/com/bcp/workshop/auth/LegacyDatabaseTest.java:26-55`; `auth/src/test/java/com/bcp/workshop/auth/LegacyDatabaseProductionProfileTest.java:22-23` | alta | Resuelto |
| H-AUTH-04 | auth | CORS permite cualquier origen | Vulnerabilidad | Resuelto: se permite el origen local configurado y producción requiere `AUTH_CORS_ORIGINS`; se probaron origen permitido y origen no permitido. | `auth/src/main/resources/application.properties:4-8` | media | Resuelto |
| H-AUTH-05 | auth | Versiones de dependencias candidatas a revisión SCA | Sugerencia | Resuelto: el análisis OSV de línea base encontró advisories en Quarkus 3.27.4, Jackson 2.21.2 y Netty 4.1.133.Final; se actualizó el BOM a Quarkus 3.27.6.1. El árbol final no tuvo coincidencias OSV; Dependency-Check y los controles remotos no se reportan como ejecutados. | `auth/pom.xml:13`; `auth/src/test/java/com/bcp/workshop/auth/LoginResponseTest.java:8-15` | media | Resuelto |
| H-AUTH-06 | auth | Respuesta de error expone detalles de excepción | Vulnerabilidad | Resuelto: el cliente recibe un mensaje genérico y el detalle se conserva solo en el log del servidor. | `auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:23,50-52` | media | Resuelto |
| H-AUTH-07 | auth | Recurso mezcla validación, persistencia, token y respuesta HTTP | Refactor | Resuelto: el recurso gestiona HTTP y validación, `AuthService` coordina autenticación y `LoginResponse` compone el DTO de éxito. | `auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:30-45`; `auth/src/main/java/com/bcp/workshop/auth/AuthService.java:14-21`; `auth/src/main/java/com/bcp/workshop/auth/LoginResponse.java:5-16` | baja | Resuelto |

### Evidencia de pruebas y pendientes

- `mvn verify` con cwd `auth/`: 23 pruebas, 0 fallos, 0 errores y 0 omitidas.
  JaCoCo registró 141/151 líneas (93.4%) en las clases de producción
  modificadas.
- Una ejecución posterior de `mvn clean verify` no llegó a las pruebas: Maven
  no pudo borrar `auth/target/workshop-auth-backend-dev.jar` porque otro proceso
  lo tenía abierto. Una ejecución posterior de `mvn verify` sí terminó
  correctamente.
- `git diff --check`: sin errores de espacios en blanco.
- H-AUTH-05 se resolvió con una consulta OSV local de las dependencias Maven
  resueltas. OWASP Dependency-Check no concluyó por falta de `NVD_API_KEY`, y
  CodeQL/Dependency Review remotos no se ejecutaron ni se reportan como
  aprobados.
- H-AUTH-01 continúa como `No encontrado`: la consulta de login usa
  `PreparedStatement` y enlaza el username, según
  `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java:60-65`.
- Revalidación de endpoints auth el 2026-10-26: `mvn verify` con cwd `auth/`
  ejecutó 32 pruebas, 0 fallos, 0 errores y 0 omitidas. El reporte JaCoCo del
  bundle completo registró 146/156 líneas (93.6%) y `AuthResource` 18/18
  (100%); esta métrica del bundle no reemplaza la medición filtrada del renglón
  anterior. Los casos y el método de medición están en `docs/TESTING.md`.
- H-AUTH-05: antes del cambio, la consulta OSV sobre 223 artefactos Maven
  detectó 48 advisory IDs en 10 coordenadas. Después de actualizar el BOM,
  `mvn verify` pasó con 33 pruebas y 0 fallos, y la consulta OSV final no
  encontró coincidencias en 222 artefactos. JaCoCo midió 152/161 líneas
  (94.4%) en el bundle y 6/6 (100%) en `LoginResponse`. OWASP
  Dependency-Check no pudo completar la descarga de NVD por falta de
  `NVD_API_KEY`; CodeQL y Dependency Review remotos no se ejecutaron. Véase
  `PLAN.md` y `docs/TESTING.md`.
