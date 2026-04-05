from fastapi import FastAPI, Request, Form, HTTPException, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from utils.url_parser import extract_video_id
import logging
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="templates")

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def get_supabase_client():
    """Create Supabase client"""
    if not supabase_url or not supabase_anon_key:
        return None
    from supabase import create_client
    return create_client(supabase_url, supabase_anon_key)

def get_supabase_admin_client():
    """Create Supabase admin client for operations that need elevated permissions"""
    if not supabase_url or not supabase_service_key:
        return None
    from supabase import create_client
    return create_client(supabase_url, supabase_service_key)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main page with form for YouTube URL input"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/summarize", response_class=HTMLResponse)
async def summarize(request: Request, youtube_url: str = Form(...)):
    """Process YouTube URL and return transcript summary"""
    try:
        from services.youtube import get_transcript
        from services.summary import generate_summary
        
        video_id = extract_video_id(youtube_url)
        if not video_id:
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")
        
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        transcript = get_transcript(video_url)
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

@app.post("/api/register", response_class=JSONResponse)
async def register(email: str = Form(...), password: str = Form(...)):
    """User registration endpoint"""
    try:
        client = get_supabase_client()
        if not client:
            return JSONResponse(
                {"error": "Supabase not configured. Please set SUPABASE_URL and SUPABASE_KEY in .env"},
                status_code=500
            )
        
        response = client.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if response.user:
            return JSONResponse({
                "message": "Registration successful! Please check your email to confirm account.",
                "user_id": response.user.id
            })
        else:
            return JSONResponse({"error": "Registration failed"}, status_code=400)
            
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return JSONResponse({"error": str(e)}, status_code=400)

@app.post("/api/login", response_class=JSONResponse)
async def login(email: str = Form(...), password: str = Form(...)):
    """User login endpoint"""
    try:
        client = get_supabase_client()
        if not client:
            return JSONResponse(
                {"error": "Supabase not configured. Please set SUPABASE_URL and SUPABASE_KEY in .env"},
                status_code=500
            )
        
        response = client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.user:
            return JSONResponse({
                "message": "Login successful",
                "user": {
                    "id": response.user.id,
                    "email": response.user.email
                },
                "session": {
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token
                }
            })
        else:
            return JSONResponse({"error": "Login failed"}, status_code=400)
            
    except Exception as e:
        logger.error(f"Login error: {e}")
        return JSONResponse({"error": str(e)}, status_code=400)

@app.post("/api/logout", response_class=JSONResponse)
async def logout(request: Request):
    """User logout endpoint"""
    try:
        client = get_supabase_client()
        if not client:
            return JSONResponse(
                {"error": "Supabase not configured"},
                status_code=500
            )
        
        client.auth.sign_out()
        return JSONResponse({"message": "Logout successful"})
            
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return JSONResponse({"error": str(e)}, status_code=400)

@app.get("/api/me", response_class=JSONResponse)
async def get_current_user(request: Request):
    """Get current authenticated user"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return JSONResponse({"user": None})
    
    try:
        client = get_supabase_client()
        if not client:
            return JSONResponse({"user": None})
        
        token = auth_header.replace("Bearer ", "")
        response = client.auth.get_user(token)
        
        if response.user:
            return JSONResponse({
                "user": {
                    "id": response.user.id,
                    "email": response.user.email
                }
            })
        return JSONResponse({"user": None})
        
    except Exception as e:
        logger.error(f"Get user error: {e}")
        return JSONResponse({"user": None})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)