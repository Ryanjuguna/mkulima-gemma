def test_create_and_query_pest_disease(client):
    payload = {
        "farmer_id": "default_farmer",
        "crop_type": "Maize",
        "issue_type": "PEST",
        "issue_name": "Fall Armyworm",
        "severity": "HIGH",
        "image_path": "/data/uploads/leaf_01.jpg",
        "symptoms_description": "Holes in leaves with saw-dust frass",
        "ai_diagnosis_summary": "PaliGemma detected Fall Armyworm (92% confidence)",
        "recommended_treatment": "Apply Neem extract or bio-pesticide",
        "chemical_safety_warning": "High chemical toxicity warning: wear PPE",
        "status": "ACTIVE"
    }

    # POST create
    post_res = client.post("/api/v1/pest-disease", json=payload)
    assert post_res.status_code == 201
    record = post_res.json()
    assert record["id"] is not None
    assert record["issue_name"] == "Fall Armyworm"
    assert record["severity"] == "HIGH"
    record_id = record["id"]

    # GET by ID
    get_res = client.get(f"/api/v1/pest-disease/{record_id}")
    assert get_res.status_code == 200
    assert get_res.json()["issue_type"] == "PEST"

    # GET list with query filters
    list_res = client.get("/api/v1/pest-disease?crop_type=Maize&issue_type=PEST&status=ACTIVE")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] == 1
    assert len(list_data["records"]) == 1


def test_patch_pest_disease_status(client):
    payload = {
        "farmer_id": "default_farmer",
        "crop_type": "Tomatoes",
        "issue_type": "DISEASE",
        "issue_name": "Late Blight",
        "severity": "CRITICAL",
        "symptoms_description": "Water-soaked lesions on leaves",
        "status": "ACTIVE"
    }

    create_res = client.post("/api/v1/pest-disease", json=payload)
    record_id = create_res.json()["id"]

    # PATCH update status to RESOLVED
    patch_payload = {
        "status": "RESOLVED",
        "recommended_treatment": "Applied copper fungicide; symptoms stopped."
    }
    patch_res = client.patch(f"/api/v1/pest-disease/{record_id}", json=patch_payload)
    assert patch_res.status_code == 200
    patched_data = patch_res.json()
    assert patched_data["status"] == "RESOLVED"
    assert patched_data["recommended_treatment"] == "Applied copper fungicide; symptoms stopped."


def test_legacy_pest_routes(client):
    payload = {
        "crop_type": "Beans",
        "issue_type": "WEED",
        "issue_name": "Striga Weed",
        "symptoms_description": "Purple flowers choking bean growth",
    }
    client.post("/api/pests", json=payload)

    res = client.get("/api/pests")
    assert res.status_code == 200
    # Legacy routes (no /v1/) return a plain list, not a paginated dict
    assert len(res.json()) >= 1
