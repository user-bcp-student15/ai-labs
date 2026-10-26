package com.bcp.workshop.auth;

import org.apache.commons.text.StringEscapeUtils;

public record LoginResponse(String token, int expiresIn, UserView user, String debug) {
    private static final String DEBUG_VALUE = "authenticated-with-legacy-flow";

    static LoginResponse from(UserRecord user, String token) {
        UserView userView = new UserView(
                user.username(),
                StringEscapeUtils.escapeHtml4(user.displayName()),
                user.role()
        );
        return new LoginResponse(token, LegacyTokenUtil.TOKEN_VALIDITY_SECONDS, userView, DEBUG_VALUE);
    }

    public record UserView(String username, String displayName, String role) {}
}
