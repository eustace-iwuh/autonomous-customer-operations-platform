from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.services.customer_service import CustomerService

router = APIRouter(prefix="/customers", tags=["customers"])


class CreateCustomerRequest(BaseModel):
    external_id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=1, max_length=320)


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: str
    name: str
    email: str


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_customer(
    request: CreateCustomerRequest,
    db: Session = Depends(get_db),
):
    service = CustomerService(db)

    try:
        customer = service.create_customer(
            external_id=request.external_id,
            name=request.name,
            email=request.email,
        )

        db.commit()
        db.refresh(customer)

        return customer

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Customer with this external_id already exists.",
        )

    except Exception:
        db.rollback()
        raise


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
):
    service = CustomerService(db)

    customer = service.get_customer(customer_id)

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer not found: {customer_id}",
        )

    return customer


@router.get(
    "",
    response_model=list[CustomerResponse],
)
def list_customers(
    db: Session = Depends(get_db),
):
    service = CustomerService(db)

    return service.list_customers()