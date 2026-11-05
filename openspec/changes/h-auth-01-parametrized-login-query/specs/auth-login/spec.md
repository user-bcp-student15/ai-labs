## ADDED Requirements

### Requirement: Credenciales tratadas como datos
El sistema SHALL verificar `username` y `password` de `POST /auth/login` como valores literales, sin que su contenido pueda alterar la lógica de la consulta de credenciales.

#### Scenario: Inyección en el usuario
- **WHEN** se envía `POST /auth/login` con `username` `' OR '1'='1` y una contraseña cualquiera
- **THEN** la respuesta es 401 y el cuerpo no contiene `token`

#### Scenario: Inyección en el usuario con comentario SQL
- **WHEN** se envía `POST /auth/login` con `username` `' OR '1'='1' --` y una contraseña cualquiera
- **THEN** la respuesta es 401 y el cuerpo no contiene `token`

#### Scenario: Inyección en la contraseña
- **WHEN** se envía `POST /auth/login` con `username` `student` y `password` `' OR '1'='1`
- **THEN** la respuesta es 401 y el cuerpo no contiene `token`

#### Scenario: Inyección en ambos campos
- **WHEN** se envía `POST /auth/login` con `' OR '1'='1` como `username` y como `password`
- **THEN** la respuesta es 401 y el cuerpo no contiene `token`

### Requirement: Login válido conservado
El sistema SHALL seguir autenticando credenciales válidas con el contrato vigente de `POST /auth/login`.

#### Scenario: Credenciales válidas
- **WHEN** se envía `POST /auth/login` con `username` `student` y `password` `Workshop123!`
- **THEN** la respuesta es 200 con `token`, `expiresIn` y `user.username` igual a `student`

### Requirement: Rechazos existentes conservados
El sistema SHALL mantener los códigos de rechazo vigentes de `POST /auth/login`.

#### Scenario: Credenciales incorrectas
- **WHEN** se envía `POST /auth/login` con `username` `student` y una contraseña incorrecta
- **THEN** la respuesta es 401 con `message` y sin `token`

#### Scenario: Campos vacíos
- **WHEN** se envía `POST /auth/login` con `username` o `password` vacío o en blanco
- **THEN** la respuesta es 400 con `message`

### Requirement: Prueba de regresión de inyección
La suite de `auth/` SHALL incluir en `AuthResourceTest` una prueba del intento de inyección, y `mvn test` ejecutado desde `auth/` SHALL pasar.

#### Scenario: Suite verde con prueba de inyección
- **WHEN** se ejecuta `mvn test` desde `auth/`
- **THEN** la prueba de inyección de `AuthResourceTest` se ejecuta y todas las pruebas pasan
