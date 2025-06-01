===============================
*** App Instructions Readme ***
===============================

FlightStats Scraper API
A FastAPI-based application to scrape flight information from FlightStats, store it in SQLite, and cache results using Redis. Background tasks are handled by Celery.
Prerequisites

Python 3.8+
Redis server
SQLite (included with Python)

Setup Instructions

Clone the Repository
git clone <https://github.com/Jake-Japy/flight-scraperl>
cd FlightStatScraper

Install DependenciesCreate a virtual environment and install requirements:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install the requirements using the requirements.txt file

====================================================
****** NB Important steps to run this program ******
====================================================

######

Start Redis ServerEnsure Redis is running on localhost:6379. On Ubuntu/Windows in separate terminal Window or in detached mode:
sudo apt-get install redis-server
redis-server

On a Windows machine open the folder where redis is located in a powershell or cmd prompt and navigate to the folder
for Windows PS ./redis-server.exe
for Windows CMD cd\Redis\redis-server.exe for example where redis folder is in path c:\Redis\

######

Run Celery WorkerIn a separate terminal, start the Celery worker or run in a detached mode:
celery -A main.celery worker --loglevel=info

If using Windows I encountered an error where I would need to set the additional permission to run concurrent celery workers
Instead of doing this you can run it using celery -A main.celery worker --loglevel=debug --pool=solo this should circumvent
the need to go and set additional thread permissions for celery. It seems to run fine on a Linux VM or Linux Virtualbox environment.

######

Run the FastAPI Application
uvicorn main:app --reload

######

Access the API
You can do this by copying the example URL into the browser

Open http://127.0.0.1:8000/docs for the Swagger UI.
Endpoint: GET /flights/?airline_code=<code>&flight_number=<number>&departure_date=<YYYY-MM-DD>
Example: http://127.0.0.1:8000/flights/?airline_code=AA&flight_number=1004&departure_date=2025-05-26

You can also use the request data script I created for testing to check that it works, I made this one using Frontier Airlines:
Call via terminal:
python request_data.py "F9" 201 "2025-06-01"

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

The scraper uses requests and Scrapy to parse FlightStats HTML.
Data is cached in Redis to reduce load.
Celery handles scraping in the background but the program can operate without it.
SQLite is used for persistent storage.
Tests validate negative and positive behaviours of the application and check basic functionality.

