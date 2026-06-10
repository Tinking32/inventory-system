import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import User
from app.services.auth import get_current_user, hash_password

SQLITE_TEST_URL = "sqlite:///./test.db"

engine = create_engine(SQLITE_TEST_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Create a mock test user for protected routes
TEST_USERNAME = "testuser@example.com"
TEST_PASSWORD = "testpass123"


def _seed_test_user():
    db = TestingSessionLocal()
    user = db.query(User).filter(User.username == TEST_USERNAME).first()
    if not user:
        user = User(
            username=TEST_USERNAME, hashed_password=hash_password(TEST_PASSWORD)
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    db.close()
    return user


def override_get_current_user():
    return _seed_test_user()


app.dependency_overrides[get_current_user] = override_get_current_user


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Register + login and return Authorization header for protected requests."""
    client.post(
        "/api/auth/register",
        json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
    )
    r = client.post(
        "/api/auth/login",
        json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
    )
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
