import uuid

from fastapi.testclient import TestClient

from backend.database.connection import SessionLocal
from backend.database.models import User
from backend.main import app
from backend.security.jwt import (
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
)
from backend.security.jwt import create_access_token
from backend.services.auth_service import AuthService
import jwt


client = TestClient(app)


def test_login_returns_access_token():
    db = SessionLocal()
    user = None

    try:
        email = f"login-test-{uuid.uuid4().hex}@example.com"
        password = "SuperSecret123!"

        from backend.services.auth_service import AuthService

        service = AuthService(db)

        user = service.create_user(
            email=email,
            password=password,
            full_name="Login Test User",
        )

        db.commit()

        response = client.post(
            "/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"

        payload = jwt.decode(
            data["access_token"],
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )

        assert payload["sub"] == str(user.id)
        assert payload["email"] == email
        assert payload["role"] == "AGENT"

    finally:
        db.rollback()

        if user is not None:
            db.query(User).filter(
                User.id == user.id
            ).delete()

            db.commit()

        db.close()

def test_login_rejects_wrong_password():
    db = SessionLocal()
    user = None

    try:
        email = f"wrong-password-{uuid.uuid4().hex}@example.com"
        password = "SuperSecret123!"

        from backend.services.auth_service import AuthService

        service = AuthService(db)

        user = service.create_user(
            email=email,
            password=password,
            full_name="Wrong Password Test User",
        )

        db.commit()

        response = client.post(
            "/auth/login",
            json={
                "email": email,
                "password": "DefinitelyWrong123!",
            },
        )

        assert response.status_code == 401
        assert response.json() == {
            "detail": "Invalid email or password.",
        }

    finally:
        db.rollback()

        if user is not None:
            db.query(User).filter(
                User.id == user.id
            ).delete()

            db.commit()

        db.close()

def test_login_rejects_nonexistent_user():
    response = client.post(
        "/auth/login",
        json={
            "email": f"does-not-exist-{uuid.uuid4().hex}@example.com",
            "password": "SuperSecret123!",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid email or password.",
    }

def test_login_rejects_inactive_user():
    db = SessionLocal()
    user = None

    try:
        email = f"inactive-{uuid.uuid4().hex}@example.com"
        password = "SuperSecret123!"

        from backend.services.auth_service import AuthService

        service = AuthService(db)

        user = service.create_user(
            email=email,
            password=password,
            full_name="Inactive Test User",
        )

        user.is_active = False
        db.commit()

        response = client.post(
            "/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )

        assert response.status_code == 403
        assert response.json() == {
            "detail": "User account is inactive.",
        }

    finally:
        db.rollback()

        if user is not None:
            db.query(User).filter(
                User.id == user.id
            ).delete()

            db.commit()

        db.close()

def test_get_me_returns_authenticated_user():
    db = SessionLocal()
    user = None

    try:
        service = AuthService(db)

        email = f"me-test-{uuid.uuid4().hex}@example.com"

        user = service.create_user(
            email=email,
            password="SuperSecret123!",
            full_name="Me Test User",
        )

        db.commit()

        token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role,
        )

        response = client.get(
            "/auth/me",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == user.id
        assert data["email"] == email
        assert data["full_name"] == "Me Test User"
        assert data["role"] == "AGENT"
        assert data["is_active"] is True

        assert "password" not in data
        assert "password_hash" not in data

    finally:
        db.rollback()

        if user is not None:
            db.query(User).filter(
                User.id == user.id
            ).delete()

            db.commit()

        db.close()


def test_get_me_rejects_invalid_token():
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer definitely-not-a-valid-token",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid or expired token.",
    }


def test_get_me_requires_authentication():
    response = client.get("/auth/me")

    assert response.status_code == 401