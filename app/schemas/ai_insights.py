from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class InsightRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=500,
        description="Question from the relationship manager about this client.",
        examples=["What risk profile does this client have based on their accounts?"],
    )


class ClientInsight(BaseModel):
    summary: str = Field(description="One-sentence summary of the client.")
    risk_profile: Literal["low", "medium", "high", "unknown"] = Field(
        description=(
            "Use unknown when the provided data is insufficient to determine the client's risk profile."
        )
    )
    key_observation: str = Field(description="Main observation based only on the provided data.")
    recommended_action: str = Field(description="Recommended action for the relationship manager.")


class ClientInsightResponse(BaseModel):
    client_id: int
    question: str
    insight: ClientInsight

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "client_id": 1,
                "question": "What risk profile does this client have based on their accounts?",
                "insight": {
                    "summary": "Active client with a savings account of 1,000 EUR.",
                    "risk_profile": "unknown",
                    "key_observation": "Account data alone is insufficient to determine risk tolerance.",
                    "recommended_action": "Collect investment objectives, horizon and risk tolerance.",
                },
            }
        }
    )
