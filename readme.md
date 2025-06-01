FlightStats Scraper API
A FastAPI-based application to scrape flight information from FlightStats, store it in SQLite, and cache results using Redis. Background tasks are handled by Celery.
Prerequisites

Python 3.8+
Redis server
SQLite (included with Python)

Setup Instructions

Clone the Repository
git clone <repository-url>
cd flightstats-scraper


Install DependenciesCreate a virtual environment and install requirements:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install fastapi uvicorn sqlalchemy requests beautifulsoup4 celery redis pytest


Start Redis ServerEnsure Redis is running on localhost:6379. On Ubuntu:
sudo apt-get install redis-server
redis-server


Run Celery WorkerIn a separate terminal, start the Celery worker:
celery -A main.celery worker --loglevel=info


Run the FastAPI Application
uvicorn main:app --reload


Access the API

Open http://127.0.0.1:8000/docs for the Swagger UI.
Endpoint: GET /flights/?airline_code=<code>&flight_number=<number>&departure_date=<YYYY-MM-DD>
Example: http://127.0.0.1:8000/flights/?airline_code=AA&flight_number=1004&departure_date=2025-05-26



Running Tests
Run tests using pytest:
pytest test_main.py

Project Structure

main.py: FastAPI application, Celery task, and database models.
test_main.py: Test cases for the API endpoint.
flight_data.db: SQLite database file (created automatically).
README.md: Project documentation.

API Endpoint

GET /flights/
Parameters: airline_code (e.g., "AA"), flight_number (e.g., "1004"), departure_date (e.g., "2025-05-26")
Response: JSON with flight details (flight_id, airline_code, flight_number, departure_date, departure_airport, arrival_airport, departure_time, arrival_time, status, gate)



Notes

The scraper uses requests and BeautifulSoup to parse FlightStats HTML.
Data is cached in Redis for 1 hour to reduce scraping load.
Celery handles scraping in the background to improve performance.
SQLite is used for persistent storage, suitable for demos.
Tests validate endpoint behavior for valid/invalid inputs.

