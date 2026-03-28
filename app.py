from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from utils.url_parser import extract_video_id
import logging

app = FastAPI()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main page with form for YouTube URL input"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/summarize", response_class=HTMLResponse)
async def summarize(request: Request, youtube_url: str = Form(...)):
    """Process YouTube URL and return transcript summary"""
    try:
        # Import services only when needed to avoid blocking at import time
        from services.youtube import get_transcript
        from services.summary import generate_summary
        
        # Extract video ID from URL
        video_id = extract_video_id(youtube_url)
        if not video_id:
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")
        
        # Get transcript
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        transcript = get_transcript(video_url)
        
        # Generate real summary
        summary = generate_summary(transcript)
        
        return templates.TemplateResponse(
            "index.html", 
            {
                "request": request,
                "youtube_url": youtube_url,
                "summary": summary,
                "transcript": transcript[:500] + "..." if len(transcript) > 500 else transcript,
                "video_id": video_id
            }
        )
    except Exception as e:
        logger.error(f"Error processing URL {youtube_url}: {e}")
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "youtube_url": youtube_url,
                "error": str(e)
            }
        )

@app.get("/health")
async def health_check():
    """Health check endpoint - returns immediately without any dependencies"""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)