def test_create_and_search_extension_contacts(client):
    contact_payload = {
        "name": "Dr. Jane Wanjiru",
        "role_or_type": "EXTENSION_OFFICER",
        "organization": "Ministry of Agriculture",
        "county_region": "Nyeri",
        "sub_county_ward": "Nyeri Central",
        "phone_number": "+254712345678",
        "email": "jwanjiru@agri.go.ke",
        "services_offered": "Soil health testing, maize disease diagnosis, organic pest advice",
        "is_verified": 1
    }

    # POST create
    post_res = client.post("/api/v1/extension-services", json=contact_payload)
    assert post_res.status_code == 201
    contact = post_res.json()
    assert contact["id"] is not None
    assert contact["name"] == "Dr. Jane Wanjiru"
    contact_id = contact["id"]

    # GET by ID
    get_res = client.get(f"/api/v1/extension-services/{contact_id}")
    assert get_res.status_code == 200
    assert get_res.json()["county_region"] == "Nyeri"

    # Search by county and role
    search_res = client.get("/api/v1/extension-services?county=Nyeri&role_type=EXTENSION_OFFICER")
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert search_data["total"] == 1
    assert search_data["directory"][0]["phone_number"] == "+254712345678"

    # Search text in services
    text_search_res = client.get("/api/v1/extension-services?search=Soil health")
    assert text_search_res.status_code == 200
    assert text_search_res.json()["total"] == 1


def test_legacy_extension_routes(client):
    payload = {
        "name": "Kiambu Agrovet Hub",
        "role_or_type": "AGROVET",
        "county_region": "Kiambu",
        "phone_number": "+254700112233",
    }
    client.post("/api/extensions", json=payload)

    res = client.get("/api/extensions?county=Kiambu")
    assert res.status_code == 200
    # Legacy routes (no /v1/) return a plain list, not a paginated dict
    assert len(res.json()) >= 1
