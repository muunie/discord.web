import asyncio
import weakref

from typing import Optional, Union, List

from .http import Route, HTTPClient
from .token import AccessTokenResponse
from .user import User


__all__: tuple = (
    "OAuth2Client",
)

class OAuth2Client:
    def __init__(
        self,
        *,
        client_id: int,
        client_secret: str,
        redirect_uri: str,
        scopes: Optional[List[str]] = None
    ):
        self._id = client_id
        self._auth = client_secret
        self._redirect = redirect_uri
        self._scopes = " ".join(scopes) if scopes is not None else None

        self.http = HTTPClient()
        self.http._state_info.update({
            "client_id": self._id,
            "client_secret": self._auth,
            "redirect_uri": self._redirect,
            "scopes": self._scopes
        })

        self._user_cache = weakref.WeakValueDictionary()
        

    async def exchange_code(self, code: str) -> AccessTokenResponse:
        route = Route("POST", "/oauth2/token")
        post_data = {
            "client_id": self._id,
            "client_secret": self._auth,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self._redirect
        }
        if self._scopes is not None:
            post_data["scope"] = self._scopes
        request_data = await self.http.request(route, data=post_data)
        token_resp = AccessTokenResponse(data=request_data)
        return token_resp

    async def refresh_token(self, refresh_token: Union[str, AccessTokenResponse]) -> AccessTokenResponse:
        refresh_token = (
            refresh_token if isinstance(refresh_token, str) else refresh_token.token
        )
        route = Route("POST", "/oauth2/token")
        post_data = {
            "client_id": self._id,
            "client_secret": self._auth,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        request_data = await self.http.request(route, data=post_data)
        token_resp = AccessTokenResponse(data=request_data)
        return token_resp

    async def fetch_user(self, access_token_response: AccessTokenResponse) -> User:
        access_token = access_token_response.token
        route = Route("GET", "/users/@me")
        headers = {"Authorization": "Bearer {}".format(access_token)}
        resp = await self.http.request(route, headers=headers)
        user = User(http = self.http, data = resp, acr = access_token_response)
        self._user_cache.update({
            user.id: user
        })
        return user

    def get_user(self, id: int) -> Optional[User]:
        user = self._user_cache.get(id)
        return user

    async def close(self):
        await self.http.close()



    