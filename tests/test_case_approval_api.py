import uuid

from fastapi.testclient import TestClient

from backend.database.connection import SessionLocal
from backend.database.models import Case, CaseEvent, Customer, User
from backend.domain.states import CaseStatus
from backend.main import app
from backend.security.jwt import create_access_token
from backend.services.auth_service import AuthService
from backend.services.case_service import CaseService


client = TestClient(app)


def create_user(db, *, role: str):
    service = AuthService(db)

    email = f"{role.lower()}-{uuid.uuid4().hex}@example.com"

    user = service.create_user(
        email=email,
        password="SuperSecret123!",
        full_name=f"{role} Test User",
    )

    user.role = role
    db.flush()

    return user


def create_case_awaiting_approval(db):
    customer = Customer(
        external_id=f"approval-customer-{uuid.uuid4().hex}",
        name="Approval Test Customer",
        email=f"approval-{uuid.uuid4().hex}@example.com",
    )

    db.add(customer)
    db.flush()

    service = CaseService(db)

    case = service.create_case(
        case_number=f"APPROVAL-{uuid.uuid4().hex}",
        customer_id=customer.id,
        title="Approval test case",
        description="Testing case approval authorization.",
    )

    service.transition_case(
        case_id=case.id,
        target_status=CaseStatus.CLASSIFYING,
    )

    service.transition_case(
        case_id=case.id,
        target_status=CaseStatus.CLASSIFIED,
    )

    service.transition_case(
        case_id=case.id,
        target_status=CaseStatus.PLANNING,
    )

    service.transition_case(
        case_id=case.id,
        target_status=CaseStatus.AWAITING_APPROVAL,
    )

    db.commit()

    return customer, case


def test_agent_cannot_approve_case():
    db = SessionLocal()

    user = None
    customer = None
    case = None

    try:
        user = create_user(db, role="AGENT")
        customer, case = create_case_awaiting_approval(db)

        token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role,
        )

        response = client.post(
            f"/cases/{case.id}/approve",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 403
        assert response.json() == {
            "detail": "Insufficient permissions.",
        }

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


def test_manager_can_approve_case():
    db = SessionLocal()

    user = None
    customer = None
    case = None

    try:
        user = create_user(db, role="MANAGER")
        customer, case = create_case_awaiting_approval(db)

        token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role,
        )

        response = client.post(
            f"/cases/{case.id}/approve",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == case.id
        assert data["status"] == CaseStatus.APPROVED.value

        db.refresh(case)

        assert case.status == CaseStatus.APPROVED.value

        event = (
            db.query(CaseEvent)
            .filter(
                CaseEvent.case_id == case.id,
                CaseEvent.event_type == "CASE_STATUS_CHANGED",
            )
            .order_by(CaseEvent.id.desc())
            .first()
        )

        assert event is not None
        assert event.actor_type == "MANAGER"
        assert event.payload["previous_status"] == (
            CaseStatus.AWAITING_APPROVAL.value
        )
        assert event.payload["new_status"] == (
            CaseStatus.APPROVED.value
        )
        assert event.payload["approved_by_user_id"] == user.id
        assert event.payload["approved_by_email"] == user.email

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


def test_admin_can_approve_case():
    db = SessionLocal()

    user = None
    customer = None
    case = None

    try:
        user = create_user(db, role="ADMIN")
        customer, case = create_case_awaiting_approval(db)

        token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role,
        )

        response = client.post(
            f"/cases/{case.id}/approve",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == case.id
        assert data["status"] == CaseStatus.APPROVED.value

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