package com.bcp.workshop.auth;

import com.nimbusds.jose.crypto.MACVerifier;
import com.nimbusds.jwt.SignedJWT;
import io.quarkus.test.junit.QuarkusTest;
import jakarta.inject.Inject;
import org.eclipse.microprofile.config.inject.ConfigProperty;
import org.junit.jupiter.api.Test;

import java.nio.charset.StandardCharsets;
import java.util.Date;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

@QuarkusTest
class LegacyTokenUtilTest {
    @Inject
    LegacyTokenUtil tokenUtil;

    @ConfigProperty(name = "auth.token.secret")
    String testSecret;

    @Test
    void createsSignedTokenWithIdentityAndExpirationClaims() throws Exception {
        SignedJWT token = SignedJWT.parse(tokenUtil.create("test-user", "STUDENT"));

        assertTrue(token.verify(new MACVerifier(testSecret.getBytes(StandardCharsets.UTF_8))));
        assertEquals("test-user", token.getJWTClaimsSet().getSubject());
        assertEquals("STUDENT", token.getJWTClaimsSet().getStringClaim("role"));
        assertTrue(token.getJWTClaimsSet().getExpirationTime().after(new Date()));
    }

    @Test
    void rejectsModifiedSignature() throws Exception {
        String[] tokenSegments = tokenUtil.create("test-user", "STUDENT").split("\\.", -1);
        char replacement = tokenSegments[2].charAt(0) == 'A' ? 'B' : 'A';
        tokenSegments[2] = replacement + tokenSegments[2].substring(1);
        SignedJWT modifiedToken = SignedJWT.parse(String.join(".", tokenSegments));

        assertFalse(modifiedToken.verify(new MACVerifier(testSecret.getBytes(StandardCharsets.UTF_8))));
    }

    @Test
    void rejectsSigningKeyShorterThanRequiredLength() {
        LegacyTokenUtil invalidTokenUtil = new LegacyTokenUtil();
        invalidTokenUtil.configuredSecret = "short-test-key";

        assertThrows(IllegalStateException.class, invalidTokenUtil::initialize);
    }
}
