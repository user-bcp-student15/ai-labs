package com.bcp.workshop.auth;

import jakarta.inject.Inject;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import org.jboss.logging.Logger;

import java.util.Map;

@Path("/auth")
@Consumes(MediaType.APPLICATION_JSON)
@Produces(MediaType.APPLICATION_JSON)
public class AuthResource {
    private static final Logger LOGGER = Logger.getLogger(AuthResource.class);
    private static final String REQUEST_NULL_MESSAGE = "Request is null";
    private static final String USERNAME_REQUIRED_MESSAGE = "Username is required";
    private static final String PASSWORD_REQUIRED_MESSAGE = "Password is required";
    private static final String INVALID_CREDENTIALS_MESSAGE = "Invalid user %s or password";
    private static final String INTERNAL_ERROR_MESSAGE = "Internal server error";

    @Inject
    AuthService authService;

    @POST
    @Path("/login")
    public Response login(LoginRequest request) {
        if (request == null) {
            return errorResponse(Response.Status.BAD_REQUEST, REQUEST_NULL_MESSAGE);
        }
        if (!hasText(request.username)) {
            return errorResponse(Response.Status.BAD_REQUEST, USERNAME_REQUIRED_MESSAGE);
        }
        if (!hasText(request.password)) {
            return errorResponse(Response.Status.BAD_REQUEST, PASSWORD_REQUIRED_MESSAGE);
        }

        try {
            LoginResponse response = authService.login(request.username, request.password);
            if (response == null) {
                return errorResponse(
                        Response.Status.UNAUTHORIZED,
                        INVALID_CREDENTIALS_MESSAGE.formatted(request.username)
                );
            }
            return Response.ok(response).build();
        } catch (RuntimeException error) {
            LOGGER.error("Authentication request failed", error);
            return errorResponse(Response.Status.INTERNAL_SERVER_ERROR, INTERNAL_ERROR_MESSAGE);
        }
    }

    private static boolean hasText(String value) {
        return value != null && !value.trim().isEmpty();
    }

    private static Response errorResponse(Response.Status status, String message) {
        return Response.status(status).entity(Map.of("message", message)).build();
    }
}
