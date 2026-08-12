from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.connection import Base


class DatabaseTest(Base):
    __tablename__ = "database_tests"

    id: Mapped[int] = mapped_column(primary_key=True)
    message: Mapped[str] = mapped_column(String(255), nullable=False)