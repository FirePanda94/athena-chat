from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
import src.services.db as db
from src.config.index import appConfig

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(
            token,
            appConfig['jwt_secret'],
            algorithms=[appConfig["jwt_algorithm"]]
        )

        user_id = payload.get("id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid Token")
        
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    if db.pool is None:
        raise HTTPException(status_code=500, detail="DB not initialised")
    
    async with db.pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT * FROM users WHERE id = $1", 
            user_id
        )

        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user