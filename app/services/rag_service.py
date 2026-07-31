"""
RAG Context Retrieval and Augmented Prompt Service for Mkulima Gemma.
Extracts context from local SQLite database (activities, weather, pest history)
and constructs structured prompts with dialect instructions and safety guardrails.
"""

from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from app.models.activity import FarmerActivityLog
from app.models.weather import WeatherCache
from app.models.pest_disease import PestDiseaseHistory

DIALECT_MAP: Dict[str, str] = {
    "sw": "sw",
    "swahili": "sw",
    "kiswahili": "sw",
    "en": "en",
    "english": "en",
    "kik": "kik",
    "kikuyu": "kik",
    "gĩkũyũ": "kik",
    "gikuyu": "kik",
    "luo": "luo",
    "dholuo": "luo",
}

DIALECT_INSTRUCTIONS: Dict[str, str] = {
    "sw": (
        "Wewe ni Afisa Kilimo (AI Agronomist) mtaalamu wa Mkulima Gemma. "
        "Jibu maswali kwa Kiswahili fasaha, rahisi, na chenye msaada kwa mkulima wa Afrika Mashariki."
    ),
    "en": (
        "You are an expert AI Agronomist for East African farmers (Mkulima Gemma). "
        "Provide clear, practical, evidence-based agronomy recommendations in English."
    ),
    "kik": (
        "Wewe ni Afisa Kilimo mtaalamu wa Mkulima Gemma. "
        "Jibu kwa lugha ya Gĩkũyũ (Kikuyu) na Kiswahili ukimpa mkulima ushauri bora wa urimi."
    ),
    "luo": (
        "Wewe ni Afisa Kilimo mtaalamu wa Mkulima Gemma. "
        "Jibu kwa lugha ya Dholuo (Luo) na Kiswahili ukimpa mkulima ushauri bora wa pur."
    ),
}

CHEMICAL_SAFETY_GUARDRAILS = (
    "CHEMICAL SAFETY & ADVISORY GUARDRAILS:\n"
    "1. When recommending chemical pesticides, fungicides, or herbicides, specify active ingredients, exact dosage, and required Personal Protective Equipment (PPE).\n"
    "2. MANDATORY: Highlight Pre-Harvest Intervals (PHI), re-entry intervals, and safe disposal of chemical containers.\n"
    "3. Prioritize Integrated Pest Management (IPM) and organic eco-friendly solutions (such as neem extract, ash, crop rotation) alongside or prior to chemical use."
)


