import requests
import logging
import argparse
from pprint import pprint

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define command-line arguments
parser = argparse.ArgumentParser(description="Test the /flights/ endpoint")
parser.add_argument("--base_url", default="http://localhost:8000")
parser.add_argument("airline_code", type=str)
parser.add_argument("flight_number")
parser.add_argument("departure_date", type=str)
args = parser.parse_args()

# Construct the URL and parameters
url = f"{args.base_url}/flights/"
params = {
    "airline_code": args.airline_code,
    "flight_number": args.flight_number,
    "departure_date": args.departure_date
}

try:

    response = requests.get(url, params=params, timeout=240)

    if response.status_code == 200:
        data = response.json()
        logger.info("Flight data retrieved successfully:")
        pprint(data)
    else:
        error_msg = response.json().get("detail", "Unknown error")
        logger.error(f"Error {response.status_code}: {error_msg}")
except requests.exceptions.Timeout:
    logger.error("Request timed out after 240 seconds")
except requests.exceptions.RequestException as e:
    logger.error(f"An error occurred: {e}")