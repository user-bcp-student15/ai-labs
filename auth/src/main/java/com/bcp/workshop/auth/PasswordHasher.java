package com.bcp.workshop.auth;

import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;
import java.security.GeneralSecurityException;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.Base64;

final class PasswordHasher {
    static final String ENCODED_PREFIX = "pbkdf2-sha256$";

    private static final String ALGORITHM = "PBKDF2WithHmacSHA256";
    private static final String FORMAT_NAME = "pbkdf2-sha256";
    private static final String SEPARATOR = "$";
    private static final int ITERATION_COUNT = 600_000;
    private static final int SALT_LENGTH_BYTES = 16;
    private static final int KEY_LENGTH_BITS = 256;
    private static final int HASH_LENGTH_BYTES = KEY_LENGTH_BITS / Byte.SIZE;

    private final SecureRandom secureRandom = new SecureRandom();

    String hash(String password) {
        if (password == null) {
            throw new IllegalArgumentException("Password is required");
        }

        byte[] salt = new byte[SALT_LENGTH_BYTES];
        secureRandom.nextBytes(salt);
        byte[] derivedKey = deriveKey(password, salt, ITERATION_COUNT);

        return FORMAT_NAME + SEPARATOR
                + ITERATION_COUNT + SEPARATOR
                + Base64.getEncoder().encodeToString(salt) + SEPARATOR
                + Base64.getEncoder().encodeToString(derivedKey);
    }

    boolean matches(String password, String encodedPassword) {
        if (password == null || encodedPassword == null) {
            return false;
        }

        String[] fields = encodedPassword.split("\\$", -1);
        if (fields.length != 4 || !FORMAT_NAME.equals(fields[0])) {
            return false;
        }

        try {
            int iterations = Integer.parseInt(fields[1]);
            byte[] salt = Base64.getDecoder().decode(fields[2]);
            byte[] expectedKey = Base64.getDecoder().decode(fields[3]);
            if (iterations <= 0 || iterations > ITERATION_COUNT
                    || salt.length != SALT_LENGTH_BYTES
                    || expectedKey.length != HASH_LENGTH_BYTES) {
                return false;
            }

            byte[] actualKey = deriveKey(password, salt, iterations);
            return MessageDigest.isEqual(expectedKey, actualKey);
        } catch (IllegalArgumentException error) {
            return false;
        }
    }

    boolean isEncoded(String value) {
        if (value == null || !value.startsWith(ENCODED_PREFIX)) {
            return false;
        }

        String[] fields = value.split("\\$", -1);
        if (fields.length != 4 || !FORMAT_NAME.equals(fields[0])) {
            return false;
        }

        try {
            int iterations = Integer.parseInt(fields[1]);
            byte[] salt = Base64.getDecoder().decode(fields[2]);
            byte[] hash = Base64.getDecoder().decode(fields[3]);
            return iterations > 0 && iterations <= ITERATION_COUNT
                    && salt.length == SALT_LENGTH_BYTES
                    && hash.length == HASH_LENGTH_BYTES;
        } catch (IllegalArgumentException error) {
            return false;
        }
    }

    private static byte[] deriveKey(String password, byte[] salt, int iterations) {
        PBEKeySpec keySpec = new PBEKeySpec(password.toCharArray(), salt, iterations, KEY_LENGTH_BITS);
        try {
            return SecretKeyFactory.getInstance(ALGORITHM).generateSecret(keySpec).getEncoded();
        } catch (GeneralSecurityException error) {
            throw new IllegalStateException("Password hashing is unavailable", error);
        } finally {
            keySpec.clearPassword();
        }
    }
}
