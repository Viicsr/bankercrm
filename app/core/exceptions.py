class AppBaseException(Exception):
    """Excepción raíz de la aplicación. Todas las demás heredan de aquí."""

    status_code: int = 500
    detail: str = "Internal server error"

    def __init__(self, detail: str | None = None):
        self.detail = detail or self.__class__.detail
        super().__init__(self.detail)


class NotFoundError(AppBaseException):
    status_code = 404
    detail = "Resource not found"

    def __init__(self, resource: str, identifier: str | int):
        super().__init__(f"{resource} '{identifier}' not found")


class ConflictError(AppBaseException):
    status_code = 409
    detail = "Resource already exists"


class ForbiddenError(AppBaseException):
    status_code = 403
    detail = "Access denied"


class ValidationError(AppBaseException):
    status_code = 422
    detail = "Validation failed"


class UnauthorizedError(AppBaseException):
    status_code = 401
    detail = "Authentication required"
