import pytest

from backend.domain.states import (
    ActionStatus,
    can_action_transition,
    validate_action_transition,
)


def test_pending_can_be_approved():
    assert can_action_transition(
        ActionStatus.PENDING,
        ActionStatus.APPROVED,
    )


def test_pending_can_be_rejected():
    assert can_action_transition(
        ActionStatus.PENDING,
        ActionStatus.REJECTED,
    )


def test_approved_can_execute():
    assert can_action_transition(
        ActionStatus.APPROVED,
        ActionStatus.EXECUTING,
    )


def test_executing_can_succeed():
    assert can_action_transition(
        ActionStatus.EXECUTING,
        ActionStatus.SUCCEEDED,
    )


def test_executing_can_fail():
    assert can_action_transition(
        ActionStatus.EXECUTING,
        ActionStatus.FAILED,
    )


def test_failed_can_retry_execution():
    assert can_action_transition(
        ActionStatus.FAILED,
        ActionStatus.EXECUTING,
    )


def test_succeeded_cannot_transition():
    assert not can_action_transition(
        ActionStatus.SUCCEEDED,
        ActionStatus.EXECUTING,
    )


def test_rejected_cannot_transition():
    assert not can_action_transition(
        ActionStatus.REJECTED,
        ActionStatus.APPROVED,
    )


def test_cancelled_cannot_transition():
    assert not can_action_transition(
        ActionStatus.CANCELLED,
        ActionStatus.EXECUTING,
    )


def test_invalid_action_transition_raises_error():
    with pytest.raises(ValueError, match="Invalid action transition"):
        validate_action_transition(
            ActionStatus.PENDING,
            ActionStatus.SUCCEEDED,
        )