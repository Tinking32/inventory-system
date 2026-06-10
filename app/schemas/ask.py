from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500, examples=["哪些货快过期了？"])


class AskResponse(BaseModel):
    question: str
    query_type: str
    results: list[dict]
    response_text: str
    mode: str = "mock"

    model_config = {"from_attributes": True}
