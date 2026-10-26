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
