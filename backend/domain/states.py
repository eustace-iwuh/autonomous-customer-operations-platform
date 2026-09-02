from enum import Enum


class CaseStatus(str, Enum):
    RECEIVED = "RECEIVED"
    CLASSIFYING = "CLASSIFYING"
    CLASSIFIED = "CLASSIFIED"
    PLANNING = "PLANNING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    EXECUTING = "EXECUTING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    ESCALATED = "ESCALATED"
    CLOSED = "CLOSED"


class CasePriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ActionType(str, Enum):
    SEND_EMAIL = "SEND_EMAIL"
    ISSUE_REFUND = "ISSUE_REFUND"
    UPDATE_CUSTOMER = "UPDATE_CUSTOMER"
    CREATE_TICKET = "CREATE_TICKET"
    ESCALATE_CASE = "ESCALATE_CASE"


class ActionStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTING = "EXECUTING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


CASE_ALLOWED_TRANSITIONS: dict[CaseStatus, set[CaseStatus]] = {
    CaseStatus.RECEIVED: {
        CaseStatus.CLASSIFYING,
    },

    CaseStatus.CLASSIFYING: {
        CaseStatus.CLASSIFIED,
        CaseStatus.ESCALATED,
    },

    CaseStatus.CLASSIFIED: {
        CaseStatus.PLANNING,
        CaseStatus.ESCALATED,
    },

    CaseStatus.PLANNING: {
        CaseStatus.AWAITING_APPROVAL,
        CaseStatus.APPROVED,
        CaseStatus.ESCALATED,
    },

    CaseStatus.AWAITING_APPROVAL: {
        CaseStatus.APPROVED,
        CaseStatus.ESCALATED,
    },

    CaseStatus.APPROVED: {
        CaseStatus.EXECUTING,
    },

    CaseStatus.EXECUTING: {
        CaseStatus.SUCCEEDED,
        CaseStatus.FAILED,
    },

    CaseStatus.FAILED: {
        CaseStatus.PLANNING,
        CaseStatus.EXECUTING,
        CaseStatus.ESCALATED,
    },

    CaseStatus.SUCCEEDED: {
        CaseStatus.CLOSED,
    },

    CaseStatus.ESCALATED: {
        CaseStatus.CLOSED,
    },

    CaseStatus.CLOSED: set(),
}


ACTION_ALLOWED_TRANSITIONS: dict[ActionStatus, set[ActionStatus]] = {
    ActionStatus.PENDING: {
        ActionStatus.APPROVED,
        ActionStatus.REJECTED,
        ActionStatus.CANCELLED,
    },

    ActionStatus.APPROVED: {
        ActionStatus.EXECUTING,
        ActionStatus.CANCELLED,
    },

    ActionStatus.EXECUTING: {
        ActionStatus.SUCCEEDED,
        ActionStatus.FAILED,
    },

    ActionStatus.FAILED: {
        ActionStatus.EXECUTING,
        ActionStatus.CANCELLED,
    },

    ActionStatus.SUCCEEDED: set(),

    ActionStatus.REJECTED: set(),

    ActionStatus.CANCELLED: set(),
}


def can_transition(
    current: CaseStatus,
    target: CaseStatus,
) -> bool:
    return target in CASE_ALLOWED_TRANSITIONS.get(current, set())


def validate_transition(
    current: CaseStatus,
    target: CaseStatus,
) -> None:
    if not can_transition(current, target):
        raise ValueError(
            f"Invalid case transition: "
            f"{current.value} -> {target.value}"
        )


def can_action_transition(
    current: ActionStatus,
    target: ActionStatus,
) -> bool:
    return target in ACTION_ALLOWED_TRANSITIONS.get(
        current,
        set(),
    )


def validate_action_transition(
    current: ActionStatus,
    target: ActionStatus,
) -> None:
    if not can_action_transition(current, target):
        raise ValueError(
            f"Invalid action transition: "
            f"{current.value} -> {target.value}"
        )