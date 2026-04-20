from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.api.auth import verify_session
from app.media_studio.generative_assets import canvas_engine

router = APIRouter(prefix="/api/v1", tags=["Media"])

class ImageGenRequest(BaseModel):
    prompt: str
    ratio: str = "16:9"

@router.post("/canvas/generate")
async def generate_img(request: ImageGenRequest, session: str = Depends(verify_session)):
    try:
        path = canvas_engine.generate_image(request.prompt, ratio=request.ratio)
        return {"file": path}
    except Exception as e: 
        raise HTTPException(status_code=500, detail=str(e))

class VideoGenRequest(BaseModel):
    prompt: str
    ratio: str = "16:9"

@router.post("/canvas/generate-video")
async def generate_vid(request: VideoGenRequest, session: str = Depends(verify_session)):
    try:
        path = canvas_engine.generate_video(request.prompt, ratio=request.ratio)
        return {"file": path}
    except Exception as e: 
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/brain/latest")
async def get_latest_brain_output():
    import os
    # Consistently resolve to the root export folder
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    path = os.path.join(base_dir, "export", "latest_script.txt")
    
    if not os.path.exists(path): return {"content": ""}
    with open(path, "r", encoding="utf-8") as f:
        return {"content": f.read()}
