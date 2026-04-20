import secrets
from fastapi import APIRouter, HTTPException, Response, Cookie, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])

# SECURITY CONFIG
AUTH_USER = "admin"
AUTH_PASS = "contentflow2026"
SESSION_DB = set()

class LoginRequest(BaseModel):
    username: str
    password: str

async def verify_session(contentflow_session: str = Cookie(None)):
    if not contentflow_session or contentflow_session not in SESSION_DB:
        raise HTTPException(status_code=401, detail="Access Denied")
    return contentflow_session

@router.post("/login")
async def login(request: LoginRequest, response: Response):
    if request.username == AUTH_USER and request.password == AUTH_PASS:
        session_id = secrets.token_hex(32)
        SESSION_DB.add(session_id)
        response.set_cookie(key="contentflow_session", value=session_id, httponly=True, samesite="lax")
        return {"status": "Verified"}
    raise HTTPException(status_code=401, detail="Invalid Pulse")

@router.get("/session")
async def check_session(session: str = Depends(verify_session)):
    return {"status": "Active"}

@router.post("/logout")
async def logout(response: Response, contentflow_session: str = Cookie(None)):
    if contentflow_session in SESSION_DB:
        SESSION_DB.remove(contentflow_session)
    response.delete_cookie("contentflow_session")
    return {"status": "Logged Out"}
