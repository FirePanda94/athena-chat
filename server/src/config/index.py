import os
from dotenv import load_dotenv

load_dotenv()

appConfig={
    "database_url": os.getenv("DATABASE_URL"),
    "jwt_secret": os.getenv("JWT_SECRET"),
    "access_token_expiry_minutes": os.getenv("ACCESS_TOKEN_EXPIRY_MINUTES"),
    "refresh_token_expiry_days": os.getenv("REFRESH_TOKEN_EXPIRY_DAYS"),
    "jwt_algorithm": os.getenv("JWT_ALGORITHM")
}