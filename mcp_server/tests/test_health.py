"""Test health API endpoints."""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "version" in data
    assert "timestamp" in data
    assert "service" in data
    assert "database" in data
    
def test_readiness_probe():
    """Test the Kubernetes readiness probe endpoint."""
    response = client.get("/api/health/readiness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    
def test_liveness_probe():
    """Test the Kubernetes liveness probe endpoint."""
    response = client.get("/api/health/liveness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
