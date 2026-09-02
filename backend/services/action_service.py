from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from backend.database.models import Action, ActionExecution, Case
from backend.domain.states import (
    ActionStatus,
    ActionType,
    validate_action_transition,
)
from backend.execution.engine import ExecutionEngine


class ActionService:
    def __init__(self, db: Session):
        self.db = db
        self.execution_engine = ExecutionEngine()

    def create_action(
        self,
        *,
        case_id: int,
        action_type: ActionType,
        payload: dict[str, Any] | None = None,
    ) -> Action:
        case = (
            self.db.query(Case)
            .filter(Case.id == case_id)
            .first()
        )

        if case is None:
            raise ValueError(f"Case not found: {case_id}")

        action = Action(
            case_id=case_id,
            action_type=action_type.value,
            status=ActionStatus.PENDING.value,
            payload=payload or {},
        )

        self.db.add(action)
        self.db.flush()

        return action

    def get_action(
        self,
        action_id: int,
    ) -> Action | None:
        return (
            self.db.query(Action)
            .filter(Action.id == action_id)
            .first()
        )

    def list_actions_for_case(
        self,
        case_id: int,
    ) -> list[Action]:
        return (
            self.db.query(Action)
            .filter(Action.case_id == case_id)
            .order_by(Action.created_at.asc())
            .all()
        )

    def transition_action(
        self,
        *,
        action_id: int,
        target_status: ActionStatus,
        result: dict[str, Any] | None = None,
    ) -> Action:
        action = self.get_action(action_id)

        if action is None:
            raise ValueError(f"Action not found: {action_id}")

        current_status = ActionStatus(action.status)

        validate_action_transition(
            current=current_status,
            target=target_status,
        )

        action.status = target_status.value

        if result is not None:
            action.result = result

        self.db.flush()

        return action

    def execute_action(
        self,
        *,
        action_id: int,
    ) -> Action:
        action = self.get_action(action_id)

        if action is None:
            raise ValueError(f"Action {action_id} not found")

        current_status = ActionStatus(action.status)

        validate_action_transition(
            current=current_status,
            target=ActionStatus.EXECUTING,
        )

        started_at = datetime.utcnow()

        execution = ActionExecution(
            action_id=action.id,
            status=ActionStatus.EXECUTING.value,
            started_at=started_at,
        )

        self.db.add(execution)
        self.db.flush()

        action.status = ActionStatus.EXECUTING.value
        self.db.flush()

        try:
            result = self.execution_engine.execute(action)

            completed_at = datetime.utcnow()

            execution.status = ActionStatus.SUCCEEDED.value
            execution.result = result
            execution.completed_at = completed_at

            action.status = ActionStatus.SUCCEEDED.value
            action.result = result

            self.db.flush()

            return action

        except Exception as exc:
            completed_at = datetime.utcnow()

            execution.status = ActionStatus.FAILED.value
            execution.error_message = str(exc)
            execution.completed_at = completed_at

            action.status = ActionStatus.FAILED.value
            action.result = {
                "success": False,
                "error": str(exc),
            }

            self.db.flush()

        return action

    def list_execution_history(
        self,
        *,
        action_id: int,
    ) -> list[ActionExecution]:
        return (
            self.db.query(ActionExecution)
            .filter(ActionExecution.action_id == action_id)
            .order_by(ActionExecution.created_at.asc())
            .all()
        )