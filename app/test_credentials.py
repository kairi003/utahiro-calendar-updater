#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import register
import requests
from google.auth.credentials import TokenState


def test_get_credentials():
    creds = register.get_credentials()
    assert creds.token_state is TokenState.FRESH
    access_token = creds.token
    assert isinstance(access_token, str)
    response = requests.get(
        f"https://www.googleapis.com/oauth2/v3/tokeninfo?access_token={access_token}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.ok
    data = response.json()
    assert isinstance(data, dict)
    assert data.get("scope") == ",".join(register.SCOPES)
