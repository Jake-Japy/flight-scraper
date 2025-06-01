from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from celery import Celery
import redis
import json
import uuid
import logging
from tenacity import retry, stop_after_attempt, wait_fixed

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI()

# SQLite database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./flight_data.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis setup with fallback
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
except redis.ConnectionError as e:
    logger.warning(f"Redis connection failed: {e}. Proceeding without cache.")
    redis_client = None

# Celery setup
celery = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')
celery.conf.update(task_track_started=True)


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


Base.metadata.create_all(bind=engine)


# Pydantic model for request
class FlightRequest(BaseModel):
    airline_code: str
    flight_number: str
    departure_date: str  # Format: YYYY-MM-DD


# Pydantic model for response
class FlightResponse(BaseModel):
    flight_id: str
    airline_code: str
    flight_number: str
    departure_date: str
    departure_airport: str
    arrival_airport: str
    departure_time: str
    arrival_time: str
    status: str
    gate: str | None


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Retry decorator for HTTP requests
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def make_request(url, headers):
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response


# Celery task for scraping
@celery.task
def scrape_flight_data(airline_code: str, flight_number: str, departure_date: str):
    logger.debug(f"Scraping flight {airline_code}{flight_number} for {departure_date}")
    url = f"https://www.flightstats.com/v2/flight-tracker/{airline_code}/{flight_number}?year={departure_date[:4]}&month={departure_date[5:7]}&date={departure_date[8:10]}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = make_request(url, headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract flight details with robust fallbacks
        try:
            flight_no_elem = soup.find("div", class_=lambda x: x and "FlightNumberContainer" in x)
            flight_no = flight_no_elem.get_text().strip() if flight_no_elem else f"{airline_code}{flight_number}"
        except Exception as e:
            logger.warning(f"Failed to extract flight number: {e}")
            flight_no = f"{airline_code}{flight_number}"

        try:
            airport_names = soup.find_all("div", class_=lambda x: x and "TextHelper" in x and "CPamx" in x)
            airports = [name.get_text().strip() for name in airport_names[:2]] if airport_names else ["N/A", "N/A"]
        except Exception as e:
            logger.warning(f"Failed to extract airports: {e}")
            airports = ["N/A", "N/A"]

        try:
            status_elements = soup.find_all("div", class_=lambda x: x and "TextHelper" in x and "bcmzUJ" in x)
            status = status_elements[0].get_text().strip() if status_elements else "N/A"
        except Exception as e:
            logger.warning(f"Failed to extract status: {e}")
            status = "N/A"

        try:
            time_elements = soup.find_all("div", class_=lambda x: x and "TextHelper" in x and "cCfBRT" in x)
            departure_time = time_elements[0].get_text().strip() if time_elements else "N/A"
            arrival_time = time_elements[1].get_text().strip() if len(time_elements) > 1 else "N/A"
        except Exception as e:
            logger.warning(f"Failed to extract times: {e}")
            departure_time = arrival_time = "N/A"

        try:
            gate_values = soup.find_all("div", class_=lambda x: x and "TGBValue" in x)
            gate = gate_values[0].get_text().strip() if gate_values else None
        except Exception as e:
            logger.warning(f"Failed to extract gate: {e}")
            gate = None

        # Convert departure_date to datetime
        try:
            parsed_date = datetime.strptime(departure_date, "%Y-%m-%d")
        except ValueError as e:
            logger.error(f"Invalid departure date format: {e}")
            return {"error": f"Invalid departure date format: {departure_date}"}

        flight_data = {
            "flight_id": str(uuid.uuid4()),
            "airline_code": airline_code,
            "flight_number": flight_number,
            "departure_date": parsed_date,
            "departure_airport": airports[0],
            "arrival_airport": airports[1],
            "departure_time": departure_time,
            "arrival_time": arrival_time,
            "status": status,
            "gate": gate
        }

        # Check if flight data is mostly empty
        if all(v in ["N/A", None] for k, v in flight_data.items() if
               k not in ["flight_id", "airline_code", "flight_number", "departure_date"]):
            logger.warning(f"No valid flight data found for {airline_code}{flight_number} on {departure_date}")
            return {"error": f"No flight data available for {airline_code}{flight_number} on {departure_date}"}

        # Save to database
        db = SessionLocal()
        try:
            db_flight = Flight(**flight_data)
            db.add(db_flight)
            db.commit()
            db.refresh(db_flight)
        except Exception as e:
            logger.error(f"Database error: {e}")
            raise
        finally:
            db.close()

        # Cache the result if Redis is available
        if redis_client:
            try:
                redis_client.setex(f"flight:{airline_code}:{flight_number}:{departure_date}", 3600,
                                   json.dumps(flight_data))
            except redis.ConnectionError:
                logger.warning("Failed to cache in Redis, proceeding without cache.")

        logger.debug(f"Successfully scraped and stored flight {airline_code}{flight_number}")
        return flight_data

    except requests.HTTPError as e:
        logger.error(f"HTTP error for {url}: {str(e)}")
        return {"error": f"Failed to fetch flight data: {str(e)}"}
    except Exception as e:
        logger.error(f"Scraping error for {url}: {str(e)}")
        return {"error": f"Failed to parse flight data: {str(e)}"}


# API endpoint
@app.get("/flights/", response_model=FlightResponse)
async def get_flight_info(airline_code: str, flight_number: str, departure_date: str, db: Session = Depends(get_db)):
    # Validate departure_date format
    try:
        datetime.strptime(departure_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    # Check cache if Redis is available
    cache_key = f"flight:{airline_code}:{flight_number}:{departure_date}"
    cached_data = None
    if redis_client:
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for {cache_key}")
                return json.loads(cached_data)
        except redis.ConnectionError:
            logger.warning("Redis unavailable, skipping cache.")

    # Check database
    flight = db.query(Flight).filter(
        Flight.airline_code == airline_code,
        Flight.flight_number == flight_number,
        Flight.departure_date == departure_date
    ).first()

    if flight:
        flight_data = {
            "flight_id": flight.flight_id,
            "airline_code": flight.airline_code,
            "flight_number": flight.flight_number,
            "departure_date": flight.departure_date.strftime("%Y-%m-%d"),
            "departure_airport": flight.departure_airport,
            "arrival_airport": flight.arrival_airport,
            "departure_time": flight.departure_time,
            "arrival_time": flight.arrival_time,
            "status": flight.status,
            "gate": flight.gate
        }
        if redis_client:
            try:
                redis_client.setex(cache_key, 3600, json.dumps(flight_data))
            except redis.ConnectionError:
                logger.warning("Failed to cache in Redis, proceeding without cache.")
        logger.debug(f"Database hit for {cache_key}")
        return flight_data

    # Trigger Celery task
    logger.debug(f"Starting Celery task for {airline_code}{flight_number} on {departure_date}")
    try:
        task = scrape_flight_data.delay(airline_code, flight_number, departure_date)
        result = task.get(timeout=30)
        if "error" in result:
            logger.error(f"Celery task returned error: {result['error']}")
            raise HTTPException(status_code=404, detail=f"Flight data retrieval failed: {result['error']}")
        return result
    except Exception as e:
        logger.error(f"Celery task failed: {str(e)}")
        # Fallback: Perform scraping directly
        logger.info("Falling back to direct scraping due to Celery failure")
        result = scrape_flight_data(airline_code, flight_number, departure_date)
        if "error" in result:
            logger.error(f"Direct scraping failed: {result['error']}")
            raise HTTPException(status_code=404, detail=f"Flight data retrieval failed: {result['error']}")
        return result