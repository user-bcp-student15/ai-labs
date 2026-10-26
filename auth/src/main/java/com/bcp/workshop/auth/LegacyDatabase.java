package com.bcp.workshop.auth;

import jakarta.annotation.PostConstruct;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import org.eclipse.microprofile.config.inject.ConfigProperty;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.LinkedHashMap;
import java.util.Map;

@ApplicationScoped
public class LegacyDatabase {
    private static final String DEFAULT_DB_URL = System.getenv().getOrDefault("AUTH_DB_URL", "jdbc:sqlite:./data/workshop.db");
    private static final String STUDENT_USERNAME = "student";
    private static final String STUDENT_PASSWORD = "Workshop123!";
    private static final String STUDENT_DISPLAY_NAME = "Workshop Student";
    private static final String TRAINER_USERNAME = "trainer";
    private static final String TRAINER_PASSWORD = "Trainer123!";
    private static final String TRAINER_DISPLAY_NAME = "Workshop Trainer";
    private static final String STUDENT_ROLE = "STUDENT";
    private static final String TRAINER_ROLE = "TRAINER";

    private final String databaseUrl;
    private final PasswordHasher passwordHasher = new PasswordHasher();

    @Inject
    @ConfigProperty(name = "auth.seed-demo-users")
    boolean seedDemoUsers;

    public LegacyDatabase() {
        this(DEFAULT_DB_URL, true);
    }

    LegacyDatabase(String databaseUrl) {
        this(databaseUrl, true);
    }

    LegacyDatabase(String databaseUrl, boolean seedDemoUsers) {
        this.databaseUrl = databaseUrl;
        this.seedDemoUsers = seedDemoUsers;
    }

    @PostConstruct
    void initialize() {
        try {
            Files.createDirectories(Path.of("data"));
        } catch (IOException error) {
            throw new IllegalStateException("Failed to create authentication data directory", error);
        }

        try (Connection connection = DriverManager.getConnection(databaseUrl);
             Statement statement = connection.createStatement()) {
            statement.executeUpdate("CREATE TABLE IF NOT EXISTS legacy_users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT NOT NULL, display_name TEXT NOT NULL, role TEXT NOT NULL)");
            if (seedDemoUsers) {
                ensureSeedUser(connection, STUDENT_USERNAME, STUDENT_PASSWORD, STUDENT_DISPLAY_NAME, STUDENT_ROLE);
                ensureSeedUser(connection, TRAINER_USERNAME, TRAINER_PASSWORD, TRAINER_DISPLAY_NAME, TRAINER_ROLE);
            }
            migratePlaintextPasswords(connection);
        } catch (SQLException error) {
            throw new IllegalStateException("Failed to initialize authentication database", error);
        }
    }

    public UserRecord findByCredentials(String username, String password) {
        String sql = "SELECT id, username, password, display_name, role FROM legacy_users WHERE username=?";
        try (Connection connection = DriverManager.getConnection(databaseUrl);
             PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setString(1, username);
            try (ResultSet result = statement.executeQuery()) {
                if (!result.next() || !passwordHasher.matches(password, result.getString("password"))) {
                    return null;
                }

                return new UserRecord(result.getLong("id"), result.getString("username"), result.getString("display_name"), result.getString("role"));
            }
        } catch (SQLException error) {
            throw new IllegalStateException("Failed to look up user credentials", error);
        }
    }

    private void ensureSeedUser(Connection connection, String username, String password, String displayName, String role) throws SQLException {
        try (PreparedStatement findUser = connection.prepareStatement(
                "SELECT 1 FROM legacy_users WHERE username = ?")) {
            findUser.setString(1, username);
            try (ResultSet result = findUser.executeQuery()) {
                if (result.next()) {
                    return;
                }
            }
        }

        try (PreparedStatement insertUser = connection.prepareStatement(
                "INSERT INTO legacy_users(username, password, display_name, role) VALUES (?, ?, ?, ?)")) {
            insertUser.setString(1, username);
            insertUser.setString(2, passwordHasher.hash(password));
            insertUser.setString(3, displayName);
            insertUser.setString(4, role);
            insertUser.executeUpdate();
        }
    }

    private void migratePlaintextPasswords(Connection connection) throws SQLException {
        Map<Long, String> plaintextPasswords = new LinkedHashMap<>();
        try (PreparedStatement selectPasswords = connection.prepareStatement(
                "SELECT id, password FROM legacy_users");
             ResultSet result = selectPasswords.executeQuery()) {
            while (result.next()) {
                String storedPassword = result.getString("password");
                if (!passwordHasher.isEncoded(storedPassword)) {
                    plaintextPasswords.put(result.getLong("id"), storedPassword);
                }
            }
        }

        try (PreparedStatement updatePassword = connection.prepareStatement(
                "UPDATE legacy_users SET password = ? WHERE id = ?")) {
            for (Map.Entry<Long, String> entry : plaintextPasswords.entrySet()) {
                updatePassword.setString(1, passwordHasher.hash(entry.getValue()));
                updatePassword.setLong(2, entry.getKey());
                updatePassword.executeUpdate();
            }
        }
    }
}
