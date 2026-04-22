# test_auth.py — unit tests for authentication functions

from auth import hash_password, verify_password, create_access_token
from jose import jwt

SECRET_KEY = "changethislater"
ALGORITHM = "HS256"

def test_hash_password_is_not_plaintext():
    """Hashed password should not match the original string."""
    hashed = hash_password("mypassword")
    assert hashed != "mypassword"

def test_verify_password_correct():
    """Correct password should verify successfully against its hash."""
    hashed = hash_password("mypassword")
    assert verify_password("mypassword", hashed) is True

def test_verify_password_incorrect():
    """Wrong password should fail verification."""
    hashed = hash_password("mypassword")
    assert verify_password("wrongpassword", hashed) is False

def test_create_access_token_contains_username():
    """Token should decode to contain the username we put in."""
    token = create_access_token(data={"sub": "testuser"})
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload.get("sub") == "testuser"

def test_create_access_token_contains_expiry():
    """Token should contain an expiry time."""
    token = create_access_token(data={"sub": "testuser"})
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert "exp" in payload