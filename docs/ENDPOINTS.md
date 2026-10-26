# Contrato HTTP — auth

## Alcance y estado del contrato

- **Contrato observado:** lo descrito abajo se deriva del código actual de
  `auth/` y de las pruebas citadas.
- **Contrato acordado:** no se encontró un acuerdo de contrato externo
  registrado. Esta documentación refleja el comportamiento observado; no afirma
  compatibilidad ya verificada con consumidores fuera de `auth/`.
- **Riesgos y preguntas abiertas:** los cuerpos de error generados por Quarkus
  (por ejemplo, rechazos CORS o de tipo de contenido) no están fijados por el
  código de `auth/src/main/java/com/bcp/workshop/auth/AuthResource.java` ni
  comprobados por las pruebas actuales. La respuesta UP de salud ya tiene una
  prueba de integración; el estado no saludable sigue sin contrato ni prueba.
  Se señalan en cada endpoint los detalles que requieren comprobación en
  runtime.

La aplicación escucha localmente en `http://localhost:8080`
(`auth/src/main/resources/application.properties:1`; `README.md:44`).

## GET /q/health

### 1. Propósito de negocio

Permite comprobar si el servicio de autenticación está disponible para atender
solicitudes.

### 2. Autenticación

No requiere autenticación ni un header `Authorization`; es un endpoint de salud
proporcionado por `quarkus-smallrye-health`
(`auth/pom.xml:40`). No hay un recurso de salud personalizado en el código de
`auth/`.

### 3. Request

| campo | tipo | obligatorio | descripción |
|---|---|---|---|
| — | — | No | La solicitud GET no tiene campos de query ni cuerpo JSON. |

Ejemplo HTTP completo (sin cuerpo; no existe un JSON de request para este GET):

```http
GET /q/health HTTP/1.1
Host: localhost:8080
Accept: application/json
```

### 4. Response exitosa

- **Código:** `200 OK`, cuando el estado de salud es `UP`.
- **Content-Type:** `application/json`.

La extensión SmallRye Health proporciona los campos `status` y `checks`. No hay
checks de salud personalizados registrados en `auth/`; el ejemplo representa
el estado sin checks.

| campo | tipo | descripción |
|---|---|---|
| `status` | string | Estado agregado del servicio; el ejemplo sin checks es `UP`. |
| `checks` | array de objetos | Checks registrados por la aplicación; vacío en el código actual. |

Ejemplo JSON de respuesta:

```json
{
  "status": "UP",
  "checks": []
}
```

Evidencia: dependencia de salud en `auth/pom.xml:38-41`; no hay checks
personalizados en `auth/src/main/java/`. La prueba de integración afirma el
status UP, el tipo JSON y el array vacío
(`auth/src/test/java/com/bcp/workshop/auth/HealthEndpointTest.java:14-29`).

### 5. Respuestas de error

El código de `auth/` no declara respuestas de error para este endpoint. Si el
proceso no está escuchando, el cliente no recibe una respuesta HTTP. SmallRye
Health puede reportar estados no saludables cuando hay checks que fallan, pero
`auth/` no registra checks propios; el status y cuerpo de ese escenario no se
han comprobado en este proyecto y quedan como pregunta abierta, no como contrato
confirmado. La prueba cubre solamente el caso UP sin checks registrados.

### 6. Notas de seguridad

El endpoint es público y solo informa salud; no lo uses como autorización para
operaciones de negocio. La ruta `/q/health` aparece como URL pública local en
`README.md:44`.

## POST /auth/login

### 1. Propósito de negocio

Autentica a una persona con su usuario y contraseña y, si son válidos, emite un
token de acceso firmado para iniciar sesión.

### 2. Autenticación

No requiere autenticación previa ni un header `Authorization`: este es el
endpoint de inicio de sesión (`auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:28-30`).
Requiere `Content-Type: application/json`; produce `application/json`
(`auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:14-16`).

### 3. Request

| campo | tipo | obligatorio | descripción |
|---|---|---|---|
| `username` | string | Sí | Nombre de usuario; debe contener texto no blanco. |
| `password` | string | Sí | Contraseña; debe contener texto no blanco. |
| `client` | string | No | Campo aceptado por el DTO, pero no se utiliza para autenticar ni construir la respuesta. |

Los campos y tipos se definen en
`auth/src/main/java/com/bcp/workshop/auth/LoginRequest.java:3-6`; la validación
de `username` y `password` está en
`auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:31-39`. `client` no
se pasa al servicio (`auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:41-43`).

Ejemplo JSON para el entorno local de desarrollo/pruebas:

```json
{
  "username": "student",
  "password": "Workshop123!",
  "client": "angular-workshop"
}
```

La cuenta es ficticia y se usa en pruebas locales; no uses estas credenciales
como cuenta de producción (`README.md:44`,
`auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java:23-30,63-65`).
El seed de cuentas demo está deshabilitado en el perfil `prod`
(`auth/src/main/resources/application.properties:10-11`).

### 4. Response exitosa

