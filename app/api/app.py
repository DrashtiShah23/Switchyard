"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import changes, health
from app.config import Settings, sqlite_path_from_url
from app.repositories.sqlite import SqliteChangeRepository
from app.services.change_service import ChangeService


def create_app(
    *,
    settings: Settings | None = None,
    change_service: ChangeService | None = None,
) -> FastAPI:
    """Build the API app with injectable settings/service for tests."""
    resolved_settings = settings or Settings.from_env()
    if change_service is None:
        repository = SqliteChangeRepository(sqlite_path_from_url(resolved_settings.database_url))
        change_service = ChangeService(repository)

    app = FastAPI(
        title="Switchyard",
        description=(
            "Network change control plane API. "
            "Callers submit typed change requests; the API persists normalized "
            "ChangeSpecifications. Terraform/OPA/apply are later milestones."
        ),
        version="0.1.0",
    )
    app.state.settings = resolved_settings
    app.state.change_service = change_service

    app.include_router(health.router)
    app.include_router(changes.router)
    return app
