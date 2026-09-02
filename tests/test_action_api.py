import uuid

from fastapi.testclient import TestClient

from backend.database.connection import SessionLocal
from backend.database.models import (
    Action,
    ActionExecution,
    Case,
    CaseEvent,
    Customer,
    User,
)
from backend.domain.states import ActionStatus, ActionType
from backend.main import app
from backend.security.jwt import create_access_token
from backend.services.auth_service import AuthService
from backend.services.case_service import CaseService


client = TestClient(app)


def create_test_user(db):
    service = AuthService(db)

    email = f"action-api-{uuid.uuid4().hex}@example.com"

    user = service.create_user(
        email=email,
        password="SuperSecret123!",
        full_name="Action API Test User",
    )

    db.flush()

    return user


def create_test_case(db):
    customer = Customer(
        external_id=f"action-api-customer-{uuid.uuid4().hex}",
        name="Action API Test Customer",
        email=f"action-api-{uuid.uuid4().hex}@example.com",
    )

    db.add(customer)
    db.flush()

    service = CaseService(db)

    case = service.create_case(
        case_number=f"ACTION-API-{uuid.uuid4().hex}",
        customer_id=customer.id,
        title="Action API test",
        description="Testing the action API.",
    )

    db.flush()

    return customer, case


def test_create_action_requires_authentication():
    response = client.post(
        "/actions",
        json={
            "case_id": 999999999,
            "action_type": ActionType.SEND_EMAIL.value,
            "payload": {},
        },
    )

    assert response.status_code == 401


