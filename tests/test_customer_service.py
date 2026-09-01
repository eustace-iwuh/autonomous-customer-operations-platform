import uuid

from backend.database.models import Customer
from backend.database.connection import SessionLocal
from backend.services.customer_service import CustomerService


def test_customer_service_creates_customer():
    db = SessionLocal()

    customer = None

    try:
        service = CustomerService(db)

        customer = service.create_customer(
            external_id=f"customer-service-{uuid.uuid4().hex}",
            name="Customer Service Test",
            email=f"customer-service-{uuid.uuid4().hex}@example.com",
        )

        db.commit()

        assert customer.id is not None
        assert customer.name == "Customer Service Test"
        assert customer.email.endswith("@example.com")

    finally:
        db.rollback()

        if customer is not None:
            db.query(Customer).filter(
                Customer.id == customer.id
            ).delete()

            db.commit()

        db.close()