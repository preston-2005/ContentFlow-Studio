from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.api.auth import verify_session
from app.voice_studio.audio_engine import audio_engine

router = APIRouter(prefix="/api/v1/audio", tags=["Audio"])

class AudioSynthesisRequest(BaseModel):
    text: str
    voice: str = "auto"

@router.post("/synthesize")
async def synthesize_audio(request: AudioSynthesisRequest, session: str = Depends(verify_session)):
    """
    Synthesize text into speech using the neural audio engine.
    """
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="No text provided for synthesis.")
            
        print(f"> [PIPELINE] 🔊 SYNTHESIZING AUDIO: '{request.text[:30]}...' [{request.voice}]")
        file_path = await audio_engine.synthesize(request.text, voice=request.voice)
        
        if not file_path:
            raise HTTPException(status_code=500, detail="Synthesis failed to generate file.")
            
        # Return the web-accessible path
        # Assuming the path is returned as 'vault/audio/...' or similar
        # We need to make it relative to the static mount
        return {"status": "Complete", "url": f"/{file_path}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
