import uuid

from backend.database.connection import SessionLocal
from backend.database.models import (
    Action,
    ActionExecution,
    Case,
    CaseEvent,
    Customer,
    User,
)
from backend.domain.states import (
    ActionStatus,
    ActionType,
    CaseStatus,
)
from backend.services.auth_service import AuthService
from backend.services.case_orchestrator import CaseOrchestrator
from backend.services.case_service import CaseService


def create_test_user(db):
    service = AuthService(db)

    user = service.create_user(
        email=f"orchestrator-{uuid.uuid4().hex}@example.com",
        password="SuperSecret123!",
        full_name="Orchestrator Test User",
    )

    db.flush()

    return user


def create_test_case(db):
    customer = Customer(
        external_id=f"orchestrator-customer-{uuid.uuid4().hex}",
        name="Orchestrator Test Customer",
        email=f"orchestrator-{uuid.uuid4().hex}@example.com",
    )

    db.add(customer)
    db.flush()

    service = CaseService(db)

    case = service.create_case(
        case_number=f"ORCH-{uuid.uuid4().hex}",
        customer_id=customer.id,
        title="Orchestrator test",
        description="Testing case orchestration.",
    )

    db.flush()

    return customer, case

def move_case_to_approved(db, case_id: int):
    service = CaseService(db)

    service.transition_case(
        case_id=case_id,
        target_status=CaseStatus.CLASSIFYING,
    )

    service.transition_case(
        case_id=case_id,
        target_status=CaseStatus.CLASSIFIED,
    )

    service.transition_case(
        case_id=case_id,
        target_status=CaseStatus.PLANNING,
    )

    service.transition_case(
        case_id=case_id,
        target_status=CaseStatus.AWAITING_APPROVAL,
    )

    service.transition_case(
        case_id=case_id,
        target_status=CaseStatus.APPROVED,
    )

    db.flush()


def test_orchestrator_get_case_returns_case():
    db = SessionLocal()

    user = None
    customer = None
    case = None

    try:
        user = create_test_user(db)
        customer, case = create_test_case(db)

        db.commit()

        orchestrator = CaseOrchestrator(db)

        result = orchestrator.get_case(case.id)

        assert result.id == case.id
        assert result.case_number == case.case_number

    finally:
        db.rollback()

        if case is not None:
            db.query(ActionExecution).filter(
                ActionExecution.action_id.in_(
                    db.query(Action.id)
                    .filter(Action.case_id == case.id)
                )
            ).delete(
                synchronize_session=False
            )

            db.query(Action).filter(
                Action.case_id == case.id
            ).delete()

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

        if user is not None:
            db.query(User).filter(
                User.id == user.id
            ).delete()

        db.commit()
        db.close()


def test_orchestrator_rejects_missing_case():
    db = SessionLocal()

    try:
        orchestrator = CaseOrchestrator(db)

        try:
            orchestrator.get_case(999999999)
            assert False, "Expected ValueError"

        except ValueError as exc:
            assert str(exc) == "Case not found: 999999999"

    finally:
        db.rollback()
        db.close()


def test_orchestrator_get_actions_returns_case_actions():
    db = SessionLocal()

    user = None
    customer = None
    case = None
    actions = []

    try:
        user = create_test_user(db)
        customer, case = create_test_case(db)

        actions = [
            Action(
                case_id=case.id,
                action_type=ActionType.SEND_EMAIL.value,
                status=ActionStatus.PENDING.value,
                payload={
                    "recipient": "customer@example.com",
                },
            ),
            Action(
                case_id=case.id,
                action_type=ActionType.CREATE_TICKET.value,
                status=ActionStatus.APPROVED.value,
                payload={
                    "subject": "Support ticket",
                },
            ),
        ]

        db.add_all(actions)
        db.commit()

        orchestrator = CaseOrchestrator(db)

        result = orchestrator.get_actions(case.id)

        assert len(result) == 2
        assert result[0].id == actions[0].id
        assert result[1].id == actions[1].id

    finally:
        db.rollback()

        if case is not None:
            db.query(ActionExecution).filter(
                ActionExecution.action_id.in_(
                    [action.id for action in actions]
                    if actions
                    else [-1]
                )
            ).delete(
                synchronize_session=False
            )

            db.query(Action).filter(
                Action.case_id == case.id
            ).delete()

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

        if user is not None:
            db.query(User).filter(
                User.id == user.id
            ).delete()

        db.commit()
        db.close()


