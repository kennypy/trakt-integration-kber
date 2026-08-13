import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from aiohttp import ClientResponseError
from homeassistant.exceptions import ConfigEntryAuthFailed
from pytest import raises

from custom_components.trakt_tv.apis.trakt import TraktApi
from custom_components.trakt_tv.const import DOMAIN


class MockResponse:
    def __init__(self, status: int, text: str = "", headers: dict | None = None):
        self.status = status
        self._text = text
        self.headers = headers or {}

    @property
    def ok(self):
        return 200 <= self.status < 300

    async def text(self):
        return self._text

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


def test_request_allow_no_content_returns_none_for_204():
    hass = SimpleNamespace(data={DOMAIN: {"configuration": {"client_id": "client"}}})
    oauth_session = SimpleNamespace(valid_token=True, token={"access_token": "token"})
    web_session = SimpleNamespace(
        request=AsyncMock(return_value=MockResponse(status=204, text=""))
    )
    api = TraktApi(websession=web_session, oauth_session=oauth_session, hass=hass)

    answer = asyncio.run(api.request("get", "users/me/watching", allow_no_content=True))

    assert answer is None


def test_request_allow_no_content_returns_none_for_empty_body():
    hass = SimpleNamespace(data={DOMAIN: {"configuration": {"client_id": "client"}}})
    oauth_session = SimpleNamespace(valid_token=True, token={"access_token": "token"})
    web_session = SimpleNamespace(
        request=AsyncMock(return_value=MockResponse(status=200, text=""))
    )
    api = TraktApi(websession=web_session, oauth_session=oauth_session, hass=hass)

    answer = asyncio.run(api.request("get", "users/me/watching", allow_no_content=True))

    assert answer is None


def test_request_raises_auth_failed_on_401():
    hass = SimpleNamespace(data={DOMAIN: {"configuration": {"client_id": "client"}}})
    oauth_session = SimpleNamespace(valid_token=True, token={"access_token": "token"})
    web_session = SimpleNamespace(
        request=AsyncMock(return_value=MockResponse(status=401, text="invalid token"))
    )
    api = TraktApi(websession=web_session, oauth_session=oauth_session, hass=hass)

    with raises(ConfigEntryAuthFailed):
        asyncio.run(api.request("get", "users/me/watching"))

    # 401 must not be retried
    assert web_session.request.await_count == 1


def test_access_token_refresh_failure_raises_auth_failed():
    hass = SimpleNamespace(data={DOMAIN: {"configuration": {"client_id": "client"}}})
    oauth_session = SimpleNamespace(
        valid_token=False,
        token={"access_token": "token"},
        async_ensure_token_valid=AsyncMock(
            side_effect=ClientResponseError(None, (), status=400)
        ),
    )
    api = TraktApi(websession=SimpleNamespace(), oauth_session=oauth_session, hass=hass)

    with raises(ConfigEntryAuthFailed):
        asyncio.run(api.async_get_access_token())


def test_access_token_refresh_server_error_is_not_auth_failure():
    hass = SimpleNamespace(data={DOMAIN: {"configuration": {"client_id": "client"}}})
    oauth_session = SimpleNamespace(
        valid_token=False,
        token={"access_token": "token"},
        async_ensure_token_valid=AsyncMock(
            side_effect=ClientResponseError(None, (), status=502)
        ),
    )
    api = TraktApi(websession=SimpleNamespace(), oauth_session=oauth_session, hass=hass)

    with raises(ClientResponseError):
        asyncio.run(api.async_get_access_token())
