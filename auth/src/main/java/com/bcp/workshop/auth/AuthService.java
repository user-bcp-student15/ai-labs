package com.bcp.workshop.auth;

import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@ApplicationScoped
public class AuthService {
    @Inject
    LegacyDatabase database;

    @Inject
    LegacyTokenUtil tokenUtil;

    public LoginResponse login(String username, String password) {
        UserRecord user = database.findByCredentials(username, password);
        if (user == null) {
            return null;
        }

        String token = tokenUtil.create(user.username(), user.role());
        return LoginResponse.from(user, token);
    }
}
