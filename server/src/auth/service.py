from fastapi import HTTPException
import src.services.db as db
from src.auth.utils import hash_password
from src.auth.utils import verify_password, create_access_token, create_refresh_token
from src.config.index import appConfig
from datetime import datetime, timedelta, timezone

async def register_user(email, password):
    try:
        if db.pool is None:
            raise HTTPException(status_code=500, detail="DB not initialised")
        
        async with db.pool.acquire() as conn:
            existing_user = await conn.fetchrow("SELECT * FROM users WHERE email = $1", email)

            if existing_user is not None:
                raise HTTPException(status_code=400, detail="User already exists")
            
            hashed = hash_password(password)
            new_user = await conn.fetchrow(
                "INSERT INTO users (email, password, is_active) VALUES ($1, $2, True) RETURNING *",
                email,
                hashed
                )
            return new_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Something went wrong")
    

async def login_user(email, password):
    try:
        if db.pool is None:
            raise HTTPException(status_code=500, detail="DB not initialised")
        
        async with db.pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE email=$1",
                email
            )
            if user is None:
                raise HTTPException(status_code=401, detail="User not found")
            
            is_valid = verify_password(password, user["password"])
            if not is_valid:
                raise HTTPException(status_code=401, detail="Wrong password")
            
            token = create_access_token({
                "id": str(user["id"]),
                "email": user["email"]
            })

            refresh_token = create_refresh_token()
            expires_at = datetime.now(timezone.utc) + timedelta(days=int(appConfig["refresh_token_expiry_days"]))
            await conn.execute(
                """
                INSERT INTO refresh_tokens (user_id, token, expires_at, is_revoked)
                VALUES ($1, $2, $3, $4)
                """,
                str(user["id"]),
                refresh_token,
                expires_at,
                False
            )

            return {"access_token": token,
                    "refresh_token": refresh_token}
    
    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Something went wrong")
    
async def refresh_access_token(refresh_token: str):
    try:
        if db.pool is None:
            raise HTTPException(status_code=500, detail="DB not initialised")
        
        async with db.pool.acquire() as conn:
            token_row = await conn.fetchrow(
                "SELECT * FROM refresh_tokens WHERE token = $1",
                refresh_token
            )
            if token_row is None:
                raise HTTPException(status_code=401, detail="Invalid refresh token")
            
            if token_row["is_revoked"]:
                raise HTTPException(status_code=401, detail="Refresh token revoked")
            
            if token_row["expires_at"] < datetime.now(timezone.utc):
                raise HTTPException(status_code=401, detail="Refresh token expired")
            
            user = await conn.fetchrow(
                "SELECT * FROM users where id = $1",
                token_row["user_id"]
            )

            if user is None:
                raise HTTPException(status_code=401, detail="User not found")
            
            access_token = create_access_token({
                "id": str(user["id"]),
                "email": user["email"]
            })

            return {"access_token": access_token}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Something went wrong")
    
async def logout_user(refresh_token: str):
    try:
        if db.pool is None:
            raise HTTPException(status_code=500, detail="DB not initialised")
        
        async with db.pool.acquire() as conn:
            token_row = await conn.fetchrow(
                "SELECT * FROM refresh_tokens WHERE token = $1",
                refresh_token
            )

            if token_row is None:
                raise HTTPException(status_code=401, detail="Invalid refresh token")
            
            await conn.execute(
                "UPDATE refresh_tokens SET is_revoked=TRUE WHERE token=$1",
                refresh_token
            )

        return {"message":"Logged out successfully"}
    
    except HTTPException:
        raise
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Something went wrong")