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
        recipient = action.payload.get("recipient")
        subject = action.payload.get("subject")

        if not recipient:
            raise ValueError(
                "Email recipient is required."
            )

        if not subject:
            raise ValueError(
                "Email subject is required."
            )

        return {
            "success": True,
            "action_type": ActionType.SEND_EMAIL.value,
            "message": "Email execution simulated successfully.",
            "recipient": recipient,
            "subject": subject,
        }

    def _execute_issue_refund(
        self,
        action: Action,
    ) -> dict[str, Any]:
        amount = action.payload.get("amount")

        if amount is None:
            raise ValueError(
                "Refund amount is required."
            )

        if amount <= 0:
            raise ValueError(
                "Refund amount must be greater than zero."
            )

        return {
            "success": True,
            "action_type": ActionType.ISSUE_REFUND.value,
            "message": "Refund execution simulated successfully.",
            "amount": amount,
        }

    def _execute_update_customer(
        self,
        action: Action,
    ) -> dict[str, Any]:
        updates = action.payload

        if not updates:
            raise ValueError(
                "Customer update fields are required."
            )

        return {
            "success": True,
            "action_type": ActionType.UPDATE_CUSTOMER.value,
            "message": "Customer update execution simulated successfully.",
            "updated_fields": updates,
        }

    def _execute_create_ticket(
        self,
        action: Action,
    ) -> dict[str, Any]:
        subject = action.payload.get("subject")

        if not subject:
            raise ValueError(
                "Ticket subject is required."
            )

        return {
            "success": True,
            "action_type": ActionType.CREATE_TICKET.value,
            "message": "Ticket creation simulated successfully.",
            "subject": subject,
        }


    def _execute_escalate_case(
        self,
        action: Action,
    ) -> dict[str, Any]:
        reason = action.payload.get("reason")

        if not reason:
            raise ValueError(
                "Escalation reason is required."
            )

        return {
            "success": True,
            "action_type": ActionType.ESCALATE_CASE.value,
            "message": "Case escalation simulated successfully.",
            "reason": reason,
        }