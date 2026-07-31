def test_create_and_get_activity(client):
    payload = {
        "farmer_id": "farmer_001",
        "activity_type": "FERTILIZER_APPLICATION",
        "crop_type": "Maize",
        "description": "Applied 50kg DAP fertilizer",
        "quantity": 50.0,
        "unit": "kg",
        "field_location": "Main Shamba",
        "notes": "Applied in the morning",
    }

    # POST create
    response = client.post("/api/v1/activities", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["farmer_id"] == "farmer_001"
    assert data["activity_type"] == "FERTILIZER_APPLICATION"
    assert data["quantity"] == 50.0
    activity_id = data["id"]

    # GET by ID
    get_res = client.get(f"/api/v1/activities/{activity_id}")
    assert get_res.status_code == 200
    assert get_res.json()["description"] == "Applied 50kg DAP fertilizer"

    # GET list
    list_res = client.get("/api/v1/activities?farmer_id=farmer_001")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] == 1
    assert len(list_data["activities"]) == 1


def test_update_and_delete_activity(client):
    payload = {
        "farmer_id": "farmer_002",
        "activity_type": "PLANTING",
        "crop_type": "Beans",
        "description": "Planted Rosecoco beans",
    }

    # Create
    create_res = client.post("/api/v1/activities", json=payload)
    activity_id = create_res.json()["id"]

    # PUT Update
    update_payload = {"notes": "Planted with 2cm depth", "quantity": 10.0, "unit": "kg"}
    update_res = client.put(f"/api/v1/activities/{activity_id}", json=update_payload)
    assert update_res.status_code == 200
    assert update_res.json()["notes"] == "Planted with 2cm depth"
    assert update_res.json()["quantity"] == 10.0

    # DELETE
    del_res = client.delete(f"/api/v1/activities/{activity_id}")
    assert del_res.status_code == 204

    # Verify 404 on GET
    get_res = client.get(f"/api/v1/activities/{activity_id}")
    assert get_res.status_code == 404


def test_legacy_activities_route(client):
    payload = {
        "farmer_id": "default_farmer",
        "activity_type": "WEEDING",
        "crop_type": "Tomatoes",
        "description": "Weeded plot B",
    }
    client.post("/api/activities", json=payload)
    res = client.get("/api/activities")
    assert res.status_code == 200
    data = res.json()
    total = data["total"] if isinstance(data, dict) else len(data)
    assert total >= 1
