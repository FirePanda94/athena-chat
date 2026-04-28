import bcrypt
from jose import jwt
from datetime import datetime, timedelta, timezone
from src.config.index import appConfig
import secrets

def hash_password(password: str):
    pass_encode = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hash_pass = bcrypt.hashpw(pass_encode, salt)
    return hash_pass.decode('utf-8')

def verify_password(password: str, hashed: str):
    encoded_password = password.encode('utf-8')
    encoded_hashed = hashed.encode('utf-8')
    return bcrypt.checkpw(encoded_password, encoded_hashed)
     
def create_access_token(data: dict):
    to_encode = data.copy()
    expires_in = datetime.now(timezone.utc) + timedelta(minutes=int(appConfig['access_token_expiry_minutes']))
    to_encode['exp'] = expires_in
    token = jwt.encode(
        to_encode,
        appConfig['jwt_secret'],
        algorithm=appConfig['jwt_algorithm']
    )
    return token

def create_refresh_token():
    token = secrets.token_hex(32)
    return token