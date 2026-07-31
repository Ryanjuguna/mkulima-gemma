# Goal: Build "Mkulima Gemma" Prototype

This plan outlines the technical architecture and implementation strategy for Mkulima Gemma, an offline-first AI Agronomist designed for Track 3 of the GDG UoN Hackathon. It merges the initial research with the team's excellent suggestions regarding local activity logging and occasional online weather syncing.

## User Review Required

> [!IMPORTANT]
> **Platform & Tech Stack Decision**
> Before we start coding, we need to decide on the frontend and backend stack for the hackathon prototype:
> 1. **Option A (Mobile-First):** Android App (Kotlin or Flutter). We can run quantized Gemma models directly on the phone using tools like MediaPipe or MLC-LLM, with local SQLite.
> 2. **Option B (Local Web/Hub):** A local web application (Python FastAPI/Flask backend + React/HTML frontend) running on a laptop or Raspberry Pi. This acts as a "community hub" that farmers can access.
> 
> *Which approach would your team prefer to build for the hackathon? Option B is usually faster to prototype in a hackathon setting, but Option A is more true to the "edge device" vision.*

## Open Questions

> [!WARNING]
> **API Keys & Models**
> - Do you have a preferred Weather API (e.g., OpenWeatherMap, WeatherAPI) for the occasional syncing?
> - Will we be using standard Gemma 2B/7B via an API for the prototype, or do you explicitly want to run a quantized GGUF model locally on the hardware during the pitch?

## Proposed Architecture

### 1. The Local Knowledge Base (SQLite)
*   **Activity Logging:** A feature for the farmer to log daily activities (e.g., "Planted maize," "Applied 2kg DAP fertilizer," "Spotted brown spots on leaves," "Noticed aphid pests").
*   **Weather Cache:** A table to store the latest fetched weather forecasts.
*   **Pest/Disease/Weed Database:** Historical logs of identified issues, including pest infestations.

### 2. Personalized RAG (Retrieval-Augmented Generation)
*   When the farmer asks Mkulima Gemma a question, the system queries the **local SQLite database** first.
*   The LLM prompt is augmented with this local context (e.g., *System prompt context: "Farmer logged applying DAP 3 days ago. Current cached weather is expecting rain tomorrow."*).
*   This ensures Gemma's advice is highly personalized and context-aware, even when completely offline.

### 3. Opportunistic Weather Sync
*   A background worker or a manual "Sync" button that detects internet connectivity.
*   When online, it fetches a 7-day or 14-day forecast for the farmer's location and overwrites the SQLite weather cache.
*   When offline, Mkulima Gemma uses the cached data to advise on planting or harvesting times.

### 4. Extension Services & Help Directory
*   A dedicated section within the app that lists related agricultural organizations, cooperatives, and local extension service contacts.
*   The database can cache these contacts offline, and occasionally sync for updates when online, giving farmers immediate access to human experts or organizational support when AI isn't enough.

## Proposed Components

If we proceed with a **Python/Local Web App** (Option B) as an example, the structure would look like this:

### Database Layer
#### [NEW] `database.py`
Sets up the SQLite tables: `activities`, `weather_cache`, `crop_health`. Includes CRUD functions for logging.

### RAG & LLM Layer
#### [NEW] `gemma_engine.py`
Handles communication with the Gemma model. It will include a function to build the prompt by retrieving recent activities and cached weather from SQLite, appending it to the farmer's query before sending it to the LLM.

### Sync Layer
#### [NEW] `weather_sync.py`
Contains the logic to ping a weather API (if internet is available) and update the `weather_cache` table.

### Frontend Interface
#### [NEW] `app.py` or Frontend Framework
The UI where the farmer interacts in their local dialect, logs activities, views the dashboard, and browses the agricultural extension help directory.

## Verification Plan

### Manual Verification
1.  **Offline Capability:** Disconnect the device from the internet and verify that logging activities and chatting with Gemma still works using local SQLite data.
2.  **Weather Sync:** Connect to the internet, trigger the sync, disconnect, and verify Gemma can recall the forecasted weather.
3.  **Contextual Advice:** Log an activity (e.g., "Applied fertilizer today") and ask Gemma a related question to ensure the RAG system successfully feeds the SQLite log into the LLM context.
