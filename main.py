import os
import pathlib
import logging
from dotenv import load_dotenv

import requests
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from cachecontrol import CacheControl
import google.auth.transport.requests

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load required environment variables
SECRET_KEY = os.getenv("SECRET_KEY")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost/callback")  # Use a default for local dev

# Validate essential environment variables
if not SECRET_KEY or not GOOGLE_CLIENT_ID:
    raise ValueError("SECRET_KEY and GOOGLE_CLIENT_ID must be set in the environment.")

# Initialize FastAPI app
app = FastAPI()

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Allow insecure transport for development
if os.getenv("ENVIRONMENT", "development") == "development":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# Path to Google OAuth secrets file
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "secret.json")

# Set up Google OAuth Flow
try:
    flow = Flow.from_client_secrets_file(
        client_secrets_file=client_secrets_file,
        scopes=[
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
            "openid",
        ],
        redirect_uri=REDIRECT_URI,
    )
except Exception as e:
    logger.error(f"Failed to initialize OAuth flow: {e}")
    raise

# Dependency: Login Required
def login_is_required(request: Request):
    if "google_id" not in request.session:
        logger.warning("Unauthorized access attempt.")
        raise HTTPException(status_code=401, detail="Authorization required")
    return request


@app.get("/login")
async def login(request: Request):
    """
    Handles the login process by redirecting the user to the Google authorization URL.
    """
    try:
        authorization_url, state = flow.authorization_url()
        request.session["state"] = state
        logger.info(f"Generated authorization URL: {authorization_url}")
        return RedirectResponse(authorization_url)
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate login URL.")


@app.get("/callback")
async def callback(request: Request):
     flow.fetch_token(authorization_response=str(request.url))
     credentials = flow.credentials

        # Verify ID token
     request_session = requests.session()
     cached_session = CacheControl(request_session)
     token_request = google.auth.transport.requests.Request(session=cached_session)

     id_info = id_token.verify_oauth2_token(
     id_token=credentials._id_token,
     request=token_request,
     audience=GOOGLE_CLIENT_ID,
    )

        # Store user info in session
     request.session["google_id"] = id_info.get("sub")
     request.session["name"] = id_info.get("name")
     logger.info(f"User {id_info.get('name')} logged in successfully.")
     return RedirectResponse("/protected_area")


@app.get("/logout")
async def logout(request: Request):
    """
    Clears the user's session and redirects to the home page.
    """
    request.session.clear()
    logger.info("User logged out.")
    return RedirectResponse("/")


@app.get("/", response_class=HTMLResponse)
async def index():
    """
    Home page with a login link.
    """
    return """
    <html>
        <body>
            <h1>Hello Devfest Lagos!</h1>
            <a href='/login' style='text-decoration:none;'>
                <button style='padding:10px 20px; background-color: #4CAF50; color: white; border: none; cursor: pointer;'>Login</button>
            </a>
        </body>
    </html>
    """


@app.get("/protected_area", response_class=HTMLResponse)
async def protected_area(request: Request = Depends(login_is_required)):
    """
    Protected area accessible only after login.
    """
    name = request.session.get("name")
    return f"""
    <html>
        <body>
            <h1>Hello {name}!</h1>
            <p>Welcome to the demo on OAuth2.0. You are now logged in using Google OAuth.</p>
            <a href='/logout' style='text-decoration:none;'>
                <button style='padding:10px 20px; background-color: #4CAF50; color: white; border: none; cursor: pointer;'>Logout</button>
            </a>
        </body>
    </html>
    """

