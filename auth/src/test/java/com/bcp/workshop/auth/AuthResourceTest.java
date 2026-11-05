package com.bcp.workshop.auth;

import io.quarkus.test.junit.QuarkusTest;
import io.restassured.response.ValidatableResponse;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

import java.util.Map;

import static io.restassured.RestAssured.given;
import static org.hamcrest.CoreMatchers.is;
import static org.hamcrest.Matchers.notNullValue;
import static org.hamcrest.Matchers.nullValue;

@QuarkusTest
class AuthResourceTest {
    private static final String VALID_USERNAME = "student";
    private static final String VALID_PASSWORD = "Workshop123!";
    private static final String SQL_INJECTION_VALUE = "' OR '1'='1";

    private ValidatableResponse login(String username, String password) {
        return given()
                .contentType("application/json")
                .body(Map.of("username", username, "password", password, "client", "angular-workshop"))
                .when().post("/auth/login")
                .then();
    }

    // Spec "Login válido conservado": forma completa del 200.
    @Test
    void logsInWithWorkshopUser() {
        login(VALID_USERNAME, VALID_PASSWORD)
                .statusCode(200)
                .body("token", notNullValue())
                .body("expiresIn", is(3600))
                .body("user.username", is("student"))
                .body("user.displayName", is("Workshop Student"))
                .body("user.role", is("STUDENT"));
    }

    // Spec "Rechazos existentes conservados / Credenciales incorrectas".
    @Test
    void rejectsWrongPasswordWith401AndNoToken() {
        login(VALID_USERNAME, "wrong-password")
                .statusCode(401)
                .body("message", notNullValue())
                .body("token", nullValue());
    }

    // Spec "Rechazos existentes conservados / Credenciales incorrectas" (usuario desconocido).
    @Test
    void rejectsUnknownUserWith401AndNoToken() {
        login("nobody", "Workshop123!")
                .statusCode(401)
                .body("message", notNullValue())
                .body("token", nullValue());
    }

    // Spec "Rechazos existentes conservados / Campos vacíos" (username).
    @ParameterizedTest
    @ValueSource(strings = {"", "   "})
    void rejectsEmptyOrBlankUsernameWith400(String username) {
        login(username, VALID_PASSWORD)
                .statusCode(400)
                .body("message", notNullValue());
    }

    // Spec "Rechazos existentes conservados / Campos vacíos" (password).
    @ParameterizedTest
    @ValueSource(strings = {"", "   "})
    void rejectsEmptyOrBlankPasswordWith400(String password) {
        login(VALID_USERNAME, password)
                .statusCode(400)
                .body("message", notNullValue());
    }

    // Design "Contraseña con comillas": hoy el error de SQL se traduce en 401, debe seguir sin ser 500.
    @Test
    void rejectsPasswordWithSingleQuoteWith401() {
        login(VALID_USERNAME, "it's")
                .statusCode(401)
                .body("token", nullValue());
    }

    // Spec "Credenciales tratadas como datos / Inyección en el usuario".
    @Test
    void rejectsSqlInjectionInUsernameWith401AndNoToken() {
        login(SQL_INJECTION_VALUE, "any-password")
                .statusCode(401)
                .body("token", nullValue());
    }

    // Spec "Credenciales tratadas como datos / Inyección en el usuario con comentario SQL".
    @Test
    void rejectsSqlCommentInjectionInUsernameWith401AndNoToken() {
        login(SQL_INJECTION_VALUE + "' --", "any-password")
                .statusCode(401)
                .body("token", nullValue());
    }

    // Spec "Credenciales tratadas como datos / Inyección en la contraseña".
    @Test
    void rejectsSqlInjectionInPasswordWith401AndNoToken() {
        login(VALID_USERNAME, SQL_INJECTION_VALUE)
                .statusCode(401)
                .body("token", nullValue());
    }

    // Spec "Credenciales tratadas como datos / Inyección en ambos campos".
    @Test
    void rejectsSqlInjectionInBothFieldsWith401AndNoToken() {
        login(SQL_INJECTION_VALUE, SQL_INJECTION_VALUE)
                .statusCode(401)
                .body("token", nullValue());
    }
}