def test_orchestrator_executes_only_approved_actions():
    db = SessionLocal()

    user = None
    customer = None
    case = None
    pending_action = None
    approved_action = None

    try:
        user = create_test_user(db)
        customer, case = create_test_case(db)

        move_case_to_approved(db, case.id)

        pending_action = Action(
            case_id=case.id,
            action_type=ActionType.SEND_EMAIL.value,
            status=ActionStatus.PENDING.value,
            payload={
                "recipient": "pending@example.com",
                "subject": "Pending test email",
            },
        )

        approved_action = Action(
            case_id=case.id,
            action_type=ActionType.SEND_EMAIL.value,
            status=ActionStatus.APPROVED.value,
            payload={
                "recipient": "approved@example.com",
                "subject": "Approved test email",
            },
        )

        db.add_all([
            pending_action,
            approved_action,
        ])

        db.commit()

        db.refresh(pending_action)
        db.refresh(approved_action)

        orchestrator = CaseOrchestrator(db)

        result = orchestrator.execute_approved_actions(
            case_id=case.id,
        )

        db.refresh(case)

        assert case.status == CaseStatus.SUCCEEDED.value
        assert result["case_status"] == CaseStatus.SUCCEEDED.value

        assert result["case_id"] == case.id
        assert result["actions_processed"] == 1

        assert len(result["results"]) == 1

        processed = result["results"][0]

        assert processed["action_id"] == approved_action.id
        assert processed["status"] == ActionStatus.SUCCEEDED.value
        assert processed["result"]["success"] is True

        db.refresh(pending_action)
        db.refresh(approved_action)

        assert (
            pending_action.status
            == ActionStatus.PENDING.value
        )

        assert (
            approved_action.status
            == ActionStatus.SUCCEEDED.value
        )

    finally:
        db.rollback()

        if pending_action is not None:
            db.query(ActionExecution).filter(
                ActionExecution.action_id == pending_action.id
            ).delete(
                synchronize_session=False
            )

        if approved_action is not None:
            db.query(ActionExecution).filter(
                ActionExecution.action_id == approved_action.id
            ).delete(
                synchronize_session=False
            )

        if case is not None:
            db.query(Action).filter(
                Action.case_id == case.id
            ).delete()

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

        if user is not None:
            db.query(User).filter(
                User.id == user.id
            ).delete()

        db.commit()
        db.close()


def test_orchestrator_rejects_case_with_no_actions():
    db = SessionLocal()

    user = None
    customer = None
    case = None

    try:
        user = create_test_user(db)
        customer, case = create_test_case(db)

        db.commit()

        orchestrator = CaseOrchestrator(db)

        try:
            orchestrator.execute_approved_actions(
                case_id=case.id,
            )

            assert False, "Expected ValueError"

        except ValueError as exc:
            assert (
                str(exc)
                == f"Case {case.id} has no actions to execute"
            )

    finally:
        db.rollback()

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

        if user is not None:
            db.query(User).filter(
                User.id == user.id
            ).delete()

        db.commit()
        db.close()

def test_orchestrator_marks_case_failed_when_action_fails():
    db = SessionLocal()

    user = None
    customer = None
    case = None
    action = None

    try:
        user = create_test_user(db)
        customer, case = create_test_case(db)

        move_case_to_approved(db, case.id)

        action = Action(
            case_id=case.id,
            action_type="INVALID_ACTION",
            status=ActionStatus.APPROVED.value,
            payload={},
        )

        db.add(action)
        db.commit()
        db.refresh(action)

        orchestrator = CaseOrchestrator(db)

        result = orchestrator.execute_approved_actions(
            case_id=case.id,
        )

        db.refresh(case)
        db.refresh(action)

        assert result["case_id"] == case.id
        assert result["actions_processed"] == 1
        assert result["case_status"] == CaseStatus.FAILED.value

        assert case.status == CaseStatus.FAILED.value
        assert action.status == ActionStatus.FAILED.value

        events = (
            db.query(CaseEvent)
            .filter(CaseEvent.case_id == case.id)
            .order_by(CaseEvent.created_at.asc())
            .all()
        )

        assert events[-1].event_type == "CASE_STATUS_CHANGED"
        assert events[-1].payload["new_status"] == CaseStatus.FAILED.value

        assert len(result["results"]) == 1
        assert result["results"][0]["action_id"] == action.id
        assert (
            result["results"][0]["status"]
            == ActionStatus.FAILED.value
        )

    finally:
        db.rollback()

        if action is not None:
            db.query(ActionExecution).filter(
                ActionExecution.action_id == action.id
            ).delete(
                synchronize_session=False
            )

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

        if user is not None:
            db.query(User).filter(
                User.id == user.id
            ).delete()

        db.commit()
        db.close()