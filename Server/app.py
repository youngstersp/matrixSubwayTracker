from flask import Flask, jsonify
from google.transit import gtfs_realtime_pb2
import requests
from time import time

app = Flask(__name__)

FEED_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw"
DEKALB_Q_MANHATTAN_STOP_ID = "D27N"

@app.route("/next_train")
def next_q_train():
    feed = gtfs_realtime_pb2.FeedMessage()
    response = requests.get(FEED_URL)
    feed.ParseFromString(response.content)

    arrival_times = []

    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue
        for stop_time_update in entity.trip_update.stop_time_update:
            print(stop_time_update)
            if stop_time_update.stop_id == DEKALB_Q_MANHATTAN_STOP_ID:
                arrival_timestamp = stop_time_update.arrival.time
                arrival_times.append(arrival_timestamp)

    if arrival_times:
        arrival_times.sort()
        minutes_away = int((arrival_times[0] - time()) / 60)
        return jsonify({
            "next_arrival_unix": arrival_times[0],
            "minutes_away": minutes_away
        })
    else:
        return jsonify({"error": "No arrivals found"}), 404

@app.route("/")
def root():
    return "MTA Q Train API is running"

