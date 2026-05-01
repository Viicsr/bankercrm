from pydantic import BaseModel


class FieldError(BaseModel):
    field: str
    message: str


class ErrorResponse(BaseModel):
    error: str  # nombre de la excepción: "NotFoundError", "ConflictError"
    detail: str  # mensaje legible por humanos
    path: str  # endpoint que generó el error
    request_id: str | None = None
    errors: list[FieldError] | None = None  # solo para errores de validación


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
