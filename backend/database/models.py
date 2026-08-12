from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.connection import Base
from backend.domain.states import CasePriority, CaseStatus


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    external_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    cases: Mapped[list["Case"]] = relationship(
        back_populates="customer",
    )


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    case_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        String(5000),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default=CaseStatus.RECEIVED.value,
        nullable=False,
        index=True,
    )

    priority: Mapped[str] = mapped_column(
        String(50),
        default=CasePriority.MEDIUM.value,
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    customer: Mapped["Customer"] = relationship(
        back_populates="cases",
    )