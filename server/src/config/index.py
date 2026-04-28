import os
from dotenv import load_dotenv

load_dotenv()

if not os.getenv("SUPABASE_API_URL") or not os.getenv("SUPABASE_SECRET_KEY"):
    raise ValueError(
        "SUPABASE_API_URL and SUPABASE_SECRET_KEY must be set in .env file"
        )

appConfig={
    "supabase_api_url": os.getenv("SUPABASE_API_URL"),
    "supabase_secret_key": os.getenv("SUPABASE_SECRET_KEY"),
    "database_url": os.getenv("DATABASE_URL"),
    "jwt_secret": os.getenv("JWT_SECRET"),
    "access_token_expiry_minutes": os.getenv("ACCESS_TOKEN_EXPIRY_MINUTES"),
    "refresh_token_expiry_days": os.getenv("REFRESH_TOKEN_EXPIRY_DAYS"),
    "jwt_algorithm": os.getenv("JWT_ALGORITHM")
}