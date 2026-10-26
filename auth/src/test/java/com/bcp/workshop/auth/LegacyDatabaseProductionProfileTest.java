package com.bcp.workshop.auth;

import io.quarkus.test.junit.QuarkusTest;
import io.quarkus.test.junit.QuarkusTestProfile;
import io.quarkus.test.junit.TestProfile;
import jakarta.inject.Inject;
import org.eclipse.microprofile.config.inject.ConfigProperty;
import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertFalse;

@QuarkusTest
@TestProfile(LegacyDatabaseProductionProfileTest.ProductionProfile.class)
class LegacyDatabaseProductionProfileTest {
    @Inject
    @ConfigProperty(name = "auth.seed-demo-users")
    boolean configuredSeedDemoUsers;

    @Test
    void configuresDemoAccountSeedingDisabledInProductionProfile() {
        assertFalse(configuredSeedDemoUsers);
    }

    public static class ProductionProfile implements QuarkusTestProfile {
        @Override
        public String getConfigProfile() {
            return "prod";
        }

        @Override
        public Map<String, String> getConfigOverrides() {
            return Map.of(
                    "auth.token.secret", "test-only-local-signing-key-more-than-32-bytes",
                    "quarkus.http.cors.origins", "http://localhost:4200"
            );
        }
    }
}
