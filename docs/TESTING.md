# Pruebas de contrato HTTP — auth

## Alcance

Esta evidencia cubre únicamente los endpoints `GET /q/health` y
`POST /auth/login` documentados en [ENDPOINTS.md](./ENDPOINTS.md). Los casos
usan el perfil de pruebas y credenciales ficticias locales. No se modificó
código de producción ni se inspeccionaron otros componentes.

## Matriz de casos

| endpoint | caso | tipo | resultado esperado | test | IDs |
|---|---|---|---|---|---|
| `GET /q/health` | Consulta anónima | Camino feliz | `200`, JSON y `status: UP`, sin requerir `Authorization`. | `reportsUpWithoutAuthentication` | Sin hallazgo asociado; contrato de endpoint |
| `GET /q/health` | No hay checks registrados | Borde | `200` y `checks: []`. | `reportsNoChecksWhenNoneAreRegistered` | Sin hallazgo asociado; contrato de endpoint |
| `GET /q/health` | Estado no saludable | Pendiente | No hay respuesta de error definida en el contrato actual ni checks de salud registrados para producirla; no se presupone un `503`. | No implementado | Pregunta abierta del contrato |
| `POST /auth/login` | Credenciales ficticias válidas con `client` | Camino feliz | `200`; token no nulo, `expiresIn: 3600` y los datos `user`/`debug` documentados. | `logsInWithWorkshopUser` | H-AUTH-02, H-AUTH-03 |
| `POST /auth/login` | Omitir el campo opcional `client` | Borde | `200`; token compacto de tres partes. | `returnsCompactSignedToken` | H-AUTH-03 |
| `POST /auth/login` | Request JSON `null` | Error | `400`, `{"message":"Request is null"}`. | `rejectsNullRequestBody` | H-AUTH-06 |
| `POST /auth/login` | Falta `username` | Error | `400`, `{"message":"Username is required"}`. | `rejectsMissingUsername` | H-AUTH-06 |
| `POST /auth/login` | Falta `password` | Error | `400`, `{"message":"Password is required"}`. | `rejectsMissingPassword` | H-AUTH-06 |
| `POST /auth/login` | `username` vacío o en blanco | Borde / error | `400`, `{"message":"Username is required"}`. | `rejectsEmptyUsername`, `rejectsWhitespaceUsername` | H-AUTH-06 |
| `POST /auth/login` | `password` vacío o en blanco | Borde / error | `400`, `{"message":"Password is required"}`. | `rejectsEmptyPassword`, `rejectsWhitespacePassword` | H-AUTH-06 |
| `POST /auth/login` | Contraseña incorrecta para usuario conocido | Error | `401`, `{"message":"Invalid user student or password"}`. | `rejectsIncorrectPasswordForKnownUser` | H-AUTH-02, H-AUTH-06 |
| `POST /auth/login` | Usuario desconocido | Error | `401`, `{"message":"Invalid user unknown-user or password"}`. | `rejectsInvalidCredentials` | H-AUTH-02, H-AUTH-06 |
| `POST /auth/login` | Username contiene comilla | Borde | `401`; no autentica ni produce un error SQL; mensaje genérico que incluye el username recibido. | `rejectsCredentialsContainingQuote` | H-AUTH-01 |
| `POST /auth/login` | Origen CORS no listado | Error | `403`; el cuerpo no está fijado por el endpoint. | `doesNotAllowUnlistedOrigin` | H-AUTH-04 |
| `POST /auth/login` | `Content-Type: text/plain` | Error | `415`; el cuerpo lo genera Quarkus y no forma parte del contrato comprobado. | `rejectsUnsupportedContentType` | Contrato de endpoint; sin ID de hallazgo |
| `POST /auth/login` | Excepción de runtime en el servicio | Error | `500`, `{"message":"Internal server error"}`; no expone detalle ni clase de excepción. | `returnsGenericErrorOverHttpWhenServiceFails` | H-AUTH-06 |
| `POST /auth/login` | Excepción de runtime, invocación directa del recurso | Error / unitario | `500` y entidad `message: Internal server error`; la entidad no contiene `exception`. | `doesNotExposeExceptionDetails` | H-AUTH-06 |

