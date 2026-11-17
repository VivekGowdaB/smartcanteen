"""Health check endpoint tests for Docker and Kubernetes probes."""


def test_root_health_endpoint(client):
    """Test /health root probe."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def test_api_health_endpoint(client):
    """Test /api/health probe."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "healthy"
    assert data["service"] == "smart-canteen-ordering-system"
