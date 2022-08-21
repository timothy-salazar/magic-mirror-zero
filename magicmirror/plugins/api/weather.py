""" Queries the National Weather Service API to retrieve the day's forecast:
        https://www.weather.gov/documentation/services-web-api
This is a 100% free service, but it's only available in the US.
"""
import os
import time
from datetime import datetime as dt
import requests
import argparse

MAX_RETRIES = 3
# A 5 second timeout should work for most purposes, but if you have a
# particularly slow connection you may need to increase this value
TIMEOUT = 5

def make_request(url: str)->dict:
    """ Input:
            url: str - a URL which will return a JSON document
        Output:
            returns a dictionary containing the requested data
    """
    for i in range(MAX_RETRIES):
        req = requests.get(url, timeout=TIMEOUT)
        # This checks to see if the request returned a successful status code
        try:
            req.raise_for_status()
            break
        # If there was an unsuccessful status code:
        #   - if we've tried less than MAX_RETRIES times, then the program will
        #     sleep for 2 seconds
        #   - if we've tried MAX_RETRIES times, then the program will raise
        #     a HTTPError
        except requests.HTTPError as e:
            if i < (MAX_RETRIES-1):
                time.sleep(2)
            else:
                raise e
    return req.json()

def get_point_data():
    """ Gets metadata for the given point. This includes the urls we use to
    request forecasts.

    Note:
        If you want to get an accurate weather forecast from this, you gotta
        have environment variables called LATITUDE and LONGITUDE which store
        the latitude and longitude respectively (as you'd expect).
        If no LATITUDE and LONGITUDE environment variables exist, it defaults
        to the latitude and longitude of the Swetsville Zoo.
    """
    latitude = os.getenv('LATITUDE', '40.523')
    longitude = os.getenv('LONGITUDE', '-104.99')
    url = f'https://api.weather.gov/points/{latitude},{longitude}'
    point_data = make_request(url)
    return point_data

def get_hourly_forecast():
    """ Returns a list of dictionaries, each of which contains forecast data for
    a given hour.
    """
    point_data = get_point_data()
    hourly_url = point_data['properties']['forecastHourly']
    hourly_data = make_request(hourly_url)
    periods = hourly_data['properties']['periods']
    stripped_periods = strip_old_data(periods)
    return stripped_periods

def strip_old_data(periods: list) -> list:
    """ Input:
            periods: a list of dictionaries, each of which contains forecast
                data for a given hour.
        Output:
            stripped_data: list of dicts - periods, but with the forecast data
                for previous hours stripped away
    """
    # the API can lag behind, so the first entry might be for an hour that's
    # already passed
    for index, period in enumerate(periods):
        end_time = dt.fromisoformat(period['endTime'])
        now = dt.now(tz=end_time.tzinfo)
        if end_time < now:
            continue
        else:
            stripped_data = periods[index:]
            return stripped_data




if __name__ == "__main__":
    pass