from fastapi import APIRouter
from src.auth.schemas import RegisterRequest, LoginRequest, RefreshTokenRequest
from src.auth.service import register_user, login_user, refresh_access_token, logout_user

#temporary delete later
from fastapi import Depends
from src.auth.dependancies import get_current_user

router = APIRouter()

@router.post("/register")
async def register(data: RegisterRequest):
    return await register_user(data.email, data.password)

@router.post("/login")
async def login(data: LoginRequest):
    return await login_user(data.email, data.password)

@router.get("/me")
async def get_me(current_user = Depends(get_current_user)):
    return current_user

@router.post("/refresh")
async def refresh(data: RefreshTokenRequest):
    return await refresh_access_token(data.refresh_token)

@router.post("/logout")
async def logout(data: RefreshTokenRequest):
    return await logout_user(data.refresh_token)