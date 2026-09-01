from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend.api.dependencies import (
    get_current_user,
    require_role,
)
from backend.database.connection import get_db
from backend.database.models import User
from backend.domain.states import CasePriority, CaseStatus
from backend.services.case_service import CaseService


router = APIRouter(prefix="/cases", tags=["cases"])


class CreateCaseRequest(BaseModel):
    customer_id: int
    case_number: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1, max_length=5000)
    priority: CasePriority = CasePriority.MEDIUM


class TransitionCaseRequest(BaseModel):
    target_status: CaseStatus
    actor_type: str = Field(
        default="SYSTEM",
        min_length=1,
        max_length=50,
    )
    description: str | None = None
    payload: dict | None = None


class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_number: str
    customer_id: int
    title: str
    description: str
    status: str
    priority: str


@router.post(
    "",
    response_model=CaseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_case(
    request: CreateCaseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CaseService(db)

    try:
        case = service.create_case(
            case_number=request.case_number,
            customer_id=request.customer_id,
            title=request.title,
            description=request.description,
            priority=request.priority,
        )

        db.commit()
        db.refresh(case)

        return case

    except Exception:
        db.rollback()
        raise


@router.post(
    "/{case_id}/transition",
    response_model=CaseResponse,
)
def transition_case(
    case_id: int,
    request: TransitionCaseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CaseService(db)

    try:
        case = service.transition_case(
            case_id=case_id,
            target_status=request.target_status,
            actor_type=request.actor_type,
            description=request.description,
            payload=request.payload,
        )

        db.commit()
        db.refresh(case)

        return case

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except Exception:
        db.rollback()
        raise


@router.post(
    "/{case_id}/approve",
    response_model=CaseResponse,
)
def approve_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("MANAGER", "ADMIN")
    ),
):
    service = CaseService(db)

    try:
        case = service.transition_case(
            case_id=case_id,
            target_status=CaseStatus.APPROVED,
            actor_type=current_user.role,
            description=(
                f"Case approved by {current_user.role}."
            ),
            payload={
                "approved_by_user_id": current_user.id,
                "approved_by_email": current_user.email,
            },
        )

        db.commit()
        db.refresh(case)

        return case

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except Exception:
        db.rollback()
        raise


@router.get(
    "/{case_id}",
    response_model=CaseResponse,
)
def get_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CaseService(db)

    case = service.get_case(case_id)

    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case not found: {case_id}",
        )

    return case


@router.get(
    "",
    response_model=list[CaseResponse],
)
def list_cases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CaseService(db)

    return service.list_cases()