"""
Gemma Engine Service for Mkulima Gemma Backend.
Ollama API Client pointing to http://localhost:11434 with offline fallback.
"""

import os
import logging
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e2b")

OFFLINE_AGRONOMIST_MESSAGE = (
    "Mkulima AI Agronomist is currently running in offline fallback mode. "
    "The local Ollama LLM endpoint (http://localhost:11434) is offline or unreachable. "
    "Please ensure Ollama service is running locally with 'ollama run gemma4:e2b' or 'ollama serve' "
    "to receive real-time Gemma 4 agronomy recommendations."
)



def query_gemma(
    prompt: str,
    system_prompt: Optional[str] = None,
    images: Optional[list[str]] = None,
    model: str = DEFAULT_MODEL,
    base_url: str = OLLAMA_BASE_URL,
    timeout: float = 60.0,
) -> Dict[str, Any]:
    """
    Sends prompt request to Ollama API POST http://localhost:11434/api/generate.
    Handles offline connection failures gracefully and returns helpful fallback response.
    """
    url = f"{base_url.rstrip('/')}/api/generate"
    target_model = model or DEFAULT_MODEL

    payload = {
        "model": target_model,
        "prompt": prompt,
        "stream": False,
    }
    if system_prompt:
        payload["system"] = system_prompt
    if images:
        payload["images"] = images

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, json=payload)

        if response.status_code == 200:
            data = response.json()
            generated_text = data.get("response", "").strip()
            return {
                "response": generated_text or OFFLINE_AGRONOMIST_MESSAGE,
                "model": target_model,
                "status": "success",
                "is_offline": False,
            }
        else:
            logger.warning(f"Ollama returned status {response.status_code}: {response.text[:200]}")
            return {
                "response": OFFLINE_AGRONOMIST_MESSAGE,
                "model": target_model,
                "status": "offline",
                "is_offline": True,
            }
    except Exception as exc:
        logger.info(f"Ollama API unreachable at {url}: {exc}")
        return {
            "response": OFFLINE_AGRONOMIST_MESSAGE,
            "model": target_model,
            "status": "offline",
            "is_offline": True,
        }