- **Código:** `200 OK`.
- **Content-Type:** `application/json`.

`AuthService` consulta las credenciales y crea el token
(`auth/src/main/java/com/bcp/workshop/auth/AuthService.java:14-22`). La forma
del DTO está en
`auth/src/main/java/com/bcp/workshop/auth/LoginResponse.java:5-17`; el tiempo
de expiración es 3600 segundos
(`auth/src/main/java/com/bcp/workshop/auth/LegacyTokenUtil.java:19,39-43`).

| campo | tipo | descripción |
|---|---|---|
| `token` | string | JWT compacto firmado con HS256. Incluye `sub`, `role`, `iat` y `exp`. |
| `expiresIn` | integer | Vigencia del token en segundos; actualmente `3600`. |
| `user` | object | Datos públicos del usuario autenticado. |
| `user.username` | string | Nombre de usuario. |
| `user.displayName` | string | Nombre mostrado; se escapa como HTML antes de responder. |
| `user.role` | string | Rol del usuario, por ejemplo `STUDENT`. |
| `debug` | string | Valor fijo actual: `authenticated-with-legacy-flow`. |

Ejemplo JSON completo en estructura. El token es dinámico y depende de la clave
de firma configurada; el texto entre `<...>` es un marcador documental y no se
puede enviar como token válido:

```json
{
  "token": "<JWT HS256 generado por el servidor>",
  "expiresIn": 3600,
  "user": {
    "username": "student",
    "displayName": "Workshop Student",
    "role": "STUDENT"
  },
  "debug": "authenticated-with-legacy-flow"
}
```

La prueba de login valida el status, los campos estables y que `token` no sea
nulo (`auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java:20-33`).
No captura una respuesta literal con un token; por ello el ejemplo no inventa
una firma estática.

### 5. Respuestas de error

Todas las respuestas de error construidas por `AuthResource` tienen un objeto
JSON con el campo string `message`
(`auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:60-61`).

| código | cuándo ocurre | ejemplo JSON |
|---|---|---|
| `400 Bad Request` | `username` ausente, vacío o en blanco. | `{"message":"Username is required"}` |
| `400 Bad Request` | `password` ausente, vacío o en blanco. | `{"message":"Password is required"}` |
| `400 Bad Request` | El método recibe un request nulo. | `{"message":"Request is null"}` |
| `401 Unauthorized` | Usuario inexistente o contraseña incorrecta. El texto incluye el username recibido. | `{"message":"Invalid user student or password"}` |
| `500 Internal Server Error` | El servicio lanza una `RuntimeException`; el detalle se registra en el servidor, no se devuelve. | `{"message":"Internal server error"}` |
| `403 Forbidden` | CORS rechaza un origen que no está permitido. La prueba confirma el status para un origen no listado. | **Cuerpo no establecido:** la prueba solo verifica el status; Quarkus genera esta respuesta y el código de auth no define su JSON. |
| `415 Unsupported Media Type` | El runtime rechaza `Content-Type: text/plain`; la prueba de integración confirma el status. | **Cuerpo no establecido:** la prueba solo verifica el status; Quarkus genera esta respuesta y el código de auth no define su JSON. |

Evidencia de validación y status:
`auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:31-52`; pruebas de
`401`, `400` y `403`:
`auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java:50-169`;
respuesta `500`:
`auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:50-52` y prueba
HTTP `auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java:194-210`,
con una prueba unitaria complementaria en
`auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java:213-231`.
La prueba CORS confirma solo `403`, no el cuerpo
(`auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java:160-169`).

Pregunta abierta: comprobar en runtime los cuerpos de `403` y `415`, y las
respuestas del runtime a JSON malformado o cuerpo vacío. Esos cuerpos no están
definidos por el recurso ni tienen ejemplos JSON verificados aquí. La prueba de
`415` verifica el status con `text/plain`
(`auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java:183-191`).

### 6. Notas de seguridad

- El token se firma con HS256, expira en una hora y contiene `sub`, `role`,
  `iat` y `exp` (`auth/src/main/java/com/bcp/workshop/auth/LegacyTokenUtil.java:17-52`).
- La clave procede de `AUTH_TOKEN_SECRET`; en producción no hay clave por
  defecto y el servicio falla al iniciar si la clave no alcanza 32 bytes
  (`auth/src/main/resources/application.properties:12-14`,
  `auth/src/main/java/com/bcp/workshop/auth/LegacyTokenUtil.java:26-31`). No
  incluyas esa clave en el cliente ni en esta documentación.
- El código de `auth/` emite el token, pero no implementa un endpoint de
  validación. El componente que lo consuma debe verificar firma y expiración
  usando la configuración segura acordada fuera del cliente; la integración
  con consumidores externos no se verificó en este alcance.
- La configuración CORS permite por defecto `http://localhost:4200` en modo
  local y requiere `AUTH_CORS_ORIGINS` en `prod`
  (`auth/src/main/resources/application.properties:4-8`).
- `debug` forma parte de la respuesta exitosa por compatibilidad observada; no
  debe interpretarse como dato de autorización.
