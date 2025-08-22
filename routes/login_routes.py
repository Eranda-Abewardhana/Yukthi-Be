from fastapi import APIRouter, Request, HTTPException
from starlette.config import Config
from authlib.integrations.starlette_client import OAuth
from starlette.responses import JSONResponse, RedirectResponse
from fastapi.encoders import jsonable_encoder
from dotenv import load_dotenv
from datetime import datetime
import os
from data_modals.pydantic_models.response_modals import ErrorResponse
from utils.db.connect_to_my_sql import db
from utils.db.user_utils import create_user_if_not_exists
from utils.jwt.pyjwt import create_jwt

load_dotenv()

login_router = APIRouter()


# Load secrets from .env
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
SECRET_KEY = os.getenv("SECRET_KEY")

# Configure OAuth
config = Config(environ={
    "GOOGLE_CLIENT_ID": GOOGLE_CLIENT_ID,
    "GOOGLE_CLIENT_SECRET": GOOGLE_CLIENT_SECRET
})
oauth = OAuth(config)
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        "scope": "openid email profile",
        "response_type": "code"
    },
)


@login_router.get("/login")
async def login(request: Request):
    try:
        redirect_uri = request.url_for('auth_callback')
        return await oauth.google.authorize_redirect(request, redirect_uri)
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content=jsonable_encoder(ErrorResponse(
                detail=str(e),
                status="error",
                links=[],
                timestamp=datetime.utcnow()
            ))
        )


@login_router.get("/auth/callback")
async def auth_callback(request: Request):
    try:
        token_data = await oauth.google.authorize_access_token(request)
        print("Token data:", token_data)

        # Fallback to userinfo if id_token missing
        if "id_token" in token_data:
            user_info = token_data.get("userinfo") or await oauth.google.userinfo(request, token=token_data)
        else:
            user_info = await oauth.google.userinfo(request, token=token_data)

        email = user_info.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Email not found in Google response")

        # Create or retrieve user
        user = create_user_if_not_exists(email=email, db=db)

        # Generate JWT
        jwt_token = create_jwt(user_info)

        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        redirect_url = f"{frontend_url}/chat?token={jwt_token}&name={user_info.get('name')}&email={email}"
        return RedirectResponse(url=redirect_url)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content=jsonable_encoder(ErrorResponse(
                detail=f"Auth callback error: {str(e)}",
                status="error",
                links=[],
                timestamp=datetime.utcnow()
            ))
        )


@login_router.get("/logout")
async def logout(request: Request):
    try:
        request.session.pop("user", None)
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Logged out"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content=jsonable_encoder(ErrorResponse(
                detail=f"Logout failed: {str(e)}",
                status="error",
                links=[],
                timestamp=datetime.utcnow()
            ))
        )


@login_router.get("/me")
async def get_user(request: Request):
    user = request.session.get("user")
    if user:
        return {
            "status": "success",
            "user": user
        }
    return JSONResponse(
        status_code=401,
        content=jsonable_encoder(ErrorResponse(
            detail="Not logged in",
            status="unauthorized",
            links=[],
            timestamp=datetime.utcnow()
        ))
    )
