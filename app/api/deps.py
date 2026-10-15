"""FastAPI dependency wiring."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.auth import AuthenticatedActor
from app.config import Settings
from app.services.change_service import ChangeService

_bearer = HTTPBearer(auto_error=False)
BearerCredentials = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(_bearer),
]


def get_change_service(request: Request) -> ChangeService:
    service = getattr(request.app.state, "change_service", None)
    if not isinstance(service, ChangeService):
        raise RuntimeError("change_service is not configured on the application")
    return service


def get_authenticated_actor(
    request: Request,
    credentials: BearerCredentials,
) -> AuthenticatedActor:
    settings: Settings | None = getattr(request.app.state, "settings", None)
    if settings is None:
        raise RuntimeError("settings are not configured on the application")
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing or invalid Authorization bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    actor = settings.api_keys.get(credentials.credentials)
    if actor is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return AuthenticatedActor(
        actor=actor,
        api_key_id=f"key-{credentials.credentials[:4]}",
    )


ChangeServiceDep = Annotated[ChangeService, Depends(get_change_service)]
ActorDep = Annotated[AuthenticatedActor, Depends(get_authenticated_actor)]
