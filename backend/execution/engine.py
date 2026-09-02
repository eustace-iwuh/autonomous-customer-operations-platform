from typing import Any

from backend.database.models import Action
from backend.domain.states import ActionType


class ExecutionEngine:
    def execute(self, action: Action) -> dict[str, Any]:
        action_type = ActionType(action.action_type)

        if action_type == ActionType.SEND_EMAIL:
            return self._execute_send_email(action)

        if action_type == ActionType.ISSUE_REFUND:
            return self._execute_issue_refund(action)

        if action_type == ActionType.UPDATE_CUSTOMER:
            return self._execute_update_customer(action)

        if action_type == ActionType.CREATE_TICKET:
            return self._execute_create_ticket(action)

        if action_type == ActionType.ESCALATE_CASE:
            return self._execute_escalate_case(action)

        raise ValueError(
            f"Unsupported action type: {action.action_type}"
        )

    def _execute_send_email(
        self,
        action: Action,
    ) -> dict[str, Any]:
        return {
            "success": True,
            "action_type": ActionType.SEND_EMAIL.value,
            "message": "Email execution simulated successfully.",
        }

    def _execute_issue_refund(
        self,
        action: Action,
    ) -> dict[str, Any]:
        return {
            "success": True,
            "action_type": ActionType.ISSUE_REFUND.value,
            "message": "Refund execution simulated successfully.",
        }

    def _execute_update_customer(
        self,
        action: Action,
    ) -> dict[str, Any]:
        return {
            "success": True,
            "action_type": ActionType.UPDATE_CUSTOMER.value,
            "message": "Customer update execution simulated successfully.",
        }

    def _execute_create_ticket(
        self,
        action: Action,
    ) -> dict[str, Any]:
        return {
            "success": True,
            "action_type": ActionType.CREATE_TICKET.value,
            "message": "Ticket creation simulated successfully.",
        }

    def _execute_escalate_case(
        self,
        action: Action,
    ) -> dict[str, Any]:
        return {
            "success": True,
            "action_type": ActionType.ESCALATE_CASE.value,
            "message": "Case escalation simulated successfully.",
        }