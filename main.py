import os
import pathlib
from dotenv import load_dotenv

import requests
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  

client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "secret.json")

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="http://localhost/callback"
)


def login_is_required(request: Request):
    if "google_id" not in request.session:
        raise HTTPException(status_code=401, detail="Authorization required")


@app.get("/login")
async def login(request: Request):
    authorization_url, state = flow.authorization_url()
    request.session["state"] = state
    return RedirectResponse(authorization_url)


@app.get("/callback")
async def callback(request: Request):
    if not request.session["state"] == request.query_params["state"]:
        raise HTTPException(status_code=500, detail="State does not match!")
    
    flow.fetch_token(authorization_response=str(request.url))
    
    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )

    request.session["google_id"] = id_info.get("sub")
    request.session["name"] = id_info.get("name")
    return RedirectResponse("/protected_area")


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/")



@app.get("/", response_class=HTMLResponse)
async def index():
    return """
    <html>
        <body>
            <h1>Hello Devfest Lagossssss!</h1>
            <a href='/login' style='text-decoration:none;'>
                <button style='padding:10px 20px; background-color: #4CAF50; color: white; border: none; cursor: pointer;'>Login</button>
            </a>
        </body>
    </html>
    """



@app.get("/protected_area", response_class=HTMLResponse)
async def protected_area(request: Request):
    name = request.session.get("name")
    return f"""
    <html>
        <body>
            <h1>Hello {name}!</h1>
            <p> Welcome to Devfest Lagos Codelab </p>
            <a href='/logout' style='text-decoration:none;'>
                <button style='padding:10px 20px; background-color: #4CAF50; color: white; border: none; cursor: pointer;'>Logout</button>
            </a>
        </body>
    </html>
    """
