from sqlalchemy import Column, Integer, String, DateTime
from database import init_db

_, _, Base = init_db()

# Database model
class Flight(Base):
    __tablename__ = "flights"
    id = Column(Integer, primary_key=True, index=True)
    flight_id = Column(String, unique=True, index=True)
    airline_code = Column(String, index=True)
    flight_number = Column(String, index=True)
    departure_date = Column(DateTime)
    departure_airport = Column(String)
    arrival_airport = Column(String)
    departure_time = Column(String)
    arrival_time = Column(String)
    status = Column(String)
    gate = Column(String, nullable=True)

class LogApiUse(Base):
    __tablename__ = "api_log"
    id = Column(Integer, primary_key=True, index=True)
    api_call_date = Column(DateTime)
    api_result = Column(String)
    api_direction = Column(String)
    api_payload = Column(String)
