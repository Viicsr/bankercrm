# 401 — Authentication required (token missing, invalid or expired)
AUTH_401_CONTENT = {
    "application/json": {
        "example": {
            "error": "AuthenticationError",
            "detail": "Authentication credentials were not provided or are invalid.",
            "path": "/api/v1/...",
            "request_id": "550e8400-e29b-41d4-a716-446655440000",
            "errors": None,
        }
    }
}

# 401 variant specific to /auth/login — wrong email or password
AUTH_401_CREDENTIALS_CONTENT = {
    "application/json": {
        "example": {
            "error": "AuthenticationError",
            "detail": "Invalid email or password.",
            "path": "/api/v1/auth/login",
            "request_id": "550e8400-e29b-41d4-a716-446655440000",
            "errors": None,
        }
    }
}

# 401 variant specific to /auth/refresh — token expired or already rotated
AUTH_401_TOKEN_CONTENT = {
    "application/json": {
        "example": {
            "error": "AuthenticationError",
            "detail": "Refresh token has expired or has already been used.",
            "path": "/api/v1/auth/refresh",
            "request_id": "550e8400-e29b-41d4-a716-446655440000",
            "errors": None,
        }
    }
}

# 403 — Authorisation failure (authenticated but wrong role)
AUTH_403_CONTENT = {
    "application/json": {
        "example": {
            "error": "AuthorizationError",
            "detail": "Role 'read_only' is not allowed to perform this action.",
            "path": "/api/v1/...",
            "request_id": "550e8400-e29b-41d4-a716-446655440000",
            "errors": None,
        }
    }
}

# 404 — Resource not found (one dict per resource type)
CLIENT_404_CONTENT = {
    "application/json": {
        "example": {
            "error": "NotFoundError",
            "detail": "Client '42' not found.",
            "path": "/api/v1/clients/42",
            "request_id": "550e8400-e29b-41d4-a716-446655440000",
            "errors": None,
        }
    }
}

# Used by POST /accounts — the client linked to the new account does not exist
CLIENT_FOR_ACCOUNT_404_CONTENT = {
    "application/json": {
        "example": {
            "error": "NotFoundError",
            "detail": "Client '7' not found or is inactive.",
            "path": "/api/v1/accounts",
            "request_id": "550e8400-e29b-41d4-a716-446655440000",
            "errors": None,
        }
    }
}

ACCOUNT_404_CONTENT = {
    "application/json": {
        "example": {
            "error": "NotFoundError",
            "detail": "Account '15' not found.",
            "path": "/api/v1/accounts/15",
            "request_id": "550e8400-e29b-41d4-a716-446655440000",
            "errors": None,
        }
    }
}

# 409 — Conflict (one dict per conflict type)
CLIENT_EMAIL_409_CONTENT = {
    "application/json": {
        "example": {
            "error": "ConflictError",
            "detail": "A client with email 'maria.garcia@banco.es' already exists.",
            "path": "/api/v1/clients",
            "request_id": "550e8400-e29b-41d4-a716-446655440000",
            "errors": None,
        }
    }
}

ACCOUNT_NUMBER_409_CONTENT = {
    "application/json": {
        "example": {
            "error": "ConflictError",
            "detail": "Account number 'ES9121000418450200051332' already exists.",
            "path": "/api/v1/accounts",
            "request_id": "550e8400-e29b-41d4-a716-446655440000",
            "errors": None,
        }
    }
}

USER_EMAIL_409_CONTENT = {
    "application/json": {
        "example": {
            "error": "ConflictError",
            "detail": "A user with email 'admin@banco.es' already exists.",
            "path": "/api/v1/auth/register",
            "request_id": "550e8400-e29b-41d4-a716-446655440000",
            "errors": None,
        }
    }
}
