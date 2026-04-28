import time
from collections import defaultdict
from fastapi import HTTPException

# { user_id: [timestamp, timestamp, ...] }
request_log: dict[str, list[float]] = defaultdict(list)

WINDOW_SECONDS = 60
MAX_REQUESTS = 10

def check_rate_limit(user_id: str):
    now = time.time()
    window_start = now - WINDOW_SECONDS

    # Remove timestamps outside the window
    request_log[user_id] = [t for t in request_log[user_id] if t > window_start]

    if len(request_log[user_id]) >= MAX_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail=f"Too many requests. Max {MAX_REQUESTS} per minute."
        )

    request_log[user_id].append(now)