Mkulima Gemma Backend API
==========================

Overview
--------

Mkulima Gemma is an offline-first backend API for a farm management and agronomy assistant. It provides a FastAPI service for activity logging, pest and disease tracking, weather caching, extension provider lookup, and RAG-backed AI agronomy recommendations.

The backend can run without external AI access, but it is designed to connect to a local Ollama model server for real-time Gemma 4 recommendations. When the Ollama endpoint is unavailable, the app returns a safe offline fallback message.

Features
--------

- FastAPI backend with SQLite persistence
- Local database of farmer activities, weather forecasts, pest/disease history, and extension contacts
- Open-Meteo weather sync and local forecast caching
- RAG prompt construction from local context
- Local Ollama integration via `http://localhost:11434/api/generate`
- Legacy and v1 API routes for compatibility
- Health check endpoint

Requirements
------------

- Python 3.11+ recommended
- Dependencies listed in `requirements.txt`
- Local Ollama installation with a supported model such as `gemma4:e2b`

Setup
-----

From the project root:

1. Create and activate a virtual environment:

   python -m venv .venv
   .\.venv\Scripts\Activate.ps1   # PowerShell
   # or .\.venv\Scripts\activate    # cmd

2. Install dependencies:

   pip install -r requirements.txt

3. Ensure the `data/` directory exists and the SQLite database can be initialized automatically at startup.

Starting the backend
--------------------

Run the FastAPI server from the project root:

   python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

The application includes automatic database initialization when it starts.

Ollama integration
------------------

By default, the backend expects Ollama at:

   http://localhost:11434/api/generate

The recommended local model is:

   gemma4:e2b

Start Ollama locally before using the RAG chat endpoints:

   ollama run gemma4:e2b

or if you are using Ollama serve:

   ollama serve

If Ollama is not available, the backend returns an offline fallback message.

API Endpoints
-------------

Base application URL:

   http://127.0.0.1:8000

Root and static content

- `/` : serves the `static/index.html` dashboard if present
- `/static` : serves static frontend assets

Health

- `GET /api/v1/health`
- `GET /api/health`

Activities

- `GET /api/v1/activities` : list activity logs
- `POST /api/v1/activities` : create an activity record
- `GET /api/v1/activities/{activity_id}` : retrieve a record
- `PUT /api/v1/activities/{activity_id}` : update a record
- `DELETE /api/v1/activities/{activity_id}` : delete a record

Weather

- `GET /api/v1/weather` : retrieve cached weather for a location
- `POST /api/v1/weather/sync` : sync forecast from Open-Meteo and cache it locally

Pest and Disease

- `GET /api/v1/pest-disease` : list pest and disease reports
- `POST /api/v1/pest-disease` : add a pest or disease report
- `GET /api/v1/pest-disease/{record_id}` : retrieve a report
- `PUT /api/v1/pest-disease/{record_id}` : update a report
- `DELETE /api/v1/pest-disease/{record_id}` : delete a report

Extension Services

- `GET /api/v1/extension-services` : search extension providers
- `POST /api/v1/extension-services` : register an extension contact
- `GET /api/v1/extension-services/{contact_id}` : retrieve a contact

RAG AI Agronomist

- `POST /api/v1/rag/chat` : send a query and receive a RAG-generated agronomy answer
- `GET /api/v1/rag/context-preview` : preview the assembled local context and prompt without invoking the model

Chat

- `POST /api/v1/chat` : legacy chat endpoint for AI agronomy recommendations

Request format for `/api/v1/chat` and `/api/v1/rag/chat`

Example:

   {
     "message": "Hello",
     "farmer_name": "Test Farmer"
   }

The chat route accepts optional fields such as `language`, `language_dialect`, `crop_name`, `crop_filter`, `location`, and `model`.

Configuration
-------------

The application reads the following environment variables:

- `DATABASE_URL` : SQLite or other SQLAlchemy database URL
- `OLLAMA_BASE_URL` : override the local Ollama endpoint (default `http://localhost:11434`)
- `OLLAMA_MODEL` : override the default model name (default `gemma4:e2b`)

Testing
-------

Run tests from the project root using pytest:

   pytest

Project layout
--------------

- `app/` : application package
  - `main.py` : FastAPI app and startup lifecycle
  - `api/` : API routers and endpoint definitions
  - `services/` : business logic for weather, RAG prompt building, and Ollama integration
  - `database.py` : SQLite initialization and session management
  - `models/` : SQLAlchemy ORM models
  - `schemas/` : Pydantic request and response models
- `data/` : persisted SQLite database and uploads
- `static/` : frontend assets
- `tests/` : automated project tests

Troubleshooting
---------------

- If the chat endpoint returns an offline fallback, confirm Ollama is running and reachable at `http://localhost:11434`.
- If weather sync fails, confirm network access to the Open-Meteo API.
- If database tables are missing, restart the backend and allow `init_db()` to create the schema.
