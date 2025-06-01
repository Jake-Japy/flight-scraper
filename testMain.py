import pytest
from fastapi.testclient import TestClient
from main import app, Flight, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch, MagicMock

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Flight.metadata.create_all(bind=engine)
    yield
    Flight.metadata.drop_all(bind=engine)

@patch("main.redis_client")
@patch("main.scrape_flight_data.delay")
def test_get_flight_valid_params(mock_scrape, mock_redis):
    # Mock Redis get to return None (cache miss)
    mock_redis.get.return_value = None
    # Mock Redis setex
    mock_redis.setex = MagicMock()
    # Mock Celery task
    mock_scrape.return_value.get.return_value = {
        "flight_id": "123e4567-e89b-12d3-a456-426614174000",
        "airline_code": "AA",
        "flight_number": "100",
        "departure_date": "2025-05-26",
        "departure_airport": "JFK",
        "arrival_airport": "LAX",
        "departure_time": "08:00 AM",
        "arrival_time": "11:30 AM",
        "status": "Scheduled",
        "gate": "B12"
    }
    response = client.get("/flights/?airline_code=AA&flight_number=100&departure_date=2025-05-26")
    assert response.status_code == 200
    assert response.json()["airline_code"] == "AA"
    assert response.json()["flight_number"] == "100"
    assert response.json()["departure_date"] == "2025-05-26"

def test_get_flight_invalid_date():
    response = client.get("/flights/?airline_code=AA&flight_number=100&departure_date=invalid")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid date format. Use YYYY-MM-DD"

def test_get_flight_missing_params():
    response = client.get("/flights/?airline_code=AA&flight_number=100")
    assert response.status_code == 422