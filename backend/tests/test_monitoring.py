from fastapi.testclient import TestClient
from fastapi_app.main import app
from fastapi_app.services.monitoring import monitoring_service

client = TestClient(app)

def test_monitoring_endpoint():
    # Hit a health endpoint to generate traffic
    client.get("/health")
    client.get("/health")
    
    # Check stats
    response = client.get("/monitoring/stats")
    assert response.status_code == 200
    data = response.json()
    
    assert "total_requests" in data
    assert data["total_requests"] >= 2  # At least the 2 health checks + maybe the monitoring check itself depending on middleware order
    assert "uptime" in data
    assert "requests_by_endpoint" in data
    
    # Check specific endpoint tracking
    # Note: Middleware runs before response, so the monitoring request itself might be counted depending on async flow, 
    # but the health calls definitely should be there.
    # The middleware wraps the request, so yes, it counts.
    
    # Allow some flexibility in exact counts due to potential other tests running or initialization
    assert data["requests_by_endpoint"].get("GET /health", 0) >= 2

def test_monitoring_404_tracking():
    # Generate a 404
    client.get("/non-existent-endpoint")
    
    response = client.get("/monitoring/stats")
    data = response.json()
    
    assert data["error_rate_4xx"] >= 1
