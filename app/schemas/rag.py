from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class RAGChatRequest(BaseModel):
    prompt: Optional[str] = Field(None, description="User query or prompt for AI Agronomist")
    message: Optional[str] = Field(None, description="Alias for prompt")
    farmer_id: Optional[str] = Field("default_farmer", description="Farmer ID for context lookup")
    crop_filter: Optional[str] = Field(None, description="Optional crop filter for context retrieval")
    language_dialect: Optional[str] = Field("sw", description="Dialect selection: sw, en, kik, luo")
    location: Optional[str] = Field(None, description="Optional location for weather context lookup")

    def get_query(self) -> str:
        return (self.prompt or self.message or "").strip()


class RAGChatResponse(BaseModel):
    response: str = Field(..., description="Generated recommendation from Ollama / Offline Gemma AI Agronomist")
    context_used: Dict[str, Any] = Field(default_factory=dict, description="Context extracted from local SQLite database")
    is_offline: bool = Field(False, description="True if response came from offline fallback mode")
    model: str = Field("gemma2", description="Ollama model used for response generation")


class ContextPreviewResponse(BaseModel):
    system_prompt: str = Field(..., description="Assembled system prompt with dialect instructions and safety rules")
    prompt: str = Field(..., description="User query prompt")
    formatted_rag_prompt: str = Field(..., description="Full RAG prompt built for LLM generation")
    context_used: Dict[str, Any] = Field(..., description="Breakdown of SQLite context retrieved")
