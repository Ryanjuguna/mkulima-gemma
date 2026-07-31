"""
RAG AI Agronomist REST API Endpoints for Mkulima Gemma.
Provides augmented RAG chat with Gemma LLM and context preview debugging.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.rag import RAGChatRequest, RAGChatResponse, ContextPreviewResponse
from app.services.rag_service import get_rag_context, build_rag_prompt
from app.services.gemma_engine import query_gemma

router = APIRouter()


@router.post("/chat", response_model=RAGChatResponse)
@router.post("/chat/", response_model=RAGChatResponse, include_in_schema=False)
def rag_chat(
    request: RAGChatRequest,
    db: Session = Depends(get_db),
):
    """
    RAG Chat endpoint.
    Retrieves local SQLite DB context (activity logs, weather, pest history),
    assembles augmented RAG prompt with dialect rules and safety guardrails,
    and invokes Ollama Gemma client (http://localhost:11434) with offline fallback.
    """
    query_text = request.get_query()
    if not query_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query prompt or message cannot be empty.",
        )

    # 1. Retrieve DB Context
    context = get_rag_context(
        db=db,
        farmer_id=request.farmer_id,
        crop_filter=request.crop_filter,
        location=request.location,
    )
    dialect = request.language_dialect or "sw"
    context["language_dialect"] = dialect

    # 2. Build RAG Prompt
    system_prompt, full_prompt = build_rag_prompt(
        user_query=query_text,
        context=context,
        language_dialect=dialect,
    )

    # 3. Query Gemma LLM via Ollama
    llm_result = query_gemma(
        prompt=full_prompt,
        system_prompt=system_prompt,
    )

    return RAGChatResponse(
        response=llm_result["response"],
        context_used=context,
        is_offline=llm_result.get("is_offline", False),
        model=llm_result.get("model", "gemma2"),
    )


@router.get("/context-preview", response_model=ContextPreviewResponse)
@router.get("/context-preview/", response_model=ContextPreviewResponse, include_in_schema=False)
def context_preview(
    prompt: str = Query(default="Jinsi ya kupanda mahindi na kuzuia wadudu?", description="User query prompt"),
    farmer_id: str = Query(default="default_farmer", description="Farmer ID"),
    crop_filter: Optional[str] = Query(default=None, description="Optional crop filter"),
    language_dialect: str = Query(default="sw", description="Dialect: sw, en, kik, luo"),
    location: Optional[str] = Query(default=None, description="Optional location for weather"),
    db: Session = Depends(get_db),
):
    """
    Debug context preview endpoint.
    Assembles system prompt and SQLite context breakdown without calling the LLM.
    """
    context = get_rag_context(
        db=db,
        farmer_id=farmer_id,
        crop_filter=crop_filter,
        location=location,
    )
    context["language_dialect"] = language_dialect

    system_prompt, full_prompt = build_rag_prompt(
        user_query=prompt,
        context=context,
        language_dialect=language_dialect,
    )

    return ContextPreviewResponse(
        system_prompt=system_prompt,
        prompt=prompt,
        formatted_rag_prompt=full_prompt,
        context_used=context,
    )
