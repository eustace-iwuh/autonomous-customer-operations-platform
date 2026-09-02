from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from backend.api.dependencies import get_current_user
from backend.database.connection import get_db
from backend.database.models import Action, ActionExecution, User
from backend.domain.states import ActionStatus, ActionType
from backend.services.action_service import ActionService


router = APIRouter(prefix="/actions", tags=["actions"])


class CreateActionRequest(BaseModel):
    case_id: int
    action_type: ActionType
    payload: dict | None = None


class TransitionActionRequest(BaseModel):
    target_status: ActionStatus
    result: dict | None = None


class ActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    action_type: str
    status: str
    payload: dict
    result: dict | None


class ActionExecutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action_id: int
    status: str
    result: dict | None
    error_message: str | None
    started_at: datetime
    completed_at: datetime | None
    created_at: datetime


@router.post(
    "",
    response_model=ActionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_action(
    request: CreateActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ActionService(db)

    try:
        action = service.create_action(
            case_id=request.case_id,
            action_type=request.action_type,
            payload=request.payload,
        )

        db.commit()
        db.refresh(action)

        return action

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    except Exception:
        db.rollback()
        raise


@router.get(
    "/{action_id}/executions",
    response_model=list[ActionExecutionResponse],
)
def list_execution_history(
    action_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ActionService(db)

    action = service.get_action(action_id)

    if action is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action not found: {action_id}",
        )

    return service.list_execution_history(
        action_id=action_id,
    )


@router.get(
    "/{action_id}",
    response_model=ActionResponse,
)
def get_action(
    action_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ActionService(db)

    action = service.get_action(action_id)

    if action is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action not found: {action_id}",
        )

    return action


@router.get(
    "/case/{case_id}",
    response_model=list[ActionResponse],
)
def list_case_actions(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ActionService(db)

    return service.list_actions_for_case(case_id)


@router.post(
    "/{action_id}/transition",
    response_model=ActionResponse,
)
def transition_action(
    action_id: int,
    request: TransitionActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ActionService(db)

    try:
        action = service.transition_action(
            action_id=action_id,
            target_status=request.target_status,
            result=request.result,
        )

        db.commit()
        db.refresh(action)

        return action

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
    "/{action_id}/execute",
    response_model=ActionResponse,
)
def execute_action(
    action_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ActionService(db)

    try:
        action = service.execute_action(
            action_id=action_id,
        )

        db.commit()
        db.refresh(action)

        return action

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except Exception:
        db.rollback()
        raise