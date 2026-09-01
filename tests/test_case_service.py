import uuid

from backend.database.models import CaseEvent
from backend.database.connection import SessionLocal
from backend.database.models import Customer
from backend.domain.states import CaseStatus
from backend.services.case_service import CaseService


def test_case_service_creates_case_and_event():
    db = SessionLocal()

    customer = None
    case = None

    try:
        customer = Customer(
            external_id=f"case_service_customer_{uuid.uuid4().hex}",
            name="Case Service Test Customer",
            email=f"case-service-{uuid.uuid4().hex}@example.com",
        )

        db.add(customer)
        db.flush()

        service = CaseService(db)

        case = service.create_case(
            case_number=f"CASE-SERVICE-{uuid.uuid4().hex}",
            customer_id=customer.id,
            title="Case service test",
            description="Testing case creation.",
        )

        db.commit()

        assert case.id is not None
        assert case.customer_id == customer.id
        assert case.status == CaseStatus.RECEIVED.value
        assert case.priority == "MEDIUM"

        assert len(case.events) == 1
        assert case.events[0].event_type == "CASE_CREATED"

    finally:
        db.rollback()

        if case is not None:
            db.query(CaseEvent).filter(
                CaseEvent.case_id == case.id
            ).delete()
                   
            db.query(type(case)).filter(
                type(case).id == case.id
            ).delete()

        if customer is not None:
            db.query(type(customer)).filter(
                type(customer).id == customer.id
            ).delete()

        db.commit()
        db.close()


def test_case_service_transition_records_event():
    db = SessionLocal()

    customer = None
    case = None

    try:
        customer = Customer(
            external_id=f"transition_customer_{uuid.uuid4().hex}",
            name="Transition Test Customer",
            email=f"transition-{uuid.uuid4().hex}@example.com",
        )

        db.add(customer)
        db.flush()

        service = CaseService(db)

        case = service.create_case(
            case_number=f"TRANSITION-{uuid.uuid4().hex}",
            customer_id=customer.id,
            title="Transition test",
            description="Testing case transition.",
        )

        service.transition_case(
            case_id=case.id,
            target_status=CaseStatus.CLASSIFYING,
        )

        db.commit()

        assert case.status == CaseStatus.CLASSIFYING.value
        assert len(case.events) == 2
        assert case.events[1].event_type == "CASE_STATUS_CHANGED"
        assert case.events[1].payload["previous_status"] == "RECEIVED"
        assert case.events[1].payload["new_status"] == "CLASSIFYING"

    finally:
        db.rollback()

        if case is not None:
            db.query(CaseEvent).filter(
                CaseEvent.case_id == case.id
            ).delete()
            
            db.query(type(case)).filter(
                type(case).id == case.id
            ).delete()

        if customer is not None:
            db.query(type(customer)).filter(
                type(customer).id == customer.id
            ).delete()

        db.commit()
        db.close()


def test_case_service_rejects_invalid_transition():
    db = SessionLocal()

    customer = None
    case = None

    try:
        customer = Customer(
            external_id=f"invalid_transition_{uuid.uuid4().hex}",
            name="Invalid Transition Test",
            email=f"invalid-{uuid.uuid4().hex}@example.com",
        )

        db.add(customer)
        db.flush()

        service = CaseService(db)

        case = service.create_case(
            case_number=f"INVALID-{uuid.uuid4().hex}",
            customer_id=customer.id,
            title="Invalid transition test",
            description="Testing invalid state transitions.",
        )

        try:
            service.transition_case(
                case_id=case.id,
                target_status=CaseStatus.CLOSED,
            )
            assert False, "Expected invalid transition to raise ValueError"
        except ValueError as exc:
            assert "Invalid case transition" in str(exc)

        db.rollback()

    finally:
        db.rollback()

        if case is not None:
            db.query(type(case)).filter(
                type(case).id == case.id
            ).delete()

        if customer is not None:
            db.query(type(customer)).filter(
                type(customer).id == customer.id
            ).delete()

        db.commit()
        db.close()
