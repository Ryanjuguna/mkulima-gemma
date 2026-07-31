"""
Legacy Chat REST API Endpoint for Mkulima Gemma.
Integrates local DB context retrieval and Ollama Gemma Engine.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse
from app.services.rag_service import get_rag_context, build_rag_prompt
from app.services.gemma_engine import query_gemma

router = APIRouter()


@router.post("", response_model=ChatMessageResponse)
@router.post("/", response_model=ChatMessageResponse, include_in_schema=False)
@router.post("/chat", response_model=ChatMessageResponse, include_in_schema=False)
@router.post("/chat/", response_model=ChatMessageResponse, include_in_schema=False)
def chat_with_agronomist(
    payload: ChatMessageRequest,
    db: Session = Depends(get_db),
):
    """
    Legacy Chat Endpoint alias.
    Extracts SQLite context, formats RAG prompt, and queries Ollama Gemma engine.
    """
    user_query = payload.get_query()
    if not user_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message query cannot be empty.",
        )

    farmer_id = payload.farmer_id or payload.farmer_name or "default_farmer"
    language = payload.language or "Swahili"

    # Map language string to dialect code
    dialect = payload.language_dialect
    if not dialect:
        lang_lower = language.lower()
        if "kikuyu" in lang_lower or "gĩkũyũ" in lang_lower:
            dialect = "kik"
        elif "luo" in lang_lower or "dholuo" in lang_lower:
            dialect = "luo"
        elif "english" in lang_lower or "en" in lang_lower:
            dialect = "en"
        else:
            dialect = "sw"

    crop_filter = payload.crop_filter or payload.crop_name
    location = payload.location

    # Retrieve context
    context = get_rag_context(
        db=db,
        farmer_id=farmer_id,
        crop_filter=crop_filter,
        location=location,
    )
    context["language_dialect"] = dialect

    system_prompt, full_prompt = build_rag_prompt(
        user_query=user_query,
        context=context,
        language_dialect=dialect,
    )

    llm_result = query_gemma(
        prompt=full_prompt,
        system_prompt=system_prompt,
        model=payload.model or "gemma4:e2b",
    )

    return ChatMessageResponse(
        response=llm_result["response"],
        language=language,
        language_dialect=dialect,
        farmer_id=farmer_id,
        status="success",
        context_used=context,
        model_used=llm_result.get("model", payload.model or "gemma4:e2b"),
        augmented_prompt=full_prompt,
        is_offline=llm_result.get("is_offline", False),
    )
