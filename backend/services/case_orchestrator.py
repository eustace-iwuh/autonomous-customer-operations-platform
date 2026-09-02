from typing import Any

from sqlalchemy.orm import Session

from backend.database.models import Action, Case
from backend.domain.states import ActionStatus, CaseStatus
from backend.services.action_service import ActionService
from backend.services.case_service import CaseService


class CaseOrchestrator:
    def __init__(self, db: Session):
        self.db = db
        self.case_service = CaseService(db)
        self.action_service = ActionService(db)

    def get_case(self, case_id: int) -> Case:
        case = self.case_service.get_case(case_id)

        if case is None:
            raise ValueError(f"Case not found: {case_id}")

        return case

    def get_actions(self, case_id: int) -> list[Action]:
        self.get_case(case_id)

        return self.action_service.list_actions_for_case(case_id)

    def execute_approved_actions(
        self,
        *,
        case_id: int,
    ) -> dict[str, Any]:
        case = self.get_case(case_id)

        actions = self.action_service.list_actions_for_case(
            case.id
        )

        if not actions:
            raise ValueError(
                f"Case {case_id} has no actions to execute"
            )

        approved_actions = [
            action
            for action in actions
            if action.status == ActionStatus.APPROVED.value
        ]

        if not approved_actions:
            raise ValueError(
                f"Case {case_id} has no approved actions to execute"
            )

        self.case_service.transition_case(
            case_id=case.id,
            target_status=CaseStatus.EXECUTING,
            actor_type="SYSTEM",
            description=(
                "Case execution started by the "
                "case orchestrator."
            ),
            payload={
                "approved_action_count": len(
                    approved_actions
                ),
            },
        )

        results: list[dict[str, Any]] = []

        for action in approved_actions:
            executed_action = self.action_service.execute_action(
                action_id=action.id
            )

            results.append(
                {
                    "action_id": executed_action.id,
                    "status": executed_action.status,
                    "result": executed_action.result,
                }
            )

        failed_actions = [
            result
            for result in results
            if result["status"] == ActionStatus.FAILED.value
        ]

        if failed_actions:
            self.case_service.transition_case(
                case_id=case.id,
                target_status=CaseStatus.FAILED,
                actor_type="SYSTEM",
                description=(
                    "Case execution failed because "
                    "one or more actions failed."
                ),
                payload={
                    "failed_action_count": len(
                        failed_actions
                    ),
                },
            )
        else:
            self.case_service.transition_case(
                case_id=case.id,
                target_status=CaseStatus.SUCCEEDED,
                actor_type="SYSTEM",
                description=(
                    "Case execution completed successfully."
                ),
                payload={
                    "successful_action_count": len(
                        results
                    ),
                },
            )

        return {
            "case_id": case.id,
            "actions_processed": len(results),
            "results": results,
            "case_status": case.status,
        }