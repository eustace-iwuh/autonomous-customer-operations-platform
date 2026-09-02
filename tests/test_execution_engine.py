from backend.database.models import Action
from backend.domain.states import ActionStatus, ActionType
from backend.execution.engine import ExecutionEngine


def create_action(
    action_type: ActionType,
    payload: dict | None = None,
) -> Action:
    return Action(
        case_id=1,
        action_type=action_type.value,
        status=ActionStatus.EXECUTING.value,
        payload=payload or {},
    )


def test_execution_engine_executes_send_email():
    engine = ExecutionEngine()

    action = create_action(
        ActionType.SEND_EMAIL,
        {
            "recipient": "customer@example.com",
            "subject": "Test email",
        },
    )

    result = engine.execute(action)

    assert result["success"] is True
    assert result["action_type"] == ActionType.SEND_EMAIL.value


def test_execution_engine_executes_issue_refund():
    engine = ExecutionEngine()

    action = create_action(
        ActionType.ISSUE_REFUND,
        {
            "amount": 100,
        },
    )

    result = engine.execute(action)

    assert result["success"] is True
    assert result["action_type"] == ActionType.ISSUE_REFUND.value


def test_execution_engine_executes_update_customer():
    engine = ExecutionEngine()

    action = create_action(
        ActionType.UPDATE_CUSTOMER,
        {
            "name": "Updated Customer",
        },
    )

    result = engine.execute(action)

    assert result["success"] is True
    assert result["action_type"] == ActionType.UPDATE_CUSTOMER.value


def test_execution_engine_executes_create_ticket():
    engine = ExecutionEngine()

    action = create_action(
        ActionType.CREATE_TICKET,
        {
            "subject": "Customer issue",
        },
    )

    result = engine.execute(action)

    assert result["success"] is True
    assert result["action_type"] == ActionType.CREATE_TICKET.value


def test_execution_engine_executes_escalate_case():
    engine = ExecutionEngine()

    action = create_action(
        ActionType.ESCALATE_CASE,
        {
            "reason": "Critical customer issue",
        },
    )

    result = engine.execute(action)

    assert result["success"] is True
    assert result["action_type"] == ActionType.ESCALATE_CASE.value

def test_execution_engine_rejects_email_without_recipient():
    engine = ExecutionEngine()

    action = create_action(
        ActionType.SEND_EMAIL,
        {
            "subject": "Test email",
        },
    )

    try:
        engine.execute(action)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert str(exc) == "Email recipient is required."


def test_execution_engine_rejects_email_without_subject():
    engine = ExecutionEngine()

    action = create_action(
        ActionType.SEND_EMAIL,
        {
            "recipient": "customer@example.com",
        },
    )

    try:
        engine.execute(action)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert str(exc) == "Email subject is required."

def test_execution_engine_rejects_empty_customer_update():
    engine = ExecutionEngine()

    action = create_action(
        ActionType.UPDATE_CUSTOMER,
        {},
    )

    try:
        engine.execute(action)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert str(exc) == "Customer update fields are required."

def test_execution_engine_rejects_ticket_without_subject():
    engine = ExecutionEngine()

    action = create_action(
        ActionType.CREATE_TICKET,
        {},
    )

    try:
        engine.execute(action)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert str(exc) == "Ticket subject is required."

def test_execution_engine_rejects_escalation_without_reason():
    engine = ExecutionEngine()

    action = create_action(
        ActionType.ESCALATE_CASE,
        {},
    )

    try:
        engine.execute(action)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert str(exc) == "Escalation reason is required."