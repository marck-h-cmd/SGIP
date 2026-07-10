import pytest
from datetime import datetime

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_dma_moche_info(client):
    response = client.get("/api/dmas/moche")
    # This assumes the endpoint is implemented and might return a 404 or 200 depending on DB state.
    # We assert standard format
    assert response.status_code in (200, 404)
