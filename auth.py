from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import jwt, os, datetime
from datetime import timezone
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()
security = HTTPBearer()

APP_SECRET = os.environ.get("APP_SECRET")
if not APP_SECRET:
    raise RuntimeError("APP_SECRET not set in environment!")

# hard-coded two users for the assignment
users = {
    'alice': {'password': 'secret', 'admin': False},
    'admin':   {'password': 'pass', 'admin': True}
}

class LoginRequest(BaseModel):
    username: str
    password: str

def generate_access_token(username: str, is_admin: bool):
    payload = {
        'username': username,
        'admin': is_admin,
        'exp': datetime.datetime.now(timezone.utc) + datetime.timedelta(minutes=30)
    }
    token = jwt.encode(payload, APP_SECRET, algorithm='HS256')
    return token

def authenticate_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials or credentials.scheme != 'Bearer':
        raise HTTPException(status_code=401, detail='Unauthorized')
    token = credentials.credentials
    try:
        user = jwt.decode(token, APP_SECRET, algorithms=['HS256'])
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail='Token expired')
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail='Invalid token')

@router.post('/login')
async def login(data: LoginRequest):
    """
    Login endpoint. Accepts username and password as JSON in request body.
    """
    user = users.get(data.username)
    if not user or user['password'] != data.password:
        raise HTTPException(status_code=401, detail='Unauthorized')
    token = generate_access_token(data.username, user['admin'])
    return {'authToken': token}
