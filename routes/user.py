
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from routes.auth import get_current_user

user_router = APIRouter()

@user_router.get("/protected")
async def protected_route(current_user: dict = Depends(get_current_user)):
    return {"status": "ok", "user": current_user}