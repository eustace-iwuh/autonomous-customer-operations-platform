from sqlalchemy.orm import Session

from backend.database.models import User
from backend.security.passwords import hash_password


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def create_user(
        self,
        *,
        email: str,
        password: str,
        full_name: str,
        role: str = "AGENT",
    ) -> User:
        user = User(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            role=role,
        )

        self.db.add(user)
        self.db.flush()

        return user

    def get_user_by_email(
        self,
        email: str,
    ) -> User | None:
        return (
            self.db.query(User)
            .filter(User.email == email)
            .first()
        )