import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    from app import app
    return TestClient(app)


class TestHealthEndpoints:
    """Test basic app endpoints"""
    
    def test_health_endpoint(self, client):
        """Test /health returns OK"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    
    def test_home_page_loads(self, client):
        """Test home page returns HTML"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")


class TestSummarizeEndpoint:
    """Test summarize functionality (mocked)"""
    
    @patch("app.get_transcript")
    @patch("app.generate_summary")
    def test_summarize_success(self, mock_summary, mock_transcript, client):
        """Test successful summarize flow"""
        mock_transcript.return_value = "Test transcript text"
        mock_summary.return_value = "Test summary"
        
        response = client.post("/summarize", data={"youtube_url": "https://youtu.be/test"})
        
        assert response.status_code == 200
    
    def test_summarize_invalid_url(self, client):
        """Test summarize with invalid URL"""
        response = client.post("/summarize", data={"youtube_url": "https://example.com"})
        assert response.status_code == 200
        assert b"Invalid" in response.content or b"error" in response.content.lower()
    
    def test_summarize_missing_url(self, client):
        """Test summarize without URL"""
        response = client.post("/summarize", data={})
        assert response.status_code == 422