No se prueba un error para `/q/health` porque el contrato no declara una
respuesta HTTP de error. Tampoco se fijan en estas pruebas los cuerpos que el
runtime genera para CORS o tipo de contenido.

## Código de los tests

### `auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java`

```java
package com.bcp.workshop.auth;

import io.quarkus.test.junit.QuarkusMock;
import io.quarkus.test.junit.QuarkusTest;
import jakarta.ws.rs.core.Response;
import org.junit.jupiter.api.Test;

import java.util.Map;

import static io.restassured.RestAssured.given;
import static org.hamcrest.CoreMatchers.is;
import static org.hamcrest.Matchers.notNullValue;
import static org.hamcrest.Matchers.nullValue;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;

@QuarkusTest
class AuthResourceTest {
    @Test
    void logsInWithWorkshopUser() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"Workshop123!\",\"client\":\"angular-workshop\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(200)
                .body("user.username", is("student"))
                .body("user.displayName", is("Workshop Student"))
                .body("user.role", is("STUDENT"))
                .body("expiresIn", is(3600))
                .body("debug", is("authenticated-with-legacy-flow"))
                .body("token", notNullValue());
    }

    @Test
    void returnsCompactSignedToken() {
        String token = given()
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"Workshop123!\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(200)
                .extract()
                .path("token");

        assertEquals(3, token.split("\\.", -1).length);
    }

    @Test
    void rejectsIncorrectPasswordForKnownUser() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"incorrect-password\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(401)
                .body("message", is("Invalid user student or password"));
    }

    @Test
    void rejectsInvalidCredentials() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"unknown-user\",\"password\":\"invalid-password\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(401)
                .body("message", is("Invalid user unknown-user or password"));
    }

    @Test
    void rejectsMissingUsername() {
        given()
                .contentType("application/json")
                .body("{\"password\":\"Workshop123!\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(400)
                .body("message", is("Username is required"));
    }

    @Test
    void rejectsMissingPassword() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"student\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(400)
                .body("message", is("Password is required"));
    }

    @Test
    void rejectsNullRequestBody() {
        given()
                .contentType("application/json")
                .body("null")
                .when().post("/auth/login")
                .then()
                .statusCode(400)
                .body("message", is("Request is null"));
    }

    @Test
    void rejectsEmptyUsername() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"\",\"password\":\"Workshop123!\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(400)
                .body("message", is("Username is required"));
    }

    @Test
    void rejectsWhitespaceUsername() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"   \",\"password\":\"Workshop123!\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(400)
                .body("message", is("Username is required"));
    }

    @Test
    void rejectsEmptyPassword() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(400)
                .body("message", is("Password is required"));
    }

    @Test
    void rejectsWhitespacePassword() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"   \"}")
                .when().post("/auth/login")
                .then()
                .statusCode(400)
                .body("message", is("Password is required"));
    }

    @Test
    void rejectsCredentialsContainingQuote() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"student'\",\"password\":\"Workshop123!\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(401)
                .body("message", is("Invalid user student' or password"));
    }

    @Test
    void doesNotAllowUnlistedOrigin() {
        given()
                .header("Origin", "https://unlisted.invalid")
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"Workshop123!\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(403);
    }

    @Test
    void allowsApprovedLocalOriginAfterCorsRestriction() {
        given()
                .header("Origin", "http://localhost:4200")
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"Workshop123!\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(200)
                .header("Access-Control-Allow-Origin", is("http://localhost:4200"));
    }

    @Test
    void rejectsUnsupportedContentType() {
        given()
                .contentType("text/plain")
                .accept("application/json")
                .body("not-json")
                .when().post("/auth/login")
                .then()
                .statusCode(415);
    }

    @Test
    void returnsGenericErrorOverHttpWhenServiceFails() {
        QuarkusMock.installMockForType(new AuthService() {
            @Override
            public LoginResponse login(String username, String password) {
                throw new IllegalStateException("test-only failure");
            }
        }, AuthService.class);

        given()
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"Workshop123!\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(500)
                .body("message", is("Internal server error"))
                .body("exception", nullValue());
    }

    @Test
    void doesNotExposeExceptionDetails() {
        AuthResource resource = new AuthResource();
        resource.authService = new AuthService() {
            @Override
            public LoginResponse login(String username, String password) {
                throw new IllegalStateException("test-only failure");
            }
        };
        LoginRequest request = new LoginRequest();
        request.username = "student";
        request.password = "Workshop123!";

        Response response = resource.login(request);
        Map<?, ?> body = (Map<?, ?>) response.getEntity();

        assertEquals(500, response.getStatus());
        assertEquals("Internal server error", body.get("message"));
        assertFalse(body.containsKey("exception"));
    }
}
```

