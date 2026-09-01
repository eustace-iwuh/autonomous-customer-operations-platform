import uuid

from backend.database.connection import SessionLocal
from backend.database.models import Customer, Case, CaseEvent
from backend.services.event_service import EventService


def test_event_service_records_case_event():
    db = SessionLocal()

    customer = None
    case = None

    try:
        customer = Customer(
            external_id=f"event_test_customer_{uuid.uuid4().hex}",
            name="Event Test Customer",
            email=f"event-{uuid.uuid4().hex}@example.com",
        )

        db.add(customer)
        db.flush()

        case = Case(
            case_number=f"EVENT-TEST-{uuid.uuid4().hex}",
            customer_id=customer.id,
            title="Event service test",
            description="Testing operational event recording.",
        )

        db.add(case)
        db.flush()

        service = EventService(db)

        event = service.record(
            case_id=case.id,
            event_type="CASE_RECEIVED",
            actor_type="SYSTEM",
            description="Case received by the operations platform.",
            payload={
                "source": "integration_test",
                "test": True,
            },
        )

        db.commit()

        assert event.id is not None
        assert event.case_id == case.id
        assert event.event_type == "CASE_RECEIVED"
        assert event.actor_type == "SYSTEM"
        assert event.payload["source"] == "integration_test"

    finally:
        db.rollback()
        
        if case is not None and case.id is not None:
            db.query(CaseEvent).filter(
                CaseEvent.case_id == case.id
            ).delete()
            
            db.query(Case).filter(
                Case.id == case.id
            ).delete()
            
        if customer is not None and customer.id is not None:
            db.query(Customer).filter(
                Customer.id == customer.id
            ).delete()
            
        db.commit()
        db.close()