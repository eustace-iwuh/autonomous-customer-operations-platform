import uuid

from backend.database.connection import SessionLocal
from backend.domain.states import ActionStatus, ActionType
from backend.services.action_service import ActionService
from backend.services.case_service import CaseService
from backend.database.models import (
    Action,
    ActionExecution,
    Case,
    CaseEvent,
    Customer,
)

def create_test_case(db):
    customer = Customer(
        external_id=f"action-service-{uuid.uuid4().hex}",
        name="Action Service Test Customer",
        email=f"action-service-{uuid.uuid4().hex}@example.com",
    )

    db.add(customer)
    db.flush()

    case = Case(
        case_number=f"ACTION-SERVICE-{uuid.uuid4().hex}",
        customer_id=customer.id,
        title="Action service test",
        description="Testing action lifecycle.",
    )

    db.add(case)
    db.flush()

    return customer, case


def test_action_service_transition_approved_to_executing():
    db = SessionLocal()
    customer = None
    case = None
    action = None

    try:
        customer, case = create_test_case(db)

        service = ActionService(db)

        action = service.create_action(
            case_id=case.id,
            action_type=ActionType.SEND_EMAIL,
            payload={"recipient": "test@example.com"},
        )

        assert action.status == ActionStatus.PENDING.value

        service.transition_action(
            action_id=action.id,
            target_status=ActionStatus.APPROVED,
        )

        assert action.status == ActionStatus.APPROVED.value

        service.transition_action(
            action_id=action.id,
            target_status=ActionStatus.EXECUTING,
        )

        db.commit()

        assert action.status == ActionStatus.EXECUTING.value

    finally:
        db.rollback()

        if action is not None:
            db.query(Action).filter(
                Action.id == action.id
            ).delete()

        if case is not None:
            db.query(Case).filter(
                Case.id == case.id
            ).delete()

        if customer is not None:
            db.query(Customer).filter(
                Customer.id == customer.id
            ).delete()

        db.commit()
        db.close()


def test_action_service_records_result_on_success():
    db = SessionLocal()
    customer = None
    case = None
    action = None

    try:
        customer, case = create_test_case(db)

        service = ActionService(db)

        action = service.create_action(
            case_id=case.id,
            action_type=ActionType.SEND_EMAIL,
        )

        service.transition_action(
            action_id=action.id,
            target_status=ActionStatus.APPROVED,
        )

        service.transition_action(
            action_id=action.id,
            target_status=ActionStatus.EXECUTING,
        )

        service.transition_action(
            action_id=action.id,
            target_status=ActionStatus.SUCCEEDED,
            result={
                "message_id": "msg-123",
                "delivered": True,
            },
        )

        db.commit()

        assert action.status == ActionStatus.SUCCEEDED.value
        assert action.result == {
            "message_id": "msg-123",
            "delivered": True,
        }

    finally:
        db.rollback()

        if action is not None:
            db.query(Action).filter(
                Action.id == action.id
            ).delete()

        if case is not None:
            db.query(Case).filter(
                Case.id == case.id
            ).delete()

        if customer is not None:
            db.query(Customer).filter(
                Customer.id == customer.id
            ).delete()

        db.commit()
        db.close()


def test_action_service_rejects_invalid_transition():
    db = SessionLocal()
    customer = None
    case = None
    action = None

    try:
        customer, case = create_test_case(db)

        service = ActionService(db)

        action = service.create_action(
            case_id=case.id,
            action_type=ActionType.ISSUE_REFUND,
        )

        try:
            service.transition_action(
                action_id=action.id,
                target_status=ActionStatus.SUCCEEDED,
            )
            assert False, "Expected invalid action transition"

        except ValueError as exc:
            assert "Invalid action transition" in str(exc)

    finally:
        db.rollback()

        if action is not None:
            db.query(Action).filter(
                Action.id == action.id
            ).delete()

        if case is not None:
            db.query(Case).filter(
                Case.id == case.id
            ).delete()

        if customer is not None:
            db.query(Customer).filter(
                Customer.id == customer.id
            ).delete()

        db.commit()
        db.close()
