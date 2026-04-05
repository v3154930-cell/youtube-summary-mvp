from fastapi import FastAPI, Request, Form, HTTPException, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from utils.url_parser import extract_video_id
import logging
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="templates")

if Path("public").exists():
    app.mount("/public", StaticFiles(directory="public"), name="public")

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def get_supabase_client():
    """Create Supabase client"""
    if not supabase_url or not supabase_anon_key:
        logger.error(f"Missing config: url={bool(supabase_url)}, anon_key={bool(supabase_anon_key)}")
        return None
    from supabase import create_client
    client = create_client(supabase_url, supabase_anon_key)
    logger.info(f"Supabase client created with URL: {supabase_url}")
    logger.info(f"Anon key starts with: {supabase_anon_key[:50]}...")
    return client

def get_supabase_admin_client():
    """Create Supabase admin client for operations that need elevated permissions"""
    if not supabase_url or not supabase_service_key:
        return None
    from supabase import create_client
    client = create_client(supabase_url, supabase_service_key)
    logger.info("Admin client created with service role key")
    return client

@app.post("/api/register", response_class=JSONResponse)
async def register(email: str = Form(...), password: str = Form(...)):
    """User registration endpoint - using admin client to bypass rate limits"""
    try:
        client = get_supabase_admin_client()
        if not client:
            client = get_supabase_client()
            if not client:
                return JSONResponse(
                    {"error": "Supabase not configured"},
                    status_code=500
                )
        
        logger.info(f"Attempting registration for: {email}")
        
        response = client.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True
        })
        
        logger.info(f"Registration response: {response}")
        
        if response.user:
            return JSONResponse({
                "message": "Registration successful! You can now login.",
                "user_id": response.user.id,
                "email_confirmed": response.user.email_confirmed_at is not None
            })
        else:
            return JSONResponse({
                "message": "Registration successful! User created.",
                "needs_confirmation": False
            })
            
    except Exception as e:
        logger.error(f"Registration error: {e}")
        error_msg = str(e)
        if "rate limit" in error_msg.lower():
            return JSONResponse({"error": "Too many registration attempts. Please try again later."}, status_code=429)
        return JSONResponse({"error": error_msg}, status_code=400)

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

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/summarize", response_class=HTMLResponse)
async def summarize(request: Request, youtube_url: str = Form(...)):
    """Summarize YouTube video"""
    try:
        video_id = extract_video_id(youtube_url)
        if not video_id:
            return templates.TemplateResponse("index.html", {"request": request, "error": "Invalid YouTube URL"})
        
        from services.youtube import get_transcript
        from services.summary import generate_summary
        
        transcript = get_transcript(youtube_url)
        if not transcript:
            return templates.TemplateResponse("index.html", {"request": request, "error": "Could not get transcript - check API key"})
        
        summary = generate_summary(transcript)
        if not summary:
            return templates.TemplateResponse("index.html", {"request": request, "error": "Could not generate summary"})
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "summary": summary,
            "transcript_preview": transcript[:500]
        })
    except Exception as e:
        logger.error(f"Summarize error: {e}")
        return templates.TemplateResponse("index.html", {"request": request, "error": str(e)})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

@app.get("/debug/env")
async def debug_env():
    """Debug endpoint to check environment variables"""
    return {
        "SUPABASE_URL": supabase_url,
        "SUPABASE_KEY": "set" if supabase_key else "not set",
        "SUPABASE_ANON_KEY": "set" if supabase_anon_key else "not set",
        "SUPABASE_SERVICE_KEY": "set" if supabase_service_key else "not set"
    }

@app.delete("/api/users/{user_id}", response_class=JSONResponse)
async def delete_user(user_id: str):
    """Delete user by ID (admin only)"""
    try:
        client = get_supabase_admin_client()
        if not client:
            return JSONResponse({"error": "Admin client not configured"}, status_code=500)
        
        response = client.auth.admin.delete_user(user_id)
        logger.info(f"Delete user {user_id}: {response}")
        
        return JSONResponse({"message": "User deleted successfully", "user_id": user_id})
        
    except Exception as e:
        logger.error(f"Delete user error: {e}")
        return JSONResponse({"error": str(e)}, status_code=400)

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)