"""Tests for the address CRUD endpoints."""

from fastapi.testclient import TestClient

VALID_ADDRESS = {
    "address_text": "Brandenburg Gate, Berlin",
    "latitude": 52.5163,
    "longitude": 13.3777,
}


def test_create_address_returns_201_and_body(client: TestClient):
    response = client.post("/addresses", json=VALID_ADDRESS)

    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["address_text"] == VALID_ADDRESS["address_text"]
    assert body["latitude"] == VALID_ADDRESS["latitude"]
    assert body["longitude"] == VALID_ADDRESS["longitude"]
    # created_at and updated_at are set in the same insert, so they match
    # to the microsecond-rounded timestamp stored in SQLite.
    assert body["created_at"][:19] == body["updated_at"][:19]


def test_create_address_strips_whitespace(client: TestClient):
    payload = {**VALID_ADDRESS, "address_text": "  Padded address  "}
    body = client.post("/addresses", json=payload).json()

    assert body["address_text"] == "Padded address"


def test_create_rejects_latitude_out_of_range(client: TestClient):
    payload = {**VALID_ADDRESS, "latitude": 95.0}
    response = client.post("/addresses", json=payload)

    assert response.status_code == 422


def test_create_rejects_longitude_out_of_range(client: TestClient):
    payload = {**VALID_ADDRESS, "longitude": -200.0}
    response = client.post("/addresses", json=payload)

    assert response.status_code == 422


def test_create_rejects_empty_address_text(client: TestClient):
    payload = {**VALID_ADDRESS, "address_text": ""}
    response = client.post("/addresses", json=payload)

    assert response.status_code == 422


def test_list_addresses_is_paginated(client: TestClient):
    for i in range(3):
        client.post("/addresses", json={**VALID_ADDRESS, "address_text": f"Addr {i}"})

    page = client.get("/addresses", params={"limit": 2, "offset": 1}).json()

    assert [a["address_text"] for a in page] == ["Addr 1", "Addr 2"]


def test_get_address_by_id(client: TestClient):
    created = client.post("/addresses", json=VALID_ADDRESS).json()

    response = client.get(f"/addresses/{created['id']}")

    assert response.status_code == 200
    assert response.json()["address_text"] == VALID_ADDRESS["address_text"]


def test_get_missing_address_returns_404(client: TestClient):
    response = client.get("/addresses/9999")

    assert response.status_code == 404


def test_update_address_changes_fields_and_timestamp(client: TestClient):
    created = client.post("/addresses", json=VALID_ADDRESS).json()
    update = {
        "address_text": "Reichstag, Berlin",
        "latitude": 52.5186,
        "longitude": 13.376,
    }

    response = client.put(f"/addresses/{created['id']}", json=update)
    body = response.json()

    assert response.status_code == 200
    assert body["address_text"] == update["address_text"]
    assert body["latitude"] == update["latitude"]
    assert body["updated_at"] > body["created_at"]


def test_update_missing_address_returns_404(client: TestClient):
    response = client.put("/addresses/9999", json=VALID_ADDRESS)

    assert response.status_code == 404


def test_delete_address_returns_204(client: TestClient):
    created = client.post("/addresses", json=VALID_ADDRESS).json()

    response = client.delete(f"/addresses/{created['id']}")

    assert response.status_code == 204
    assert client.get(f"/addresses/{created['id']}").status_code == 404


def test_delete_missing_address_returns_404(client: TestClient):
    response = client.delete("/addresses/9999")

    assert response.status_code == 404