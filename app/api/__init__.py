"""HTTP API layer — routes and auth. No Terraform orchestration here."""

from app.api.app import create_app

__all__ = ["create_app"]