def test_create_action_returns_created_action():
    db = SessionLocal()

    user = None
    customer = None
    case = None
    action = None

    try:
        user = create_test_user(db)
        customer, case = create_test_case(db)

        db.commit()

        token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role,
        )

        response = client.post(
            "/actions",
            json={
                "case_id": case.id,
                "action_type": ActionType.SEND_EMAIL.value,
                "payload": {
                    "recipient": "customer@example.com",
                    "subject": "Test email",
                },
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 201

        data = response.json()

        assert data["id"] is not None
        assert data["case_id"] == case.id
        assert data["action_type"] == ActionType.SEND_EMAIL.value
        assert data["status"] == ActionStatus.PENDING.value
        assert data["payload"]["recipient"] == "customer@example.com"
        assert data["result"] is None

        action = (
            db.query(Action)
            .filter(Action.id == data["id"])
            .first()
        )

        assert action is not None

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

        if user is not None:
            db.query(User).filter(
                User.id == user.id
            ).delete()

        db.commit()
        db.close()


def test_create_action_rejects_missing_case():
    db = SessionLocal()

    user = None

    try:
        user = create_test_user(db)
        db.commit()

        token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role,
        )

        response = client.post(
            "/actions",
            json={
                "case_id": 999999999,
                "action_type": ActionType.SEND_EMAIL.value,
                "payload": {},
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 404
        assert response.json() == {
            "detail": "Case not found: 999999999",
        }

    finally:
        db.rollback()

        if user is not None:
            db.query(User).filter(
                User.id == user.id
            ).delete()

        db.commit()
        db.close()


def test_get_action_returns_action():
    db = SessionLocal()

    user = None
    customer = None
    case = None
    action = None

    try:
        user = create_test_user(db)
        customer, case = create_test_case(db)

        action = Action(
            case_id=case.id,
            action_type=ActionType.CREATE_TICKET.value,
            status=ActionStatus.PENDING.value,
            payload={
                "subject": "Test ticket",
            },
        )

        db.add(action)
        db.commit()
        db.refresh(action)

        token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role,
        )

        response = client.get(
            f"/actions/{action.id}",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == action.id
        assert data["case_id"] == case.id
        assert data["action_type"] == ActionType.CREATE_TICKET.value
        assert data["status"] == ActionStatus.PENDING.value

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

        if user is not None:
            db.query(User).filter(
                User.id == user.id
            ).delete()

        db.commit()
        db.close()


def test_list_case_actions_returns_actions():
    db = SessionLocal()

    user = None
    customer = None
    case = None
    actions = []

    try:
        user = create_test_user(db)
        customer, case = create_test_case(db)

        actions.append(
            Action(
                case_id=case.id,
                action_type=ActionType.SEND_EMAIL.value,
                status=ActionStatus.PENDING.value,
                payload={},
            )
        )

        actions.append(
            Action(
                case_id=case.id,
                action_type=ActionType.CREATE_TICKET.value,
                status=ActionStatus.PENDING.value,
                payload={},
            )
        )

        db.add_all(actions)
        db.commit()

        for action in actions:
            db.refresh(action)

        token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role,
        )

        response = client.get(
            f"/actions/case/{case.id}",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert len(data) == 2
        assert data[0]["id"] == actions[0].id
        assert data[1]["id"] == actions[1].id

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


def test_transition_action_pending_to_approved():
    db = SessionLocal()

    user = None
    customer = None
    case = None
    action = None

    try:
        user = create_test_user(db)
        customer, case = create_test_case(db)

        action = Action(
            case_id=case.id,
            action_type=ActionType.SEND_EMAIL.value,
            status=ActionStatus.PENDING.value,
            payload={
                "recipient": "customer@example.com",
            },
        )

        db.add(action)
        db.commit()
        db.refresh(action)

        token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role,
        )

        response = client.post(
            f"/actions/{action.id}/transition",
            json={
                "target_status": ActionStatus.APPROVED.value,
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == action.id
        assert data["status"] == ActionStatus.APPROVED.value

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

        if user is not None:
            db.query(User).filter(
                User.id == user.id
            ).delete()

        db.commit()
        db.close()


def test_transition_action_approved_to_executing():
    db = SessionLocal()

    user = None
    customer = None
    case = None
    action = None

    try:
        user = create_test_user(db)
        customer, case = create_test_case(db)

        action = Action(
            case_id=case.id,
            action_type=ActionType.SEND_EMAIL.value,
            status=ActionStatus.APPROVED.value,
            payload={
                "recipient": "customer@example.com",
            },
        )

        db.add(action)
        db.commit()
        db.refresh(action)

        token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role,
        )

        response = client.post(
            f"/actions/{action.id}/transition",
            json={
                "target_status": ActionStatus.EXECUTING.value,
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == action.id
        assert data["status"] == ActionStatus.EXECUTING.value

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

        if user is not None:
            db.query(User).filter(
                User.id == user.id
            ).delete()

        db.commit()
        db.close()


def test_transition_action_rejects_invalid_transition():
    db = SessionLocal()

    user = None
    customer = None
    case = None
    action = None

    try:
        user = create_test_user(db)
        customer, case = create_test_case(db)

        action = Action(
            case_id=case.id,
            action_type=ActionType.SEND_EMAIL.value,
            status=ActionStatus.PENDING.value,
            payload={},
        )

        db.add(action)
        db.commit()
        db.refresh(action)

        token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role,
        )

        response = client.post(
            f"/actions/{action.id}/transition",
            json={
                "target_status": ActionStatus.SUCCEEDED.value,
            },
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 400

        assert "Invalid action transition" in response.json()["detail"]

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

        if user is not None:
            db.query(User).filter(
                User.id == user.id
            ).delete()

        db.commit()
        db.close()


def test_execute_approved_action():
    db = SessionLocal()

    user = None
    customer = None
    case = None
    action = None

    try:
        user = create_test_user(db)
        customer, case = create_test_case(db)

        action = Action(
            case_id=case.id,
            action_type=ActionType.SEND_EMAIL.value,
            status=ActionStatus.APPROVED.value,
            payload={
                "recipient": "customer@example.com",
                "subject": "Test email",
            },
        )

        db.add(action)
        db.commit()
        db.refresh(action)

        token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role,
        )

        response = client.post(
            f"/actions/{action.id}/execute",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == action.id
        assert data["status"] == ActionStatus.SUCCEEDED.value
        assert data["result"] is not None
        assert data["result"]["success"] is True
        assert (
            data["result"]["action_type"]
            == ActionType.SEND_EMAIL.value
        )

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

        if user is not None:
            db.query(User).filter(
                User.id == user.id
            ).delete()

        db.commit()
        db.close()


def test_execute_pending_action_is_rejected():
    db = SessionLocal()

    user = None
    customer = None
    case = None
    action = None

    try:
        user = create_test_user(db)
        customer, case = create_test_case(db)

        action = Action(
            case_id=case.id,
            action_type=ActionType.SEND_EMAIL.value,
            status=ActionStatus.PENDING.value,
            payload={
                "recipient": "customer@example.com",
            },
        )

        db.add(action)
        db.commit()
        db.refresh(action)

        token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role,
        )

        response = client.post(
            f"/actions/{action.id}/execute",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 400

        assert "Invalid action transition" in response.json()["detail"]

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

        if user is not None:
            db.query(User).filter(
                User.id == user.id
            ).delete()

        db.commit()
        db.close()

def test_list_execution_history_returns_history():
    db = SessionLocal()

    user = None
    customer = None
    case = None
    action = None

    try:
        user = create_test_user(db)
        customer, case = create_test_case(db)

        action = Action(
            case_id=case.id,
            action_type=ActionType.SEND_EMAIL.value,
            status=ActionStatus.APPROVED.value,
            payload={
                "recipient": "customer@example.com",
                "subject": "Test email",
            },
        )

        db.add(action)
        db.commit()
        db.refresh(action)

        token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role,
        )

        headers = {
            "Authorization": f"Bearer {token}",
        }

        response = client.post(
            f"/actions/{action.id}/execute",
            headers=headers,
        )

        assert response.status_code == 200

        response = client.get(
            f"/actions/{action.id}/executions",
            headers=headers,
        )

        assert response.status_code == 200

        history = response.json()

        assert len(history) == 1
        assert history[0]["action_id"] == action.id
        assert history[0]["status"] == ActionStatus.SUCCEEDED.value
        assert history[0]["result"] is not None
        assert history[0]["result"]["success"] is True
        assert history[0]["started_at"] is not None
        assert history[0]["completed_at"] is not None
        assert history[0]["created_at"] is not None

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