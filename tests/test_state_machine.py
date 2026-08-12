import pytest

from backend.domain.states import (
    CaseStatus,
    can_transition,
    validate_transition,
)


def test_received_can_move_to_classifying():
    assert can_transition(
        CaseStatus.RECEIVED,
        CaseStatus.CLASSIFYING,
    )


def test_received_cannot_move_directly_to_succeeded():
    assert not can_transition(
        CaseStatus.RECEIVED,
        CaseStatus.SUCCEEDED,
    )


def test_executing_can_succeed():
    assert can_transition(
        CaseStatus.EXECUTING,
        CaseStatus.SUCCEEDED,
    )


def test_closed_cannot_transition():
    assert not can_transition(
        CaseStatus.CLOSED,
        CaseStatus.EXECUTING,
    )


def test_invalid_transition_raises_error():
    with pytest.raises(ValueError):
        validate_transition(
            CaseStatus.RECEIVED,
            CaseStatus.SUCCEEDED,
        )