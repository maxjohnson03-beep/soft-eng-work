# conftest.py — shared test setup
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from database import Base, get_db, User
from auth import hash_password
from main import app

TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True, scope="session")
def setup_db():
    # Wipe and recreate tables fresh for every test session
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # Manually seed admin — don't rely on lifespan
    db = TestingSessionLocal()
    db.add(User(
        username="admin",
        hashed_password=hash_password("admin123"),
        role="commander",
    ))
    db.commit()
    db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)