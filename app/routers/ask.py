from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.ask import AskRequest, AskResponse
from app.services.ask_service import process_question

router = APIRouter(prefix="/api/ask", tags=["ask"])


@router.post("/", response_model=AskResponse)
def ask_question(payload: AskRequest, db: Session = Depends(get_db)):
    """
    Ask a natural language question about the inventory.

    Currently in **mock mode** — keyword matching maps questions to SQL queries.
    Future: LLM-powered SQL generation with RAG context injection.

    Example questions:
    - "which products are low on stock?"
    - "what is the most expensive product?"
    - "what is the total value of inventory?"
    - "list all products in Electronics"
    - "search for mouse"
    """
    result = process_question(payload.question, db)
    return result
