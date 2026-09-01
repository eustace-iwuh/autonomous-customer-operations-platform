import uuid

from backend.database.connection import SessionLocal
from backend.database.models import User
from backend.security.passwords import verify_password
from backend.services.auth_service import AuthService


def test_create_user_hashes_password():
    db = SessionLocal()

    user = None

    try:
        service = AuthService(db)

        email = f"auth-test-{uuid.uuid4().hex}@example.com"
        password = "SuperSecret123!"

        user = service.create_user(
            email=email,
            password=password,
            full_name="Auth Test User",
        )

        db.commit()

        assert user.id is not None
        assert user.email == email
        assert user.full_name == "Auth Test User"
        assert user.role == "AGENT"
        assert user.is_active is True

        assert user.password_hash != password
        assert verify_password(
            password,
            user.password_hash,
        ) is True

    finally:
        db.rollback()

        if user is not None:
            db.query(User).filter(
                User.id == user.id
            ).delete()

            db.commit()

        db.close()