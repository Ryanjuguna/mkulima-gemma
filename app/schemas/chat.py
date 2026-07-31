from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    message: Optional[str] = Field(default=None, description="User query or question for AI Agronomist")
    prompt: Optional[str] = Field(default=None, description="User query or question prompt")
    language: Optional[str] = Field(default="Swahili", description="Target language: English, Swahili, Kikuyu, Luo")
    language_dialect: Optional[str] = Field(default=None, description="Target language dialect code")
    farmer_id: Optional[str] = Field(default="default_farmer", description="Farmer ID for context lookup")
    farmer_name: Optional[str] = Field(default=None, description="Farmer name")
    crop_name: Optional[str] = Field(default=None, description="Crop name")
    crop_filter: Optional[str] = Field(default=None, description="Crop filter")
    location: Optional[str] = Field(default=None, description="Location")
    model: Optional[str] = Field(default="gemma2", description="LLM model name")

    def get_query(self) -> str:
        return (self.message or self.prompt or "").strip()


class ChatMessageResponse(BaseModel):
    response: str = Field(..., description="Generated agronomy answer")
    language: str = Field(default="Swahili", description="Language used for response")
    language_dialect: Optional[str] = Field(default="sw", description="Language dialect code")
    farmer_id: str = Field(default="default_farmer", description="Farmer ID")
    status: str = Field(default="success", description="Status of chat response")
    context_used: Optional[Dict[str, Any]] = Field(default=None, description="Context retrieved from SQLite DB")
    model_used: Optional[str] = Field(default="gemma2", description="LLM model used")
    augmented_prompt: Optional[str] = Field(default=None, description="Full formatted RAG prompt")
    is_offline: Optional[bool] = Field(default=False, description="Offline status flag")
