from fastapi import APIRouter
from app.api.endpoints import activities, weather, pest_disease, extension, health, chat, rag

api_router = APIRouter()

# API v1 routes
api_router.include_router(activities.router, prefix="/api/v1/activities", tags=["Activities"])
api_router.include_router(weather.router, prefix="/api/v1/weather", tags=["Weather"])
api_router.include_router(pest_disease.router, prefix="/api/v1/pest-disease", tags=["Pest & Disease"])
api_router.include_router(extension.router, prefix="/api/v1/extension-services", tags=["Extension Services"])
api_router.include_router(extension.router, prefix="/api/v1/extensions", tags=["Extension Services Alias"], include_in_schema=False)
api_router.include_router(rag.router, prefix="/api/v1/rag", tags=["RAG AI Agronomist"])
api_router.include_router(chat.router, prefix="/api/v1/chat", tags=["AI Chat"])
api_router.include_router(health.router, prefix="/api/v1/health", tags=["Health"])

# Root / legacy route aliases for backward compatibility
api_router.include_router(activities.router, prefix="/api/activities", tags=["Legacy Activities"], include_in_schema=False)
api_router.include_router(weather.router, prefix="/api/weather", tags=["Legacy Weather"], include_in_schema=False)
api_router.include_router(pest_disease.router, prefix="/api/pest-disease", tags=["Legacy Pest & Disease"], include_in_schema=False)
api_router.include_router(pest_disease.router, prefix="/api/pests", tags=["Legacy Pests Alias"], include_in_schema=False)
api_router.include_router(extension.router, prefix="/api/extension-services", tags=["Legacy Extension Services"], include_in_schema=False)
api_router.include_router(extension.router, prefix="/api/extensions", tags=["Legacy Extensions Alias"], include_in_schema=False)
api_router.include_router(rag.router, prefix="/api/rag", tags=["Legacy RAG Alias"], include_in_schema=False)
api_router.include_router(chat.router, prefix="/api/chat", tags=["Legacy Chat Alias"], include_in_schema=False)
api_router.include_router(chat.router, prefix="/api", tags=["Chat"], include_in_schema=False)
api_router.include_router(health.router, prefix="/api/health", tags=["Legacy Health"], include_in_schema=False)


