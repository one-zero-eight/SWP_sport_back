import logging
from ast import literal_eval
from base64 import urlsafe_b64decode
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, Depends, HTTPException, responses, Query

from app.api.utils.db import get_db
from app.api.utils.link import form_link
from app.api.utils.security import get_current_user, process_token
from app.core import config
from app.core.security import get_code_retrieve_params, get_token_retrieve_params
from app.db import find_student, create_student
from app.models.token import TokenRetrieval
from app.models.user import TokenUser

router = APIRouter()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@router.post("/login/test-token", tags=["login"], response_model=TokenUser)
def test_token(current_user: dict = Depends(get_current_user)):
    """
    Test access token
    """
    return current_user


@router.get("/loginform", tags=["login"])
def login_from_form():
    return responses.RedirectResponse(
        url="/api/login?state=login&redirect_uri=https%3A%2F%2Fhelpdesk.innopolis.university"
    )


@router.get("/login", tags=["login"], response_class=responses.HTMLResponse)
def loginSSO(state: str, redirect_uri: str):
    params = get_code_retrieve_params({"state": state, "redirect_uri": redirect_uri})
    auth_url = f"{config.OAUTH_AUTHORIZATION_BASE_URL}?{urlencode(params)}"
    return responses.RedirectResponse(url=auth_url)


@router.get("/get_code/get_code")
def process_code(code: str, state: str, client_request_id: str = Query(..., alias="client-request-id"),
                 db=Depends(get_db)):
    state = literal_eval(urlsafe_b64decode(state.encode()).decode())
    if not state["redirect_uri"].startswith(config.BASE_URL):
        raise HTTPException(status_code=400,
                            detail=f"Redirect uri must start with {config.BASE_URL} Got {state['redirect_uri']}")

    params = get_token_retrieve_params(code)
    resp = requests.post(config.OAUTH_TOKEN_URL, data=params, headers={
        'content-type': 'application/json'
    })

    data = resp.json()

    if data.get("error", None):
        raise HTTPException(status_code=401, detail=data)
    else:
        tokens = TokenRetrieval(**data)
        if state["redirect_uri"].startswith(config.DOCS_BASE_URL):
            url = form_link(state["redirect_uri"],
                            {
                                "state": state["state"],
                                "access_token": tokens.access_token,
                                "expires_in": tokens.expires_in,
                            }
                            )
        else:
            url = form_link(state["redirect_uri"],
                            {
                                "state": state["state"]
                            }
                            )
    token_user = process_token(tokens.access_token)
    if token_user.is_student() and find_student(db, token_user.email) is None:
        create_student(db, token_user.first_name, token_user.last_name, token_user.email)

    # TODO: create trainers and admins
    response = responses.RedirectResponse(
        url=url,
        status_code=302
    )
    response.set_cookie(key="access_token", value=tokens.access_token, expires=tokens.expires_in)
    # response.set_cookie(key="id_token", value=f"{tokens.id_token}", expires=tokens.expires_in)
    response.set_cookie(key="refresh_token", value=f"{tokens.refresh_token}",
                        expires=tokens.refresh_token_expires_in)

    return response
