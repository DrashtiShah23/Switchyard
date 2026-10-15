"""Change request HTTP routes — transport only, no Terraform orchestration."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, status

from app.api.deps import ActorDep, ChangeServiceDep
from app.api.schemas import (
    ChangeCreateResponse,
    ChangeRequestResponse,
    StageStubResponse,
)
from app.domain.change_request import ChangeRequest
from app.domain.errors import DomainValidationError
from app.domain.ids import RequestId
from app.services.errors import IdempotencyConflictError, NotFoundError

router = APIRouter(prefix="/v1/changes", tags=["changes"])


def _to_request_response(request: ChangeRequest) -> ChangeRequestResponse:
    return ChangeRequestResponse.model_validate(request.to_dict())


@router.post(
    "",
    response_model=ChangeCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_change(
    body: dict[str, Any],
    service: ChangeServiceDep,
    actor: ActorDep,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> ChangeCreateResponse:
    """Create a validated change request and persist its ChangeSpecification."""
    try:
        change_request, specification = service.create_change(
            actor=actor.actor,
            payload=body,
            idempotency_key=idempotency_key,
        )
    except DomainValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except IdempotencyConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return ChangeCreateResponse(
        request=_to_request_response(change_request),
        change_specification=specification.to_dict(),
    )


@router.get("/{request_id}", response_model=ChangeRequestResponse)
def get_change(
    request_id: str, service: ChangeServiceDep, actor: ActorDep
) -> ChangeRequestResponse:
    del actor  # authenticated access required; ownership scoping is a later concern
    try:
        RequestId.parse(request_id)
        change_request = service.get_request(request_id)
    except DomainValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    return _to_request_response(change_request)


@router.get("/{request_id}/plan", response_model=StageStubResponse)
def get_plan(
    request_id: str,
    service: ChangeServiceDep,
    actor: ActorDep,
) -> StageStubResponse:
    del actor
    return _stage_stub(request_id, service, stage="plan")


@router.get("/{request_id}/policy", response_model=StageStubResponse)
def get_policy(
    request_id: str,
    service: ChangeServiceDep,
    actor: ActorDep,
) -> StageStubResponse:
    del actor
    return _stage_stub(request_id, service, stage="policy")


@router.get("/{request_id}/verification", response_model=StageStubResponse)
def get_verification(
    request_id: str,
    service: ChangeServiceDep,
    actor: ActorDep,
) -> StageStubResponse:
    del actor
    return _stage_stub(request_id, service, stage="verification")


def _stage_stub(request_id: str, service: ChangeServiceDep, *, stage: str) -> StageStubResponse:
    try:
        RequestId.parse(request_id)
        change_request = service.get_request(request_id)
    except DomainValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return StageStubResponse(
        request_id=str(change_request.request_id),
        state=change_request.state.value,
        available=False,
        stage=stage,
        detail=(
            f"{stage} results are not produced in Milestone 3; "
            "request is persisted with a normalized change specification only"
        ),
    )