### `auth/src/test/java/com/bcp/workshop/auth/HealthEndpointTest.java`

```java
package com.bcp.workshop.auth;

import io.quarkus.test.junit.QuarkusTest;
import io.restassured.http.ContentType;
import org.junit.jupiter.api.Test;

import static io.restassured.RestAssured.given;
import static org.hamcrest.CoreMatchers.is;
import static org.hamcrest.Matchers.hasSize;

@QuarkusTest
class HealthEndpointTest {
    @Test
    void reportsUpWithoutAuthentication() {
        given()
                .when().get("/q/health")
                .then()
                .statusCode(200)
                .contentType(ContentType.JSON)
                .body("status", is("UP"));
    }

    @Test
    void reportsNoChecksWhenNoneAreRegistered() {
        given()
                .when().get("/q/health")
                .then()
                .statusCode(200)
                .body("checks", hasSize(0));
    }
}
```

### `auth/src/test/java/com/bcp/workshop/auth/LoginResponseTest.java`

```java
package com.bcp.workshop.auth;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

class LoginResponseTest {
    @Test
    void escapesHtmlCharactersInDisplayName() {
        LoginResponse response = LoginResponse.from(
                new UserRecord(1, "test-user", "A & <B>", "STUDENT"),
                "test-token"
        );

        assertEquals("A &amp; &lt;B&gt;", response.user().displayName());
    }
}
```

## Comandos y resultados ejecutados

Las pruebas se ejecutaron con cwd `auth/`, como requiere el proyecto. El
código de salida `0` corresponde al proceso Maven.

