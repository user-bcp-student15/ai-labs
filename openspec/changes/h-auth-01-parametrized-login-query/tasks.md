## 1. Caracterización (sin cambiar código de producción)

- [x] 1.1 Ejecutar `mvn test` desde `auth/` y registrar la línea base: la prueba existente pasa y el estado inicial de JaCoCo
- [x] 1.2 Antes de escribir pruebas, comprobar manualmente contra el código actual el resultado (401 o 500) de `student` con la contraseña `it's` y anotarlo en el mensaje del commit; si es 500, no se prueba como contrato
- [x] 1.3 En `AuthResourceTest`, ampliar la prueba de login válido para verificar `token`, `expiresIn`, `user.username`, `user.displayName` y `user.role`; verificar que pasa sobre el código actual
- [x] 1.4 Añadir prueba de contraseña incorrecta de `student`: 401 con `message` y sin `token`; verificar que pasa sobre el código actual
- [x] 1.5 Añadir prueba de usuario inexistente: 401 con `message` y sin `token`; verificar que pasa sobre el código actual
- [x] 1.6 Añadir pruebas de `username` o `password` vacíos o en blanco: 400 con `message`; verificar que pasan sobre el código actual
- [x] 1.7 Si en 1.2 el resultado fue 401, añadir la prueba de `student` con `it's` esperando 401; verificar que pasa sobre el código actual
- [x] 1.8 Ejecutar `mvn test` desde `auth/` y confirmar que toda la caracterización está en verde antes de continuar; commit solo de pruebas

## 2. Pruebas de inyección en rojo

- [x] 2.1 Añadir en `AuthResourceTest` las pruebas de `username` con contraseña cualquiera, ambas con 401 y sin `token`: `' OR '1'='1` (regresión; hoy ya responde 401) y `' OR '1'='1' --` (en rojo)
- [x] 2.2 Añadir la prueba con `student` y `' OR '1'='1` como `password`: 401 y sin `token`
- [x] 2.3 Añadir la prueba con `' OR '1'='1` en ambos campos: 401 y sin `token`
- [x] 2.4 Ejecutar `mvn test` desde `auth/` y confirmar que fallan exactamente las 3 pruebas en rojo (`username` con `' OR '1'='1' --`, `password` y ambos campos; devuelven 200 con el código vulnerable) y que la de `username` con `' OR '1'='1'` pasa; commit solo de estas pruebas

## 3. Corrección

- [x] 3.1 En `LegacyDatabase.findByCredentials`, reemplazar la concatenación por SQL constante con `username = ? AND password = ?` y `PreparedStatement` con `setString` para ambos valores, manteniendo firma, `try-with-resources`, retorno `null` y mapeo a `UserRecord`
- [x] 3.2 Ejecutar `mvn test` desde `auth/` y confirmar que las pruebas de inyección pasan y la caracterización sigue en verde; commit solo del cambio funcional

## 4. Verificación final

- [x] 4.1 Confirmar con una búsqueda en `auth/src/main` que `username` y `password` no se concatenan en ningún SQL y que no se modificó `AuthResource`, `pom.xml`, `api/` ni `web/` (`git diff --stat`)
- [x] 4.2 Revisar el informe JaCoCo de `auth/` y confirmar cobertura de 85 % o más en el código modificado
- [x] 4.3 Ejecutar `openspec validate h-auth-01-parametrized-login-query` y comprobar que cada escenario de `specs/auth-login/spec.md` tiene una prueba asociada
- [x] 4.4 Verificar los cuatro criterios de aceptación del Issue #23 y registrar la evidencia (comandos y resultados) en la raíz como H-AUTH-01, conservando las secciones existentes
