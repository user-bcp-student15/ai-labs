# Spec Delta

## Purpose

Define cómo las rutas protegidas de la API autentican la identidad presentada mediante el JWT que emite auth. La API solo acepta identidades cuya firma y vigencia hayan sido verificadas.

## ADDED Requirements

### Requirement: API autentica el JWT emitido por auth
La API MUST aceptar un JWT que cumpla el contrato actual de `POST /auth/login` solo después de verificar su firma y vigencia. La identidad autenticada MUST proceder de los claims `sub` y `role` del token verificado.

#### Scenario: JWT válido permite listar tareas
- **WHEN** una solicitud a `GET /api/tasks` presenta en `Authorization: Bearer` un JWT vigente y correctamente firmado conforme al contrato actual de auth
- **THEN** la API responde `200 OK` con la forma de respuesta exitosa actual
- **AND** cuando no se especifica `owner`, la identidad usada para listar tareas corresponde al claim `sub` verificado

### Requirement: API rechaza tokens sin identidad verificable
La API MUST responder `401 Unauthorized` y no conceder acceso a una ruta protegida si la credencial está ausente, no es un JWT válido, tiene una firma incorrecta, fue alterada o está expirada. El formato legado Base64 MUST rechazarse porque no verifica criptográficamente la identidad.

#### Scenario: Credencial ausente
- **WHEN** una solicitud a una ruta protegida no incluye una credencial Bearer
- **THEN** la API responde `401 Unauthorized`

#### Scenario: Token malformado o con firma incorrecta
- **WHEN** una solicitud a una ruta protegida presenta un token malformado o firmado con una clave distinta
- **THEN** la API responde `401 Unauthorized`
- **AND** no usa la identidad incluida en la credencial

#### Scenario: Token alterado o expirado
- **WHEN** una solicitud a una ruta protegida presenta un JWT cuya firma ya no corresponde a su contenido o cuya vigencia terminó
- **THEN** la API responde `401 Unauthorized`
- **AND** no usa la identidad incluida en la credencial

#### Scenario: Token del formato legado
- **WHEN** una solicitud a una ruta protegida presenta una credencial del formato legado Base64
- **THEN** la API responde `401 Unauthorized`
- **AND** no usa la identidad incluida en la credencial

### Requirement: API conserva el contrato de error 401
La API MUST conservar el status y la forma JSON del cuerpo 401 observados actualmente para credenciales rechazadas. El valor específico del detalle puede depender de la causa del rechazo.

#### Scenario: Cuerpo de error de una credencial rechazada
- **WHEN** una credencial es rechazada en una ruta protegida
- **THEN** la respuesta tiene status `401 Unauthorized`
- **AND** conserva el objeto JSON actual con el campo `detail` y el prefijo de mensaje `Invalid token: `

### Requirement: Las rutas protegidas conservan sus respuestas exitosas
Cuando una solicitud presenta un JWT válido, las rutas protegidas existentes MUST conservar el status y la forma de sus respuestas exitosas actuales.

#### Scenario: Creación de tarea autenticada
- **WHEN** se crea una tarea en `POST /api/tasks` con un JWT válido
- **THEN** la API conserva el status `201 Created` y la forma de respuesta exitosa actual

#### Scenario: Resumen autenticado
- **WHEN** se solicita `GET /api/summary` con un JWT válido
- **THEN** la API conserva el status `200 OK` y la forma de respuesta exitosa actual

#### Scenario: Carga de requisito autenticada
- **WHEN** se carga un archivo mediante `POST /api/requirements` con un JWT válido
- **THEN** la API conserva el status `201 Created` y la forma de respuesta exitosa actual

#### Scenario: Consulta de salud autenticada
- **WHEN** se solicita `GET /api/backend-health` con un JWT válido
- **THEN** la API conserva el status y la forma de respuesta exitosa actuales

### Requirement: La clave de validación no es un secreto del repositorio
La clave usada para verificar la firma MUST proporcionarse externamente al código versionado. Las pruebas MUST usar una clave ficticia y no incorporar secretos reales.

#### Scenario: Validación y pruebas sin secretos versionados
- **WHEN** la API valida un JWT en un entorno de prueba
- **THEN** la firma se verifica con una clave ficticia suministrada al entorno
- **AND** el repositorio no contiene la clave como secreto incorporado

### Requirement: El contrato de emisión de auth permanece sin cambios
La integración de autenticación de la API MUST preservar el contrato documentado de `POST /auth/login` en `docs/ENDPOINTS.md`.

#### Scenario: Login conserva el JWT documentado
- **WHEN** se autentican credenciales válidas mediante `POST /auth/login`
- **THEN** auth conserva el status `200 OK` y la respuesta JSON con `token`, `expiresIn`, `user` y `debug`
- **AND** el token conserva HS256, los claims `sub`, `role`, `iat` y `exp`, y la vigencia actual de 3600 segundos
