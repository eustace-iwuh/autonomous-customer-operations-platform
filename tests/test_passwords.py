from backend.security.passwords import hash_password, verify_password


def test_password_hash_is_not_plaintext():
    password = "SuperSecret123!"

    hashed = hash_password(password)

    assert hashed != password
    assert len(hashed) > 0


def test_correct_password_verifies():
    password = "SuperSecret123!"

    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_wrong_password_does_not_verify():
    password = "SuperSecret123!"

    hashed = hash_password(password)

    assert verify_password("WrongPassword123!", hashed) is False