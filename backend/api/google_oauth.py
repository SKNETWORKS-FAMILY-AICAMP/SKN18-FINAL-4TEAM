import requests
from django.conf import settings


class GoogleOAuthError(Exception):
    pass


def exchange_code_for_tokens(code: str, redirect_uri: str):
    payload = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    resp = requests.post("https://oauth2.googleapis.com/token", data=payload, timeout=10)
    if not resp.ok:
        raise GoogleOAuthError(f"Failed to exchange code: {resp.text}")
    return resp.json()


def fetch_userinfo(access_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get("https://www.googleapis.com/oauth2/v3/userinfo", headers=headers, timeout=10)
    if not resp.ok:
        raise GoogleOAuthError(f"Failed to fetch userinfo: {resp.text}")
    data = resp.json()
    return {
        "sub": data.get("sub"),
        "email": data.get("email"),
        "name": data.get("name") or data.get("given_name") or "",
    }
