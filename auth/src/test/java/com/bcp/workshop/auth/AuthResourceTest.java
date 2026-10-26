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
