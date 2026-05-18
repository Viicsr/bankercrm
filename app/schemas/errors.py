from pydantic import BaseModel, Field


class FieldError(BaseModel):
    field: str = Field(
        ...,
        description="Request field that failed validation (dot-notation for nested fields).",
        examples=["body.email"],
    )
    message: str = Field(
        ...,
        description="Human-readable description of the validation failure.",
        examples=["value is not a valid email address"],
    )


class ErrorResponse(BaseModel):
    error: str = Field(
        ...,
        description="Exception class name. Machine-readable error type.",
        examples=["NotFoundError"],
    )  # nombre de la excepción: "NotFoundError", "ConflictError"
    detail: str = Field(
        ...,
        description="Human-readable description of this specific occurrence.",
        examples=["Client '42' not found"],
    )  # mensaje legible por humanos
    path: str = Field(
        ...,
        description="Endpoint path that generated the error.",
        examples=["/api/v1/clients/42"],
    )  # endpoint que generó el error
    request_id: str | None = Field(
        None,
        description=(
            "Correlation ID from the `X-Request-ID` response header. "
            "Use this value to locate the corresponding log entry."
        ),
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    errors: list[FieldError] | None = Field(
        None,
        description="Per-field validation errors. Present only on 422 responses.",
    )  # solo para errores de validación


class HealthResponse(BaseModel):
    status: str = Field(
        ...,
        description="`ok` when all systems are healthy, `error` otherwise.",
        examples=["ok"],
    )
    version: str = Field(
        ...,
        description="Running application version.",
        examples=["0.1.0"],
    )
    environment: str = Field(
        ...,
        description="Active environment name.",
        examples=["development"],
    )
