"""
RAG Service Module for Mkulima Gemma
Retrieves local SQLite context (activities, pest logs, weather) and calls Ollama API at http://localhost:11434.
"""

import httpx
from typing import Dict, Any, Optional
from app.database import (
    get_activities,
    get_pest_records,
    get_weather_cache,
    DEFAULT_DB_PATH
)

OLLAMA_GENERATE_URL = "http://localhost:11434/api/generate"


def retrieve_context(
    farmer_name: Optional[str] = None,
    crop_name: Optional[str] = None,
    location: str = "Nairobi",
    db_path: str = DEFAULT_DB_PATH
) -> Dict[str, Any]:
    """Extract context from SQLite database for RAG prompt augmentation."""
    activities = get_activities(farmer_name=farmer_name, limit=5, db_path=db_path)
    pest_records = get_pest_records(crop_name=crop_name, limit=5, db_path=db_path)
    weather = get_weather_cache(location=location, db_path=db_path)

    return {
        "farmer_name": farmer_name,
        "location": location,
        "activities": activities,
        "pest_records": pest_records,
        "weather": weather
    }


def format_rag_prompt(user_prompt: str, context: Dict[str, Any]) -> str:
    """Combine context retrieved from SQLite with the farmer's prompt."""
    context_sections = []

    if context.get("farmer_name"):
        context_sections.append(f"Farmer Name: {context['farmer_name']}")

    # Cached Weather
    weather = context.get("weather")
    if weather:
        context_sections.append(
            f"Cached Weather ({weather.get('location', 'Nairobi')}): "
            f"Temp: {weather.get('temperature')}°C, Humidity: {weather.get('humidity')}%, "
            f"Precipitation: {weather.get('precipitation')}mm. Forecast: {weather.get('forecast')}"
        )
    else:
        context_sections.append("Cached Weather: No weather data cached yet.")

    # Recent Activities
    activities = context.get("activities", [])
    if activities:
        act_summary = "; ".join(
            [f"[{a.get('timestamp')}] {a.get('activity_type')} on {a.get('crop_type')}: {a.get('details')}" for a in activities]
        )
        context_sections.append(f"Recent Farm Activities: {act_summary}")

    # Pest Records
    pests = context.get("pest_records", [])
    if pests:
        pest_summary = "; ".join(
            [f"[{p.get('logged_at')}] {p.get('crop_name')} issue: {p.get('issue_name')} - Treatment: {p.get('treatment')}" for p in pests]
        )
        context_sections.append(f"Pest/Disease History: {pest_summary}")

    context_str = "\n".join(context_sections)

    augmented_prompt = (
        f"You are Mkulima Gemma, an expert offline AI Agronomist for small-scale farmers in Kenya.\n"
        f"--- LOCAL FARMER CONTEXT FROM SQLITE ---\n"
        f"{context_str}\n"
        f"----------------------------------------\n"
        f"FARMER QUESTION: {user_prompt}\n"
        f"Provide personalized, safe, and practical agricultural advice based on the above context."
    )
    return augmented_prompt


async def generate_rag_response(
    prompt: str,
    farmer_name: Optional[str] = None,
    crop_name: Optional[str] = None,
    location: str = "Nairobi",
    db_path: str = DEFAULT_DB_PATH,
    ollama_url: str = OLLAMA_GENERATE_URL,
    model: str = "gemma4:e2b"
) -> Dict[str, Any]:
    """Retrieve SQLite context, format augmented prompt, and query Ollama API."""
    context = retrieve_context(farmer_name=farmer_name, crop_name=crop_name, location=location, db_path=db_path)
    augmented_prompt = format_rag_prompt(prompt, context)

    payload = {
        "model": model,
        "prompt": augmented_prompt,
        "stream": False
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(ollama_url, json=payload)
        response.raise_for_status()
        ollama_data = response.json()

    ai_response = ollama_data.get("response", "No response received from model.")

    return {
        "response": ai_response,
        "augmented_prompt": augmented_prompt,
        "context_used": context,
        "model_used": model
    }
