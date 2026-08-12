from backend.database.connection import SessionLocal
from backend.database.models import Customer, Case


def main():
    db = SessionLocal()

    try:
        customer = Customer(
            external_id="test_customer_001",
            name="John Doe",
            email="john@example.com",
        )

        db.add(customer)
        db.flush()

        case = Case(
            case_number="CASE-000001",
            customer_id=customer.id,
            title="Duplicate payment",
            description="Customer reports being charged twice.",
        )

        db.add(case)
        db.commit()

        print(f"Customer created: {customer.id}")
        print(f"Case created: {case.id}")
        print(f"Case number: {case.case_number}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()