package com.bcp.workshop.auth;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Path;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.Statement;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

class LegacyDatabaseTest {
    private static final String STUDENT_PASSWORD = "Workshop123!";
    private static final String LEGACY_USERNAME = "legacy-test-user";
    private static final String LEGACY_PASSWORD = "test-only-legacy-password";
    private static final String TRAINER_PASSWORD = "Trainer123!";

    @Test
    void seedsDemonstrationAccountsInDefaultMode(@TempDir Path temporaryDirectory) throws Exception {
        registerSqliteDriver();
        String databaseUrl = "jdbc:sqlite:" + temporaryDirectory.resolve("demo-users.db");
        LegacyDatabase database = new LegacyDatabase(databaseUrl);

        database.initialize();

        UserRecord student = database.findByCredentials("student", STUDENT_PASSWORD);
        UserRecord trainer = database.findByCredentials("trainer", TRAINER_PASSWORD);

        assertNotNull(student);
        assertNotNull(trainer);
        assertEquals("STUDENT", student.role());
        assertEquals("TRAINER", trainer.role());
    }

    @Test
    void doesNotSeedDemonstrationAccountsWhenDisabled(@TempDir Path temporaryDirectory) throws Exception {
        registerSqliteDriver();
        String databaseUrl = "jdbc:sqlite:" + temporaryDirectory.resolve("no-demo-users.db");
        LegacyDatabase database = new LegacyDatabase(databaseUrl, false);

        database.initialize();

        assertNull(database.findByCredentials("student", STUDENT_PASSWORD));
        assertNull(database.findByCredentials("trainer", TRAINER_PASSWORD));
    }

    @Test
    void migratesExistingPlaintextPasswordAndRemainsIdempotent(@TempDir Path temporaryDirectory) throws Exception {
        Path databaseFile = temporaryDirectory.resolve("legacy-users.db");
        String databaseUrl = "jdbc:sqlite:" + databaseFile;
        createLegacyDatabase(databaseUrl);

        LegacyDatabase database = new LegacyDatabase(databaseUrl);
        database.initialize();

        assertNotNull(database.findByCredentials(LEGACY_USERNAME, LEGACY_PASSWORD));
        assertStoredPasswordIsHashed(databaseUrl);

        database.initialize();

        assertNotNull(database.findByCredentials(LEGACY_USERNAME, LEGACY_PASSWORD));
        assertStoredPasswordIsHashed(databaseUrl);
    }

    private static void createLegacyDatabase(String databaseUrl) throws Exception {
        registerSqliteDriver();
        try (Connection connection = DriverManager.getConnection(databaseUrl);
             Statement statement = connection.createStatement()) {
            statement.executeUpdate("CREATE TABLE legacy_users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT NOT NULL, display_name TEXT NOT NULL, role TEXT NOT NULL)");
        }
        try (Connection connection = DriverManager.getConnection(databaseUrl);
             PreparedStatement statement = connection.prepareStatement(
                     "INSERT INTO legacy_users(username, password, display_name, role) VALUES (?, ?, ?, ?)")) {
            statement.setString(1, LEGACY_USERNAME);
            statement.setString(2, LEGACY_PASSWORD);
            statement.setString(3, "Legacy Test User");
            statement.setString(4, "STUDENT");
            statement.executeUpdate();
        }
    }

    private static void registerSqliteDriver() throws ClassNotFoundException {
        Class.forName("org.sqlite.JDBC");
    }

    private static void assertStoredPasswordIsHashed(String databaseUrl) throws Exception {
        try (Connection connection = DriverManager.getConnection(databaseUrl);
             PreparedStatement statement = connection.prepareStatement(
                     "SELECT password FROM legacy_users WHERE username = ?")) {
            statement.setString(1, LEGACY_USERNAME);
            try (ResultSet result = statement.executeQuery()) {
                assertTrue(result.next());
                assertNotEquals(LEGACY_PASSWORD, result.getString("password"));
                assertTrue(result.getString("password").startsWith(PasswordHasher.ENCODED_PREFIX));
                assertEquals(false, result.next());
            }
        }
    }
}