| fecha | componente | IDs / alcance | comando | cwd | código de salida | resultado real |
|---|---|---|---|---|---:|---|
| 2026-10-26 | auth | Endpoints de health y login; H-AUTH-01, H-AUTH-02, H-AUTH-03, H-AUTH-04, H-AUTH-06 | `mvn '-Dtest=AuthResourceTest,HealthEndpointTest' test` | `auth/` | 0 | Ejecución preliminar antes de añadir la prueba HTTP de `500`: 18 pruebas (16 `AuthResourceTest`, 2 `HealthEndpointTest`), sin fallos, errores ni omisiones. |
| 2026-10-26 | auth | Suite completa; H-AUTH-01, H-AUTH-02, H-AUTH-03, H-AUTH-04, H-AUTH-06, H-AUTH-08 | `mvn verify` | `auth/` | 0 | Ejecución preliminar antes de añadir la prueba HTTP de `500`: `BUILD SUCCESS`; 31 pruebas, sin fallos, errores ni omisiones. |
| 2026-10-26 | auth | Endpoints de health y login; H-AUTH-01, H-AUTH-02, H-AUTH-03, H-AUTH-04, H-AUTH-06 | `mvn '-Dtest=AuthResourceTest,HealthEndpointTest' test` | `auth/` | 0 | Resultado final: 19 pruebas (17 `AuthResourceTest`, 2 `HealthEndpointTest`), 0 fallos, 0 errores, 0 omitidas. |
| 2026-10-26 | auth | Suite completa; H-AUTH-01, H-AUTH-02, H-AUTH-03, H-AUTH-04, H-AUTH-06, H-AUTH-08 | `mvn verify` | `auth/` | 0 | Resultado final: `BUILD SUCCESS`; 32 pruebas, 0 fallos, 0 errores, 0 omitidas. JaCoCo produjo el reporte. |
| 2026-10-26 | auth | Caracterización SCA; H-AUTH-05 | `mvn '-Dtest=LoginResponseTest,LegacyTokenUtilTest,AuthResourceTest' test` | `auth/` | 0 | Antes del cambio de BOM: 21 pruebas, 0 fallos, 0 errores, 0 omitidas. |
| 2026-10-26 | auth | Suite de línea base; H-AUTH-05 | `mvn verify` | `auth/` | 0 | Antes del cambio de BOM: 33 pruebas, 0 fallos, 0 errores, 0 omitidas; JaCoCo generó el reporte. |
| 2026-10-26 | auth | Árbol de línea base; H-AUTH-05 | `mvn dependency:tree -DoutputFile=target\auth-dependency-tree.txt -DoutputType=text` | `auth/` | 0 | Árbol Maven capturado: 223 coordenadas JAR incluidas en la consulta OSV. |
| 2026-10-26 | auth | OWASP Dependency-Check; H-AUTH-05 | `mvn org.owasp:dependency-check-maven:13.0.0:check -Dformat=JSON` | `auth/` | 1 | No concluyó: NVD rechazó la clave ausente (`NVD_API_KEY` con longitud 0); no es un resultado sin vulnerabilidades. |
| 2026-10-26 | auth | OSV de línea base; H-AUTH-05 | `python -` con script inline `urllib.request` para OSV API `v1/querybatch` | `ai-labs/` | 0 | 223 coordenadas, 48 advisory IDs en 10 coordenadas afectadas. |
| 2026-10-26 | auth | Presentación inicial de detalles OSV; H-AUTH-05 | `python -` con script inline de consulta `/v1/vulns/{id}` | `ai-labs/` | 1 | `UnicodeEncodeError` al imprimir un carácter no representable en la consola. |
| 2026-10-26 | auth | Presentación corregida de detalles OSV; H-AUTH-05 | `python -` con script inline y escape ASCII para `/v1/vulns/{id}` | `ai-labs/` | 0 | Se recuperaron los detalles de los 48 advisory IDs de la línea base. |
| 2026-10-26 | auth | Resolución del candidato Quarkus 3.27.6.1; H-AUTH-05 | `mvn "-Dquarkus.platform.version=3.27.6.1" dependency:tree -DoutputFile=target\auth-dependency-tree-3.27.6.1.txt -DoutputType=text` | `auth/` | 0 | Candidato resuelve Jackson 2.21.7, Netty 4.1.139.Final y `quarkus-vertx-http` 3.27.6.1. |
| 2026-10-26 | auth | OSV del árbol candidato; H-AUTH-05 | `python -` con script inline `urllib.request` para OSV API `v1/querybatch` | `auth/` | 0 | Las 222 coordenadas del candidato devolvieron 0 coincidencias. |
| 2026-10-26 | auth | Primer intento OSV del árbol candidato; H-AUTH-05 | `python -` con script inline que apuntaba a `target/` desde la raíz | `ai-labs/` | 1 | `FileNotFoundError`; se corrigió el cwd a `auth/` y la consulta completa terminó con código 0. |
| 2026-10-26 | auth | Caracterización después del cambio de BOM; H-AUTH-05 | `mvn '-Dtest=LoginResponseTest,LegacyTokenUtilTest,AuthResourceTest' test` | `auth/` | 0 | 21 pruebas, 0 fallos, 0 errores, 0 omitidas. |
| 2026-10-26 | auth | Suite después del cambio de BOM; H-AUTH-05 | `mvn verify` | `auth/` | 0 | `BUILD SUCCESS`; 33 pruebas, 0 fallos, 0 errores, 0 omitidas; JaCoCo: 152/161 líneas (94.4%) en el bundle. |
| 2026-10-26 | auth | Árbol final; H-AUTH-05 | `mvn dependency:tree -DoutputFile=target\auth-dependency-tree-final.txt -DoutputType=text` | `auth/` | 0 | 222 coordenadas Maven JAR en el árbol final. |
| 2026-10-26 | auth | OSV final; H-AUTH-05 | Python 3, `urllib.request`, OSV API `v1/querybatch` | `auth/` | 0 | Consulta completa de 222 coordenadas; 0 coincidencias y 0 advisory IDs. |

## Cobertura

Medición con JaCoCo, usando los contadores `LINE` de
`auth/target/site/jacoco/jacoco.xml`; el HTML se genera en
`auth/target/site/jacoco/index.html`. El porcentaje se calcula como
`líneas cubiertas / (líneas cubiertas + líneas no cubiertas)`.

