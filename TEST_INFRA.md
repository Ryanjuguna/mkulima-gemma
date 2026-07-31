# TEST INFRASTRUCTURE & STRATEGY DOCUMENT (`TEST_INFRA.md`)
**Project:** Mkulima Gemma — Offline-First AI Agronomist for Small-Scale Farmers  
**Target Directory:** `c:\Users\ryanj\Documents\GDG-Gemma-Hack\mkulima-gemma`  
**Test Harness Entrypoint:** `tests/test_app.py`  
**Test Runner:** `pytest tests/test_app.py -v`  

---

## 1. Test Philosophy

The testing philosophy for **Mkulima Gemma** is built on four core tenets:

1. **Genuine Behavior Verification**: No shortcut mocks or hardcoded test returns. All database schemas, FastAPI routes, RAG prompt augmentations, and async operations execute real application logic.
2. **Network Isolation for Offline Reliability**: Because Mkulima Gemma is designed to work in low-connectivity rural settings, external REST APIs (Open-Meteo weather service and local Ollama server at `http://localhost:11434`) are isolated using deterministic network mocks during end-to-end test execution.
3. **Multi-Tier Coverage Hierarchy**: Tests are structured across 4 distinct tiers—from unit table integrity to complete multi-step farmer workflows.
4. **Resilience & Local Dialect Integrity**: Agriculture in Kenya requires supporting local terminology (e.g., Swahili / Kikuyu farming inputs), edge cases (missing data, non-existent weather locations), and strict schema constraints.

---

## 2. Feature Inventory (R1–R4)

| Requirement ID | Feature Name | Description | Key Modules Tested |
|----------------|--------------|-------------|--------------------|
| **R1** | **Database Schema & Integrity** | SQLite database initialization and table schema integrity for all 4 domain tables (`farmer_activity_logs`, `weather_cache`, `pest_disease_history`, `extension_directory`). Verifies table existence, datatypes, column constraints, and ON CONFLICT upsert behavior. | `app/database.py` |
| **R2** | **Backend CRUD Operations via REST API** | Full RESTful API CRUD endpoints (`/api/activities`, `/api/pests`, `/api/extension-services`, `/api/weather`). Verifies creation, retrieval, parameter filtering, and HTTP validation error handling. | `app/main.py`, `app/database.py` |
| **R3** | **Weather Sync Service** | Keyless weather sync integrating Open-Meteo REST API (`https://api.open-meteo.com/v1/forecast`) with SQLite caching logic. Mocks HTTP response and verifies parsing, forecast text generation, and DB table updates. | `app/weather_service.py`, `app/main.py` |
| **R4** | **Offline RAG & Ollama AI Agronomist** | Context retrieval from SQLite (recent activities, pest history, cached weather), prompt formatting into augmented RAG instructions, and network invocation targeting Ollama API at `http://localhost:11434/api/generate`. | `app/rag_service.py`, `app/main.py` |

---

## 3. Test Architecture

```
                                  +---------------------------------------+
                                  |     Pytest Runner / Test Suite        |
                                  |        (tests/test_app.py)            |
                                  +-------------------+-------------------+
                                                      |
                                   +------------------+------------------+
                                   |                                     |
                         [FastAPI TestClient]                 [Direct DB & RAG Unit]
                                   |                                     |
                                   v                                     v
                       +-----------------------+             +-----------------------+
                       |   app.main REST API   |             |   app.database SQLite |
                       +-----------+-----------+             |    (Isolated Temp DB) |
                                   |                         +-----------------------+
                +------------------+------------------+
                |                                     |
                v                                     v
    +-----------------------+             +-----------------------+
    | app.weather_service   |             |    app.rag_service    |
    | (Open-Meteo Sync)     |             |  (Ollama RAG Engine)  |
    +-----------+-----------+             +-----------+-----------+
                |                                     |
    [Mocked Open-Meteo API]                [Mocked Ollama API]
    (https://api.open-meteo.com)           (http://localhost:11434)
```

### Key Components:
- **Test Suite (`tests/test_app.py`)**: 14 test functions spanning Tier 1 to Tier 4.
- **Fixtures (`temp_db`, `client`)**: Uses temporary, isolated SQLite databases (`tempfile.mkstemp()`) for each test to guarantee thread safety and clean state.
- **Network Mocks**: Utilizes `unittest.mock.patch` to intercept `httpx.AsyncClient` calls targeting Open-Meteo and `http://localhost:11434/api/generate`.

---

## 4. Coverage Goals Across Tiers 1–4

### Tier 1: Feature Coverage (Unit & Direct REST CRUD)
- **Goal**: 100% endpoint and database table schema verification.
- **Test Cases**:
  - `test_tier1_database_schema_creation_and_integrity`: Validates schema creation for all 4 tables.
  - `test_tier1_direct_db_crud_operations`: Validates direct Python database functions.
  - `test_tier1_rest_api_health_check`: Verifies `GET /api/health`.
  - `test_tier1_rest_api_activities_crud`: Verifies `POST /api/activities` and `GET /api/activities`.
  - `test_tier1_rest_api_pests_crud`: Verifies `POST /api/pests` and `GET /api/pests`.
  - `test_tier1_rest_api_extension_services_crud`: Verifies `POST /api/extension-services` and `GET /api/extension-services`.

### Tier 2: Boundary & Corner Cases
- **Goal**: Ensure robust error handling, invalid inputs, non-existent records, and multi-lingual UTF-8 text support.
- **Test Cases**:
  - `test_tier2_non_existent_weather_location`: Asserts `404 Not Found` for un-cached locations.
  - `test_tier2_empty_database_queries`: Asserts empty list `[]` for unmatched queries.
  - `test_tier2_validation_missing_required_fields`: Asserts `422 Unprocessable Entity` on missing mandatory schema fields.
  - `test_tier2_unicode_and_swahili_dialect_support`: Asserts correct storage and retrieval of Swahili dialect inputs (e.g. "Kupanda Mbegu", "mbolea ya DAP").

### Tier 3: Cross-Feature Combinations (Mocked Integrations)
- **Goal**: Verify multi-service data pipelines and external API contract compliance.
- **Test Cases**:
  - `test_tier3_weather_sync_with_mocked_open_meteo_api`: Mocks Open-Meteo REST response, verifies parsing, upsert into SQLite `weather_cache`, and HTTP `200` response from `/api/weather/sync`.
  - `test_tier3_rag_context_retrieval_and_prompt_formatting`: Verifies SQLite context extraction (activities, pests, weather) and augmented prompt construction.
  - `test_tier3_rag_chat_endpoint_with_mocked_ollama_api`: Mocks Ollama REST API endpoint at `http://localhost:11434/api/generate`, asserts request payload contains DB context, and returns expected response JSON.

### Tier 4: Real-World Application Scenarios & Async Invocation
- **Goal**: Validate complete, realistic end-to-end user journeys and async route execution.
- **Test Cases**:
  - `test_tier4_end_to_end_farmer_workflow_simulation`: Simulates full farmer workflow: Activity Logging -> Pest History Logging -> Open-Meteo Weather Sync -> RAG Query to Ollama AI Agronomist -> Response Verification.
  - `test_tier4_async_endpoint_invocation`: Verifies non-blocking execution of async endpoints under concurrency.

---

## 5. Execution Command

To execute the full test suite:
```bash
pytest tests/test_app.py -v
```
