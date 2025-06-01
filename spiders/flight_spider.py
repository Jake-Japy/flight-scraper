# spiders/flight_spider.py
import scrapy
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

class FlightSpider(scrapy.Spider):
    name = 'flight_spider'

    def __init__(self, airline_code, flight_number, departure_date, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.airline_code = airline_code
        self.flight_number = flight_number
        self.departure_date = departure_date
        self.start_urls = [
            f"https://www.flightstats.com/v2/flight-tracker/{airline_code}/{flight_number}?year={departure_date[:4]}&month={departure_date[5:7]}&date={departure_date[8:10]}"
        ]

    def parse(self, response):
        try:
            # Extract flight details with robust fallbacks
            try:
                flight_no_elem = response.css("div[class*='FlightNumberContainer']::text").get()
                flight_no = flight_no_elem.strip() if flight_no_elem else f"{self.airline_code}{self.flight_number}"
            except Exception as e:
                logger.warning(f"Failed to extract flight number: {e}")
                flight_no = f"{self.airline_code}{self.flight_number}"

            try:
                airport_names = response.css("div[class*='TextHelper'][class*='CPamx']::text").getall()
                airports = [name.strip() for name in airport_names[:2]] if airport_names else ["N/A", "N/A"]
            except Exception as e:
                logger.warning(f"Failed to extract airports: {e}")
                airports = ["N/A", "N/A"]

            try:
                status_elements = response.css("div[class*='TextHelper'][class*='bcmzUJ']::text").getall()
                status = status_elements[0].strip() if status_elements else "N/A"
            except Exception as e:
                logger.warning(f"Failed to extract status: {e}")
                status = "N/A"

            try:
                time_elements = response.css("div[class*='TextHelper'][class*='cCfBRT']::text").getall()
                departure_time = time_elements[0].strip() if time_elements else "N/A"
                arrival_time = time_elements[1].strip() if len(time_elements) > 1 else "N/A"
            except Exception as e:
                logger.warning(f"Failed to extract times: {e}")
                departure_time = arrival_time = "N/A"

            try:
                gate_values = response.css("div[class*='TGBValue']::text").getall()
                gate = gate_values[0].strip() if gate_values else None
            except Exception as e:
                logger.warning(f"Failed to extract gate: {e}")
                gate = None

            # Convert departure_date to datetime
            try:
                parsed_date = datetime.strptime(self.departure_date, "%Y-%m-%d").date()
            except ValueError as e:
                logger.error(f"Invalid departure date format: {e}")
                return {"error": f"Invalid departure date format: {self.departure_date}"}

            flight_data = {
                "flight_id": str(uuid.uuid4()),
                "airline_code": self.airline_code,
                "flight_number": self.flight_number,
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
                logger.warning(f"No valid flight data found for {self.airline_code}{self.flight_number} on {self.departure_date}")
                return {"error": f"No flight data available for {self.airline_code}{self.flight_number} on {self.departure_date}"}

            yield flight_data  # Use yield to return data to Scrapy

        except Exception as e:
            logger.error(f"Scraping error for {response.url}: {str(e)}")
            yield {"error": f"Failed to parse flight data: {str(e)}"}