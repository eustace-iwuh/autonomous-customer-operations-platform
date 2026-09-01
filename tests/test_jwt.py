import jwt

from backend.security.jwt import (
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
    create_access_token,
)


def test_create_access_token():
    token = create_access_token(
        user_id=4,
        email="api-test@example.com",
        role="AGENT",
    )

    assert isinstance(token, str)
    assert len(token) > 0

    payload = jwt.decode(
        token,
        JWT_SECRET_KEY,
        algorithms=[JWT_ALGORITHM],
    )

    assert payload["sub"] == "4"
    assert payload["email"] == "api-test@example.com"
    assert payload["role"] == "AGENT"
    assert "exp" in payload