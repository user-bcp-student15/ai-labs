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
