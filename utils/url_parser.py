
import re
from typing import Optional

def extract_video_id(url: str) -> Optional[str]:
    """
    Extract YouTube video ID from various URL formats.
    
    Args:
        url (str): YouTube URL
        
    Returns:
        Optional[str]: Video ID if found, None otherwise
    """
    if not url:
        return None
    
    # Remove any whitespace
    url = url.strip()
    
    # Pattern to match YouTube video ID
    # Handles: https://www.youtube.com/watch?v=ID
    #          https://youtu.be/ID
    #          https://www.youtube.com/shorts/ID
    #          https://www.youtube.com/embed/ID
    #          etc.
    patterns = [
        r'[?&]v=([^&]+)',           # watch?v=ID
        r'youtu\.be/([^?&]+)',      # youtu.be/ID
        r'/shorts/([^?&]+)',        # /shorts/ID
        r'embed/([^?&]+)',          # embed/ID
        r'v/([^?&]+)'               # v/ID
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            # YouTube video IDs are typically 11 characters
            if len(video_id) == 11:
                return video_id
    
    return None
