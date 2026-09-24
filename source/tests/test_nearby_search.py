"""Tests for the nearby search endpoint and the Haversine helper."""

import math

import pytest
from fastapi.testclient import TestClient

from app.service import haversine_distance_km

BERLIN = {"address_text": "Reichstag, Berlin", "latitude": 52.5186, "longitude": 13.376}
PARIS = {"address_text": "Eiffel Tower, Paris", "latitude": 48.8584, "longitude": 2.2945}
ROME = {"address_text": "Colosseum, Rome", "latitude": 41.8902, "longitude": 12.4922}


@pytest.mark.parametrize(
    ("lat1", "lon1", "lat2", "lon2", "expected_km"),
    [
        (52.5186, 13.376, 48.8584, 2.2945, 879),  # Berlin -> Paris
        (52.5186, 13.376, 52.5186, 13.376, 0),  # identical points
        (0.0, 0.0, 0.0, 1.0, 111.2),  # one degree of longitude at the equator
    ],
)
def test_haversine_matches_known_distances(lat1, lon1, lat2, lon2, expected_km):
    distance = haversine_distance_km(lat1, lon1, lat2, lon2)

    assert math.isclose(distance, expected_km, abs_tol=1.0)


def test_nearby_returns_only_addresses_within_radius(client: TestClient):
    for address in (BERLIN, PARIS, ROME):
        client.post("/addresses", json=address)

    hits = client.get(
        "/addresses/nearby",
        params={"lat": 52.52, "lon": 13.405, "radius_km": 50},
    ).json()

    assert [h["address_text"] for h in hits] == [BERLIN["address_text"]]


def test_nearby_results_sorted_by_distance(client: TestClient):
    for address in (BERLIN, PARIS, ROME):
        client.post("/addresses", json=address)

    hits = client.get(
        "/addresses/nearby",
        params={"lat": 52.52, "lon": 13.405, "radius_km": 1200},
    ).json()

    distances = [h["distance_km"] for h in hits]
    assert distances == sorted(distances)
    assert [h["address_text"] for h in hits] == [
        BERLIN["address_text"],
        PARIS["address_text"],  # ~881 km from the origin
        ROME["address_text"],  # ~1184 km from the origin
    ]


def test_nearby_distance_is_plausible(client: TestClient):
    client.post("/addresses", json=BERLIN)

    hit = client.get(
        "/addresses/nearby",
        params={"lat": 52.52, "lon": 13.405, "radius_km": 50},
    ).json()[0]

    assert 1.0 < hit["distance_km"] < 3.0


def test_nearby_supports_pagination(client: TestClient):
    for address in (BERLIN, PARIS, ROME):
        client.post("/addresses", json=address)

    page = client.get(
        "/addresses/nearby",
        params={"lat": 52.52, "lon": 13.405, "radius_km": 1200, "limit": 1, "offset": 1},
    ).json()

    assert [h["address_text"] for h in page] == [PARIS["address_text"]]


def test_nearby_rejects_invalid_latitude(client: TestClient):
    response = client.get(
        "/addresses/nearby",
        params={"lat": 200, "lon": 13, "radius_km": 10},
    )

    assert response.status_code == 422


def test_nearby_rejects_non_positive_radius(client: TestClient):
    response = client.get(
        "/addresses/nearby",
        params={"lat": 52, "lon": 13, "radius_km": 0},
    )

    assert response.status_code == 422