def test_action_service_executes_approved_action():
    db = SessionLocal()

    customer = None
    case = None
    action = None

    try:
        customer = Customer(
            external_id=f"execution_customer_{uuid.uuid4().hex}",
            name="Execution Test Customer",
            email=f"execution-{uuid.uuid4().hex}@example.com",
        )

        db.add(customer)
        db.flush()

        case = CaseService(db).create_case(
            case_number=f"EXECUTION-{uuid.uuid4().hex}",
            customer_id=customer.id,
            title="Execution test",
            description="Testing action execution.",
        )

        action = ActionService(db).create_action(
            case_id=case.id,
            action_type=ActionType.SEND_EMAIL,
            payload={
                "recipient": "customer@example.com",
                "subject": "Test customer email",
            },
        )

        action.status = ActionStatus.APPROVED.value
        db.flush()

        service = ActionService(db)

        result = service.execute_action(
            action_id=action.id,
        )

        assert result.status == ActionStatus.SUCCEEDED.value
        assert result.result is not None
        assert result.result["success"] is True
        assert (
            result.result["action_type"]
            == ActionType.SEND_EMAIL.value
        )

    finally:
        db.rollback()

        if action is not None:
            db.query(Action).filter(
                Action.id == action.id
            ).delete()

        if case is not None:
            db.query(CaseEvent).filter(
                CaseEvent.case_id == case.id
            ).delete()

            db.query(Case).filter(
                Case.id == case.id
            ).delete()

        if customer is not None:
            db.query(Customer).filter(
                Customer.id == customer.id
            ).delete()

        db.commit()
        db.close()

def test_action_service_marks_action_failed_when_execution_fails():
    db = SessionLocal()

    customer = None
    case = None
    action = None

    try:
        customer = Customer(
            external_id=f"execution_failure_customer_{uuid.uuid4().hex}",
            name="Execution Failure Customer",
            email=f"execution-failure-{uuid.uuid4().hex}@example.com",
        )

        db.add(customer)
        db.flush()

        case = CaseService(db).create_case(
            case_number=f"EXECUTION-FAILURE-{uuid.uuid4().hex}",
            customer_id=customer.id,
            title="Execution failure test",
            description="Testing failed action execution.",
        )

        action = ActionService(db).create_action(
            case_id=case.id,
            action_type=ActionType.SEND_EMAIL,
            payload={
                "recipient": "customer@example.com",
            },
        )

        action.status = ActionStatus.APPROVED.value
        db.flush()

        service = ActionService(db)

        def failing_execute(_action):
            raise RuntimeError("Simulated execution failure")

        service.execution_engine.execute = failing_execute

        result = service.execute_action(
            action_id=action.id,
        )

        assert result.status == ActionStatus.FAILED.value
        assert result.result is not None
        assert result.result["success"] is False
        assert result.result["error"] == "Simulated execution failure"

    finally:
        db.rollback()

        if action is not None:
            db.query(Action).filter(
                Action.id == action.id
            ).delete()

        if case is not None:
            db.query(CaseEvent).filter(
                CaseEvent.case_id == case.id
            ).delete()

            db.query(Case).filter(
                Case.id == case.id
            ).delete()

        if customer is not None:
            db.query(Customer).filter(
                Customer.id == customer.id
            ).delete()

        db.commit()
        db.close()

