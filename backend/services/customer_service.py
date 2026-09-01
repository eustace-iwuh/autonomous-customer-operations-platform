from sqlalchemy.orm import Session

from backend.database.models import Customer


class CustomerService:
    def __init__(self, db: Session):
        self.db = db

    def create_customer(
        self,
        *,
        external_id: str,
        name: str,
        email: str,
    ) -> Customer:
        customer = Customer(
            external_id=external_id,
            name=name,
            email=email,
        )

        self.db.add(customer)
        self.db.flush()

        return customer

    def get_customer(self, customer_id: int) -> Customer | None:
        return (
            self.db.query(Customer)
            .filter(Customer.id == customer_id)
            .first()
        )

    def list_customers(self) -> list[Customer]:
        return (
            self.db.query(Customer)
            .order_by(Customer.created_at.desc())
            .all()
        )