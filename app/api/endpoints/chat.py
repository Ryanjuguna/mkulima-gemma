"""
Legacy Chat REST API Endpoint for Mkulima Gemma.
Integrates local DB context retrieval and Ollama Gemma Engine.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse
import os
import base64
import uuid
from datetime import datetime, timezone
from app.services.rag_service import get_rag_context, build_rag_prompt
from app.services.gemma_engine import query_gemma
from app.models.pest_disease import PestDiseaseHistory

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

    # Handle image upload if present
    images_list = None
    if payload.image_base64:
        images_list = [payload.image_base64]
        try:
            # Create uploads directory if it doesn't exist
            from app.main import DATA_DIR
            uploads_dir = DATA_DIR / "uploads"
            uploads_dir.mkdir(parents=True, exist_ok=True)
            
            # Decode and save the image
            image_data = base64.b64decode(payload.image_base64)
            filename = f"chat_upload_{uuid.uuid4().hex[:8]}.jpg"
            filepath = uploads_dir / filename
            
            with open(filepath, "wb") as f:
                f.write(image_data)
                
            # Log to PestDiseaseHistory
            new_issue = PestDiseaseHistory(
                farmer_id=farmer_id,
                crop_type=crop_filter or "Unknown",
                issue_type="IMAGE_UPLOAD",
                issue_name="Image Upload from Chat",
                severity="MEDIUM",
                image_path=f"/data/uploads/{filename}",
                symptoms_description=user_query[:500],  # Truncate if too long
                status="PENDING",
            )
            db.add(new_issue)
            db.commit()
        except Exception as e:
            print(f"Failed to save uploaded image: {e}")

    # Explicitly instruct the model to look at the image if one is provided
    if images_list:
        full_prompt = (
            "[SYSTEM NOTICE: The user has attached an image of their crop. "
            "Please analyze the provided image carefully to identify any visible pests, diseases, or deficiencies. "
            "Use the visual evidence from the image to inform your diagnosis and answer the user's question.]\n\n"
            f"{full_prompt}"
        )

    llm_result = query_gemma(
        prompt=full_prompt,
        system_prompt=system_prompt,
        images=images_list,
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