def test_action_service_records_execution_history():
    db = SessionLocal()

    customer = None
    case = None
    action = None

    try:
        customer, case = create_test_case(db)

        service = ActionService(db)

        action = service.create_action(
            case_id=case.id,
            action_type=ActionType.SEND_EMAIL,
            payload={
                "recipient": "test@example.com",
                "subject": "Test execution email",
            },
        )

        action.status = ActionStatus.APPROVED.value
        db.flush()

        result = service.execute_action(
            action_id=action.id,
        )

        assert result.status == ActionStatus.SUCCEEDED.value

        execution = (
            db.query(ActionExecution)
            .filter(
                ActionExecution.action_id == action.id
            )
            .one()
        )

        assert execution.status == ActionStatus.SUCCEEDED.value
        assert execution.result is not None
        assert execution.result["success"] is True
        assert execution.started_at is not None
        assert execution.completed_at is not None

    finally:
        db.rollback()

        if action is not None:
            db.query(ActionExecution).filter(
                ActionExecution.action_id == action.id
            ).delete()

            db.query(Action).filter(
                Action.id == action.id
            ).delete()

        if case is not None:
            db.query(CaseEvent).filter(
                CaseEvent.case_id == case.id
            ).delete()

            db.query(Case).filter(
                Case.id == case.id
            ).delete()

        if customer is not None:
            db.query(Customer).filter(
                Customer.id == customer.id
            ).delete()

        db.commit()
        db.close()

def test_action_service_records_failed_execution_history():
    db = SessionLocal()

    customer = None
    case = None
    action = None

    try:
        customer, case = create_test_case(db)

        action = ActionService(db).create_action(
            case_id=case.id,
            action_type=ActionType.SEND_EMAIL,
            payload={
                "recipient": "test@example.com",
            },
        )

        action.status = ActionStatus.APPROVED.value
        db.flush()

        service = ActionService(db)

        def failing_execute(_action):
            raise RuntimeError("Simulated execution failure")

        service.execution_engine.execute = failing_execute

        result = service.execute_action(
            action_id=action.id,
        )

        assert result.status == ActionStatus.FAILED.value

        execution = (
            db.query(ActionExecution)
            .filter(
                ActionExecution.action_id == action.id
            )
            .one()
        )

        assert execution.status == ActionStatus.FAILED.value
        assert execution.result is None
        assert execution.error_message == "Simulated execution failure"
        assert execution.started_at is not None
        assert execution.completed_at is not None

    finally:
        db.rollback()

        if action is not None:
            db.query(ActionExecution).filter(
                ActionExecution.action_id == action.id
            ).delete()

            db.query(Action).filter(
                Action.id == action.id
            ).delete()

        if case is not None:
            db.query(CaseEvent).filter(
                CaseEvent.case_id == case.id
            ).delete()

            db.query(Case).filter(
                Case.id == case.id
            ).delete()

        if customer is not None:
            db.query(Customer).filter(
                Customer.id == customer.id
            ).delete()

        db.commit()
        db.close()

def test_action_service_lists_execution_history():
    db = SessionLocal()

    customer = None
    case = None
    action = None

    try:
        customer, case = create_test_case(db)

        action = ActionService(db).create_action(
            case_id=case.id,
            action_type=ActionType.SEND_EMAIL,
            payload={
                "recipient": "test@example.com",
                "subject": "Test execution history email",
            }, 
        )

        action.status = ActionStatus.APPROVED.value
        db.flush()

        service = ActionService(db)

        service.execute_action(
            action_id=action.id,
        )

        history = service.list_execution_history(
            action_id=action.id,
        )

        assert len(history) == 1
        assert history[0].action_id == action.id
        assert history[0].status == ActionStatus.SUCCEEDED.value

    finally:
        db.rollback()

        if action is not None:
            db.query(ActionExecution).filter(
                ActionExecution.action_id == action.id
            ).delete()

            db.query(Action).filter(
                Action.id == action.id
            ).delete()

        if case is not None:
            db.query(CaseEvent).filter(
                CaseEvent.case_id == case.id
            ).delete()

            db.query(Case).filter(
                Case.id == case.id
            ).delete()

        if customer is not None:
            db.query(Customer).filter(
                Customer.id == customer.id
            ).delete()

        db.commit()
        db.close()