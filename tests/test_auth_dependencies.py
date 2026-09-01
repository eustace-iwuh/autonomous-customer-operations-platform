import uuid

import jwt
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from backend.database.connection import SessionLocal
from backend.database.models import User
from backend.api.dependencies import get_current_user
from backend.security.jwt import (
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
    create_access_token,
)
from backend.services.auth_service import AuthService


def test_get_current_user_returns_user():
    db = SessionLocal()
    user = None

    try:
        email = f"dependency-{uuid.uuid4().hex}@example.com"

        service = AuthService(db)

        user = service.create_user(
            email=email,
            password="SuperSecret123!",
            full_name="Dependency Test User",
        )

        db.commit()

        token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role,
        )

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token,
        )

        current_user = get_current_user(
            credentials=credentials,
            db=db,
        )

        assert current_user.id == user.id
        assert current_user.email == email
        assert current_user.role == "AGENT"
        assert current_user.is_active is True

    finally:
        db.rollback()

        if user is not None:
            db.query(User).filter(
                User.id == user.id
            ).delete()

            db.commit()

        db.close()


def test_get_current_user_rejects_invalid_token():
    db = SessionLocal()

    try:
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="this-is-not-a-valid-jwt",
        )

        try:
            get_current_user(
                credentials=credentials,
                db=db,
            )
            assert False, "Expected HTTPException"

        except HTTPException as exc:
            assert exc.status_code == 401
            assert exc.detail == "Invalid or expired token."

    finally:
        db.close()


def test_get_current_user_rejects_missing_user():
    db = SessionLocal()

    try:
        token = jwt.encode(
            {
                "sub": "999999999",
                "email": "ghost@example.com",
                "role": "AGENT",
            },
            JWT_SECRET_KEY,
            algorithm=JWT_ALGORITHM,
        )

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token,
        )

        try:
            get_current_user(
                credentials=credentials,
                db=db,
            )
            assert False, "Expected HTTPException"

        except HTTPException as exc:
            assert exc.status_code == 401
            assert exc.detail == "User not found."

    finally:
        db.close()

def test_require_role_allows_authorized_role():
    from backend.api.dependencies import require_role

    db = SessionLocal()
    user = None

    try:
        service = AuthService(db)

        user = service.create_user(
            email=f"admin-{uuid.uuid4().hex}@example.com",
            password="SuperSecret123!",
            full_name="Admin Test User",
            role="ADMIN",
        )

        db.commit()

        dependency = require_role("ADMIN")

        authorized_user = dependency(
            current_user=user,
        )

        assert authorized_user.id == user.id
        assert authorized_user.role == "ADMIN"

    finally:
        db.rollback()

        if user is not None:
            db.query(User).filter(
                User.id == user.id
            ).delete()

            db.commit()

        db.close()


def test_require_role_rejects_unauthorized_role():
    from backend.api.dependencies import require_role

    db = SessionLocal()
    user = None

    try:
        service = AuthService(db)

        user = service.create_user(
            email=f"agent-{uuid.uuid4().hex}@example.com",
            password="SuperSecret123!",
            full_name="Agent Test User",
            role="AGENT",
        )

        db.commit()

        dependency = require_role("ADMIN")

        try:
            dependency(
                current_user=user,
            )
            assert False, "Expected HTTPException"

        except HTTPException as exc:
            assert exc.status_code == 403
            assert exc.detail == "Insufficient permissions."

    finally:
        db.rollback()

        if user is not None:
            db.query(User).filter(
                User.id == user.id
            ).delete()

            db.commit()

        db.close()

def test_require_role_allows_multiple_roles():
    from backend.api.dependencies import require_role

    db = SessionLocal()
    users = []

    try:
        service = AuthService(db)

        manager = service.create_user(
            email=f"manager-{uuid.uuid4().hex}@example.com",
            password="SuperSecret123!",
            full_name="Manager Test User",
            role="MANAGER",
        )

        admin = service.create_user(
            email=f"admin-multi-{uuid.uuid4().hex}@example.com",
            password="SuperSecret123!",
            full_name="Admin Multi Test User",
            role="ADMIN",
        )

        users.extend([manager, admin])

        db.commit()

        dependency = require_role("MANAGER", "ADMIN")

        assert dependency(current_user=manager) is manager
        assert dependency(current_user=admin) is admin

    finally:
        db.rollback()

        for user in users:
            db.query(User).filter(
                User.id == user.id
            ).delete()

        db.commit()
        db.close()