def get_rag_context(
    db: Session,
    farmer_id: Optional[str] = None,
    crop_filter: Optional[str] = None,
    location: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieves relevant context from local SQLite database:
    - Top 5 recent farmer activity logs
    - 3-day weather cache forecast for location
    - Active pest and disease history records
    """
    # 1. Farmer Activity Logs (top 5)
    act_query = db.query(FarmerActivityLog)
    if farmer_id and farmer_id not in ["all", "default_farmer"]:
        act_query = act_query.filter(FarmerActivityLog.farmer_id.ilike(f"%{farmer_id}%"))
    if crop_filter and crop_filter != "All Crops":
        act_query = act_query.filter(FarmerActivityLog.crop_type.ilike(f"%{crop_filter}%"))
    
    activity_records = (
        act_query.order_by(FarmerActivityLog.logged_at.desc(), FarmerActivityLog.id.desc())
        .limit(5)
        .all()
    )

    activities_list = []
    for a in activity_records:
        activities_list.append({
            "id": a.id,
            "farmer_id": a.farmer_id,
            "activity_type": a.activity_type,
            "crop_type": a.crop_type,
            "description": a.description,
            "quantity": a.quantity,
            "unit": a.unit,
            "field_location": a.field_location,
            "notes": a.notes,
            "logged_at": a.logged_at.isoformat() if a.logged_at else None,
        })

    # 2. Weather Cache (3-day forecast)
    weather_query = db.query(WeatherCache)
    if location:
        weather_query = weather_query.filter(WeatherCache.location_name.ilike(f"%{location}%"))
    
    weather_records = (
        weather_query.order_by(WeatherCache.forecast_date.asc(), WeatherCache.id.asc())
        .limit(3)
        .all()
    )

    weather_list = []
    for w in weather_records:
        weather_list.append({
            "id": w.id,
            "location_name": w.location_name,
            "forecast_date": str(w.forecast_date) if w.forecast_date else None,
            "temp_min_c": w.temp_min_c,
            "temp_max_c": w.temp_max_c,
            "condition_text": w.condition_text,
            "precipitation_mm": w.precipitation_mm,
            "humidity_pct": w.humidity_pct,
            "wind_speed_kmh": w.wind_speed_kmh,
        })

    # 3. Active Pest & Disease History
    pest_query = db.query(PestDiseaseHistory).filter(PestDiseaseHistory.status == "ACTIVE")
    if farmer_id and farmer_id != "all":
        pest_query = pest_query.filter(PestDiseaseHistory.farmer_id == farmer_id)
    if crop_filter:
        pest_query = pest_query.filter(PestDiseaseHistory.crop_type.ilike(f"%{crop_filter}%"))
    
    pest_records = (
        pest_query.order_by(PestDiseaseHistory.detected_at.desc(), PestDiseaseHistory.id.desc())
        .limit(5)
        .all()
    )

    pest_list = []
    for p in pest_records:
        pest_list.append({
            "id": p.id,
            "farmer_id": p.farmer_id,
            "crop_type": p.crop_type,
            "issue_type": p.issue_type,
            "issue_name": p.issue_name,
            "severity": p.severity,
            "symptoms_description": p.symptoms_description,
            "recommended_treatment": p.recommended_treatment,
            "status": p.status,
            "detected_at": p.detected_at.isoformat() if p.detected_at else None,
        })

    return {
        "farmer_id": farmer_id or "default_farmer",
        "crop_filter": crop_filter,
        "location": location,
        "farmer_activity_logs": activities_list,
        "weather_cache": weather_list,
        "pest_disease_history": pest_list,
    }


def build_rag_prompt(
    user_query: str,
    context: Dict[str, Any],
    language_dialect: str = "sw",
) -> Tuple[str, str]:
    """
    Assembles augmented RAG system prompt and full user prompt string.
    Combines dialect rules, chemical safety rules, retrieved SQLite context, and user query.
    Returns tuple: (system_prompt, formatted_full_prompt)
    """
    dialect_raw = (language_dialect or "sw").lower().strip()
    dialect_code = DIALECT_MAP.get(dialect_raw, "sw")
    dialect_instruction = DIALECT_INSTRUCTIONS.get(
        dialect_code,
        DIALECT_INSTRUCTIONS["sw"]
    )

    system_prompt = (
        f"{dialect_instruction}\n\n"
        f"{CHEMICAL_SAFETY_GUARDRAILS}"
    )

    # Format activities section
    activities = context.get("farmer_activity_logs", [])
    if activities:
        act_lines = []
        for a in activities:
            date_str = a.get("logged_at") or "Recent"
            desc = a.get("description") or "Logged activity"
            act_lines.append(
                f"- [{date_str}] {a.get('crop_type')} ({a.get('activity_type')}): {desc} "
                f"({a.get('quantity') or ''} {a.get('unit') or ''}, {a.get('field_location') or ''})".strip()
            )
        act_text = "\n".join(act_lines)
    else:
        act_text = "No recent farmer activities found in local database."

    # Format weather section
    weather_entries = context.get("weather_cache", [])
    if weather_entries:
        weather_lines = []
        for w in weather_entries:
            weather_lines.append(
                f"- Location: {w.get('location_name')} | Date: {w.get('forecast_date')} | "
                f"Temp: {w.get('temp_min_c')}°C - {w.get('temp_max_c')}°C | "
                f"Condition: {w.get('condition_text')} | Rain: {w.get('precipitation_mm')}mm | "
                f"Humidity: {w.get('humidity_pct')}%"
            )
        weather_text = "\n".join(weather_lines)
    else:
        weather_text = "No weather forecast data cached in local database."

    # Format pest & disease section
    pests = context.get("pest_disease_history", [])
    if pests:
        pest_lines = []
        for p in pests:
            pest_lines.append(
                f"- Crop: {p.get('crop_type')} | {p.get('issue_type')}: {p.get('issue_name')} "
                f"[Severity: {p.get('severity')}] | Symptoms: {p.get('symptoms_description')} | "
                f"Treatment: {p.get('recommended_treatment') or 'Pending'}"
            )
        pest_text = "\n".join(pest_lines)
    else:
        pest_text = "No active pest/disease threats recorded in local database."

    farmer_id = context.get("farmer_id") or "default_farmer"
    crop_filter = context.get("crop_filter") or "All Crops"

    formatted_full_prompt = (
        f"--- LOCAL FARM DATABASE CONTEXT ---\n"
        f"Farmer ID: {farmer_id}\n"
        f"Crop Context: {crop_filter}\n\n"
        f"1. RECENT FARMER ACTIVITIES (Top 5):\n{act_text}\n\n"
        f"2. WEATHER FORECAST (3-Day):\n{weather_text}\n\n"
        f"3. ACTIVE PEST & DISEASE THREATS:\n{pest_text}\n\n"
        f"--- FARMER QUESTION / QUERY ---\n"
        f"{user_query}\n\n"
        f"--- AGRONOMIST RECOMMENDATION ---"
    )

    return system_prompt, formatted_full_prompt
