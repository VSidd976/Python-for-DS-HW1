import datetime as dt
import json

import requests
from flask import Flask, jsonify, request

import os
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
WEATHER_API_KEY =os.getenv("WEATHER_API_KEY")

app = Flask(__name__)


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv


def get_weather(location: str, date: str, unit: str = "metric"):
    base_url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/"

    url = f"{base_url}/{location}/{date}?unitGroup={unit}&key={WEATHER_API_KEY}"

    response = requests.get(url)

    if response.status_code == requests.codes.ok:
        return json.loads(response.text)
    else:
        raise InvalidUsage(response.text, status_code=response.status_code)


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route("/")
def home_page():
    return "<p><h2>KMA L2: python Saas.</h2></p>"


@app.route("/content/api/v1/integration/weather", methods=["POST"])
def weather_endpoint():

    json_data = request.get_json()

    token = json_data.get("token")

    if token is None:
        raise InvalidUsage("token is required", status_code=400)

    if token != API_TOKEN:
        raise InvalidUsage("wrong API token", status_code=403)

    location = json_data.get("location")

    if not location:
        raise InvalidUsage("location is required", status_code=400)
    
    date = json_data.get("date")

    if not date:
        raise InvalidUsage("date is required", status_code=400)

    requester_name = json_data.get("requester_name", "Unknown")
    timestamp = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    weather = get_weather(location, date)
    daily_forecast = weather.get("days", [{}])[0]

    result = {
        "requester name": requester_name,
        "timestamp": timestamp,
        "location": location,
        "date": date,
        "weather":
            {
                "description": daily_forecast.get("description", None),
                "cloudcover": daily_forecast.get("cloudcover", None),
                "temp_c": daily_forecast.get("temp", None),
                "wind_kph": daily_forecast.get("windspeed", None),
                "pressure_mb": daily_forecast.get("pressure", None),
                "humidity": daily_forecast.get("humidity", None),
                "visibility": daily_forecast.get("visibility", None)
            }
    }

    return result
