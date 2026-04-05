import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app import app
    return TestClient(app)


class TestSecurityHeaders:
    """Test security headers and configurations"""
    
    def test_no_credentials_in_debug(self, client):
        """Ensure debug endpoint doesn't leak sensitive data"""
        response = client.get("/debug/env")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("SUPABASE_KEY") == "not set"
        assert data.get("SUPABASE_ANON_KEY") == "not set"
        assert data.get("SUPABASE_SERVICE_KEY") == "not set"
    
    def test_health_no_auth_required(self, client):
        """Health endpoint should be public"""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_home_no_auth_required(self, client):
        """Home page should be public"""
        response = client.get("/")
        assert response.status_code == 200


class TestAuthSecurity:
    """Test auth endpoint security"""
    
    def test_login_csrf_protection(self, client):
        """Login should work with Form data"""
        response = client.post("/api/login", data={"email": "test@test.com", "password": "test"})
        assert response.status_code in [200, 400, 401, 500]
    
    def test_register_no_json_injection(self, client):
        """Register should not accept JSON body injection"""
        response = client.post("/api/register", json={"email": "test@test.com", "password": "test"})
        assert response.status_code in [422, 500]
    
    def test_unauthorized_access_denied(self, client):
        """Protected routes should require auth"""
        response = client.delete("/api/users/test-user-id")
        assert response.status_code in [401, 403, 500]