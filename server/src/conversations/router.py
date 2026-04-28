from fastapi import APIRouter, Depends
from src.auth.dependancies import get_current_user
import src.services.db as db

router = APIRouter()

@router.get("/conversations")
async def list_conversations(current_user=Depends(get_current_user)):
    rows = await db.pool.fetch(
        """
        SELECT id, thread_id, title, created_at
        FROM conversations
        WHERE user_id = $1
        ORDER BY updated_at DESC
        """,
        current_user["id"]
    )
    return [dict(row) for row in rows]