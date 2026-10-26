package com.bcp.workshop.auth;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class PasswordHasherTest {
    private final PasswordHasher passwordHasher = new PasswordHasher();

    @Test
    void verifiesPasswordAgainstStoredHash() {
        String password = "test-only-password";
        String hash = passwordHasher.hash(password);

        assertNotEquals(password, hash);
        assertTrue(passwordHasher.matches(password, hash));
        assertFalse(passwordHasher.matches("different-password", hash));
    }

    @Test
    void generatesDifferentHashesForSamePassword() {
        String password = "test-only-password";

        assertNotEquals(passwordHasher.hash(password), passwordHasher.hash(password));
    }

    @Test
    void rejectsMalformedStoredHash() {
        assertFalse(passwordHasher.matches("test-only-password", "not-a-password-hash"));
    }

    @Test
    void rejectsNullPasswordsAndHashes() {
        assertThrows(IllegalArgumentException.class, () -> passwordHasher.hash(null));
        assertFalse(passwordHasher.matches(null, passwordHasher.hash("test-only-password")));
        assertFalse(passwordHasher.matches("test-only-password", null));
        assertFalse(passwordHasher.isEncoded(null));
    }

    @Test
    void recognizesOnlyValidEncodedHashes() {
        String encodedPassword = passwordHasher.hash("test-only-password");

        assertTrue(passwordHasher.isEncoded(encodedPassword));
        assertFalse(passwordHasher.isEncoded("test-only-password"));
        assertFalse(passwordHasher.isEncoded("pbkdf2-sha256$invalid$%%%$%%%"));
    }

    @Test
    void rejectsMalformedHashFieldsAndIterationCounts() {
        assertFalse(passwordHasher.matches(
                "test-only-password", "pbkdf2-sha256$invalid$%%%$%%%"));
        assertFalse(passwordHasher.matches(
                "test-only-password", "pbkdf2-sha256$1$AA==$AA=="));
        assertFalse(passwordHasher.matches(
                "test-only-password", "pbkdf2-sha256$600001$AAAAAAAAAAAAAAAAAAAAAA==$"
                        + "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="));
    }
}
