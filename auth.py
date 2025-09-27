import os, hmac, hashlib, base64, requests
import boto3
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from dotenv import load_dotenv
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError, JWTClaimsError

load_dotenv()
security = HTTPBearer()

REGION = os.environ["AWS_REGION"]
USER_POOL_ID = os.environ["USER_POOL_ID"]
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]

#Cognito
JWKS_URL = f"https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json"
jwks = requests.get(JWKS_URL).json()
client = boto3.client("cognito-idp", region_name=REGION)

#Models
class SignUpRequest(BaseModel):
    username: str
    email: str
    password: str

class ConfirmRequest(BaseModel):
    username: str
    confirmation_code: str

class LoginRequest(BaseModel):
    username: str
    password: str

#Helpers
def secret_hash(username: str):
    message = bytes(username + CLIENT_ID, "utf-8")
    key = bytes(CLIENT_SECRET, "utf-8")
    return base64.b64encode(
        hmac.new(key, message, digestmod=hashlib.sha256).digest()
    ).decode()

#Cognito operations
def signup_user(username: str, email: str, password: str):
    try:
        response = client.sign_up(
            ClientId=CLIENT_ID,
            Username=username,
            Password=password,
            SecretHash=secret_hash(username),
            UserAttributes=[{"Name": "email", "Value": email}],
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Signup failed: {e}")

def confirm_user(username: str, code: str):
    try:
        response = client.confirm_sign_up(
            ClientId=CLIENT_ID,
            Username=username,
            ConfirmationCode=code,
            SecretHash=secret_hash(username)
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Confirmation failed: {e}")

def login_user(username: str, password: str):
    try:
        response = client.initiate_auth(
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": username,
                "PASSWORD": password,
                "SECRET_HASH": secret_hash(username),
            },
            ClientId=CLIENT_ID
        )
        return response["AuthenticationResult"]  #contains IdToken, AccessToken and RefreshToken
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Login failed: {e}")

#JWT Verification
def authenticate_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials or credentials.scheme != 'Bearer':
        raise HTTPException(status_code=401, detail='Unauthorized')

    token = credentials.credentials

    try:
        #Get the unverified header to extract the key id (kid)
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header["kid"]

        key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
        if not key:
            raise HTTPException(status_code=401, detail="Invalid token header")

        #Use jose to decode with JWK directly
        payload = jwt.decode(
            token,
            key,  #jose handles jwk dicts directly
            algorithms=["RS256"],
            audience=CLIENT_ID,
            issuer=f"https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}"
        )

        #Check its an ID token 
        if payload.get("token_use") != "id":
            raise HTTPException(status_code=401, detail="Only ID tokens are allowed")

        return {
            "username": payload.get("cognito:username"),
            "sub": payload.get("sub"),
            "email": payload.get("email"),
            "admin": "admin" in payload.get("cognito:groups", []),
            "token_use": payload.get("token_use"),
        }

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTClaimsError as e:
        raise HTTPException(status_code=401, detail=f"Invalid claims: {e}")
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