| alcance medido | resultado |
|---|---:|
| Bundle de producción `workshop-auth-backend` | 146/156 líneas (93.6%) |
| `AuthResource` | 18/18 líneas (100%) |
| Bundle después de H-AUTH-05 | 152/161 líneas (94.4%) |
| `AuthResource` después de H-AUTH-05 | 20/20 líneas (100%) |
| `AuthService` después de H-AUTH-05 | 6/6 líneas (100%) |
| `LoginResponse` después de H-AUTH-05 | 6/6 líneas (100%) |
| `LegacyTokenUtil` después de H-AUTH-05 | 18/20 líneas (90%) |

H-AUTH-05 actualiza únicamente la versión del BOM en `auth/pom.xml`; no se
modificaron clases Java de producción. `LoginResponseTest` se añadió y ejecutó
antes del cambio de POM. JaCoCo no instrumenta `src/test/`, por lo que estos
porcentajes describen el código de producción ejercitado, no las líneas de los
tests. Las clases de auth medidas superan el 85%; el endpoint de salud lo
genera Quarkus y no tiene código de aplicación medible en `auth/`.

## Evidencia SCA — H-AUTH-05

La línea base consultó en OSV la versión Maven resuelta de cada artefacto JAR.
Los 48 advisory IDs aparecieron en estas 10 coordenadas:

| coordenada de línea base | advisory IDs OSV |
|---|---|
| `com.fasterxml.jackson.core:jackson-core:2.21.2` | GHSA-7hhh-6rmp-j9qf, GHSA-p6pp-m3f8-5c89, GHSA-r7wm-3cxj-wff9 |
| `com.fasterxml.jackson.core:jackson-databind:2.21.2` | GHSA-3pjw-73gf-8qr5, GHSA-5gvw-p9qm-jgwh, GHSA-5hh8-q8hv-fr38, GHSA-5jmj-h7xm-6q6v, GHSA-9fxm-vc8v-hj55, GHSA-cxp5-3px4-pw24, GHSA-gx83-3vf8-gh7j, GHSA-hgj6-7826-r7m5, GHSA-j3rv-43j4-c7qm, GHSA-mhm7-754m-9p8w, GHSA-q4xh-88c3-wmh7, GHSA-rcqc-6cw3-h962, GHSA-rmj7-2vxq-3g9f, GHSA-vvgp-rfg2-7rr6, GHSA-wjgm-6hv5-3cvf, GHSA-wv8q-qhhj-9h54 |
| `io.netty:netty-codec-dns:4.1.133.Final` | GHSA-mfg7-5gfp-c4w3 |
| `io.netty:netty-codec-haproxy:4.1.133.Final` | GHSA-cc37-9q2j-3hfv, GHSA-h2qv-fj59-j46j, GHSA-q6cq-mhr2-jmr5, GHSA-wh89-7897-x99h |
| `io.netty:netty-codec-http2:4.1.133.Final` | GHSA-563q-j3cm-6jxm, GHSA-5x3r-wrvg-rp6q, GHSA-93wv-jw9v-4972, GHSA-c2gf-v879-257j, GHSA-c69g-56f8-xwqj |
| `io.netty:netty-codec-http:4.1.133.Final` | GHSA-4mp9-239f-g9hg, GHSA-6cqp-g7gg-8hr5, GHSA-6jqx-86gh-f27w, GHSA-8c42-7qj2-3j46, GHSA-gcjf-9mgh-3p7g, GHSA-hvcg-qmg6-jm4c, GHSA-jppx-w49h-x2qq, GHSA-mvh2-crg5-v77c, GHSA-q4f6-jm68-57ww |
| `io.netty:netty-codec:4.1.133.Final` | GHSA-558v-64gr-wgg4 |
| `io.netty:netty-handler:4.1.133.Final` | GHSA-3qp7-7mw8-wx86, GHSA-c4c3-7fpv-j4q5, GHSA-c653-97m9-rcg9, GHSA-fccg-mwvh-qqg4, GHSA-x4gw-5cx5-pgmh |
| `io.netty:netty-resolver-dns:4.1.133.Final` | GHSA-5pvg-856g-cp85, GHSA-676x-f7gg-47vc, GHSA-xmv7-r254-6q78 |
| `io.quarkus:quarkus-vertx-http:3.27.4` | GHSA-qcxp-gm7m-4j5v |

