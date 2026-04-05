import pytest
from utils.url_parser import extract_video_id


class TestExtractVideoId:
    """Test URL parsing functionality"""
    
    def test_standard_youtube_url(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"
    
    def test_youtu_be_short_url(self):
        url = "https://youtu.be/dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"
    
    def test_youtube_shorts_url(self):
        url = "https://www.youtube.com/shorts/dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"
    
    def test_youtube_embed_url(self):
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"
    
    def test_url_with_extra_params(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PL123&index=5"
        assert extract_video_id(url) == "dQw4w9WgXcQ"
    
    def test_invalid_url(self):
        assert extract_video_id("https://example.com/video") is None
    
    def test_empty_url(self):
        assert extract_video_id("") is None
        assert extract_video_id(None) is None
    
    def test_whitespace_in_url(self):
        url = "  https://www.youtube.com/watch?v=dQw4w9WgXcQ  "
        assert extract_video_id(url) == "dQw4w9WgXcQ"