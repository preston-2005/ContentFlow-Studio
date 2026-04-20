import os
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from pydantic import BaseModel
from app.api.auth import verify_session
from app.services.pipeline_service import execute_production_pipeline, execute_iteration, process_voice_pitch

router = APIRouter(prefix="/api/v1/production", tags=["Production"])

class ProductionRequest(BaseModel):
    topic: str
    style: str = "cinematic"
    platform: str = "youtube"

class IterateRequest(BaseModel):
    instruction: str

class VoicePitchRequest(BaseModel):
    transcript: str

@router.post("/initialize")
async def initialize_production(request: ProductionRequest, background_tasks: BackgroundTasks, session: str = Depends(verify_session)):
    if not request.topic:
        raise HTTPException(status_code=400, detail="Topic required")
    background_tasks.add_task(execute_production_pipeline, request.topic, request.style, request.platform)
    return {"status": "Swarm Initialized"}

@router.post("/iterate")
async def iterate_production(request: IterateRequest, session: str = Depends(verify_session)):
    try:
        refined_script = execute_iteration(request.instruction)
        return {"status": "Magic Applied", "content": refined_script}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/voice-pitch")
async def voice_pitch(request: VoicePitchRequest, session: str = Depends(verify_session)):
    try:
        topic = process_voice_pitch(request.transcript)
        return {"status": "Pitch Decoded", "topic": topic}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/latest-script")
async def get_latest_script():
    path = "export/latest_script.txt"
    if not os.path.exists(path): return {"content": ""}
    with open(path, "r", encoding="utf-8") as f:
        return {"content": f.read()}

@router.get("/logs")
async def get_logs():
    if not os.path.exists("crew_output.log"): return {"logs": "Connecting..."}
    with open("crew_output.log", "r", encoding="utf-8") as f:
        # Get last 100 lines
        lines = f.readlines()
        return {"logs": "".join(lines[-100:])}