El BOM final `3.27.6.1` resuelve Jackson `2.21.7`, Netty `4.1.139.Final` y
`quarkus-vertx-http` `3.27.6.1`; la consulta OSV final cubrió 222 coordenadas
JAR y no devolvió advisories. Esto no sustituye los controles remotos ni el
análisis de Dependency-Check: CodeQL y Dependency Review no se ejecutaron, y
Dependency-Check no concluyó por la actualización NVD sin `NVD_API_KEY`.

## Fallos

- Las ejecuciones Maven de pruebas registradas terminaron sin fallos ni
  errores. Una ejecución histórica de `mvn clean verify` no llegó a las
  pruebas porque un proceso retenía el JAR de `target`; un `mvn verify`
  posterior sí terminó correctamente.
- OWASP Dependency-Check finalizó con código 1 antes de completar el análisis:
  no estaba configurada `NVD_API_KEY` y NVD devolvió `NoDataException`. No se
  interpreta como resultado limpio.
- Una primera presentación de los detalles OSV falló por un carácter no
  representable en la consola Windows; se repitió con escape ASCII y se
  recuperaron los 48 detalles. Un primer intento de consulta del árbol
  candidato apuntó a `target/` desde la raíz y falló con `FileNotFoundError`;
  la consulta repetida desde `auth/` terminó con código 0.

## Pendientes

- El endpoint de salud no registra checks que permitan probar un estado
  `DOWN`; no se asigna ni se presume un status o cuerpo de error.
- Las pruebas de CORS `403` y tipo de contenido `415` verifican el status, no
  un cuerpo JSON. El runtime lo genera y el contrato lo deja abierto.
- JSON malformado y cuerpo HTTP vacío no tienen respuesta documentada ni
  expectativas de test.
- H-AUTH-05 está resuelto con la consulta OSV local del árbol completo. OWASP
  Dependency-Check no concluyó por falta de `NVD_API_KEY`; CodeQL y Dependency
  Review remotos no se ejecutaron y no se reportan como aprobados.

## Pruebas propuestas

- Si se acuerda un contrato para el estado no saludable de `/q/health`, añadir
  un health check de prueba controlado y comprobar status y cuerpo exactos.
- Si los consumidores necesitan un formato estable para `403` o `415`, capturar
  las respuestas del runtime en una prueba local y acordar/documentar el body
  antes de fijarlo en assertions.
- Acordar primero el status y body esperados para JSON malformado o cuerpo
  vacío; entonces añadir pruebas de integración para esos requests.

## Documentos y fuentes consultados

- [README.md](../README.md): comandos locales y credenciales ficticias de
  desarrollo.
- [RETO.md](../RETO.md): alcance de auth y hallazgos candidatos.
- [GOOD_PRACTICES.md](./GOOD_PRACTICES.md): convenciones de pruebas y seguridad
  para auth.
- [HALLAZGOS.md](../HALLAZGOS.md) y [PLAN.md](../PLAN.md): IDs, estados e
  historial de ejecuciones de auth.
- [ENDPOINTS.md](./ENDPOINTS.md): contrato observado de ambos endpoints.
- Código y pruebas de auth consultados: `auth/pom.xml`,
  `auth/src/main/resources/application.properties`,
  `auth/src/test/resources/application.properties`,
  `auth/src/main/java/com/bcp/workshop/auth/AuthResource.java`,
  `auth/src/main/java/com/bcp/workshop/auth/LoginRequest.java`,
  `auth/src/main/java/com/bcp/workshop/auth/LoginResponse.java`,
  `auth/src/main/java/com/bcp/workshop/auth/AuthService.java`,
  `auth/src/main/java/com/bcp/workshop/auth/LegacyTokenUtil.java`,
  `auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java` y
  `auth/src/test/java/com/bcp/workshop/auth/HealthEndpointTest.java`,
  `auth/src/test/java/com/bcp/workshop/auth/LoginResponseTest.java`.
