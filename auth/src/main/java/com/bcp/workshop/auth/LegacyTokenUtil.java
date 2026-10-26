package com.bcp.workshop.auth;

import com.nimbusds.jose.JOSEException;
import com.nimbusds.jose.JWSAlgorithm;
import com.nimbusds.jose.JWSHeader;
import com.nimbusds.jose.crypto.MACSigner;
import com.nimbusds.jwt.JWTClaimsSet;
import com.nimbusds.jwt.SignedJWT;
import jakarta.annotation.PostConstruct;
import jakarta.enterprise.context.ApplicationScoped;
import org.eclipse.microprofile.config.inject.ConfigProperty;

import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Date;

@ApplicationScoped
public class LegacyTokenUtil {
    public static final int TOKEN_VALIDITY_SECONDS = 3600;

    private static final int MINIMUM_SIGNING_KEY_BYTES = 32;

    @ConfigProperty(name = "auth.token.secret", defaultValue = "")
    String configuredSecret;

    private byte[] signingKey;

    @PostConstruct
    void initialize() {
        byte[] configuredKey = configuredSecret.getBytes(StandardCharsets.UTF_8);
        if (configuredKey.length < MINIMUM_SIGNING_KEY_BYTES) {
            throw new IllegalStateException("AUTH_TOKEN_SECRET must contain at least 32 bytes");
        }
        signingKey = configuredKey;
    }

    public String create(String username, String role) {
        Instant issuedAt = Instant.now();
        JWTClaimsSet claims = new JWTClaimsSet.Builder()
                .subject(username)
                .claim("role", role)
                .issueTime(Date.from(issuedAt))
                .expirationTime(Date.from(issuedAt.plusSeconds(TOKEN_VALIDITY_SECONDS)))
                .build();
        SignedJWT token = new SignedJWT(
                new JWSHeader(JWSAlgorithm.HS256),
                claims
        );

        try {
            token.sign(new MACSigner(signingKey));
            return token.serialize();
        } catch (JOSEException error) {
            throw new IllegalStateException("Failed to create signed token", error);
        }
    }
}
