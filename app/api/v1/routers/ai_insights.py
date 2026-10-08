from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_roles
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.ai_insights import ClientInsightResponse, InsightRequest
from app.schemas.error_examples import (
    AUTH_401_CONTENT,
    AUTH_403_CONTENT,
    CLIENT_404_CONTENT,
)
from app.schemas.errors import ErrorResponse
from app.services.ai_insight_service import AIInsightService

router = APIRouter(prefix="/ai", tags=["AI Insights"])

_auth_responses = {
    401: {
        "model": ErrorResponse,
        "description": "Authentication required",
        "content": AUTH_401_CONTENT,
    },
    403: {
        "model": ErrorResponse,
        "description": "Insufficient permissions",
        "content": AUTH_403_CONTENT,
    },
}


@router.post(
    "/clients/{client_id}/insights",
    response_model=ClientInsightResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate client insight",
    description="""
Ask an internal LLM analyst about a client using **only** CRM data
(name, status, and accounts). The model must not invent balances,
products, or personal details.

Requires `admin` or `analyst` role. Calls OpenAI (`OPENAI_API_KEY`).
    """,
    responses={
        200: {"description": "Structured insight generated from CRM data"},
        404: {
            "model": ErrorResponse,
            "description": "Client not found",
            "content": CLIENT_404_CONTENT,
        },
        422: {"description": "Validation error — empty or too long question"},
        502: {
            "model": ErrorResponse,
            "description": "AI provider unavailable or not configured",
            "content": {
                "application/json": {
                    "example": {
                        "error": "AIServiceError",
                        "detail": "AI provider unavailable",
                        "path": "/api/v1/ai/clients/1/insights",
                        "request_id": "550e8400-e29b-41d4-a716-446655440000",
                        "errors": None,
                    }
                }
            },
        },
        **_auth_responses,
    },
)
async def get_client_insight(
    client_id: int,
    request: InsightRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ANALYST)),
) -> ClientInsightResponse:
    return await AIInsightService(db).get_client_insight(client_id, request.question)
