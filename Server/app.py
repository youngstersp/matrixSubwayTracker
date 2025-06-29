from flask import Flask, jsonify
from google.transit import gtfs_realtime_pb2
import requests
from time import time

app = Flask(__name__)

FEED_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw"
DEKALB_Q_MANHATTAN_STOP_ID = "R30N"

@app.route("/next_train")
def next_q_train():
    feed = gtfs_realtime_pb2.FeedMessage()
    response = requests.get(FEED_URL)
    feed.ParseFromString(response.content)

    q_arrival_times = []
    b_arrival_times = []

    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue
        if entity.trip_update.trip.route_id != "Q" or entity.trip_update.trip.route_id != "B":
            continue
        for stop_time_update in entity.trip_update.stop_time_update:
            if stop_time_update.stop_id == DEKALB_Q_MANHATTAN_STOP_ID and "Q" in entity.trip_update.trip.route_id:
                print(entity.trip_update.trip.route_id)
                arrival_timestamp = stop_time_update.arrival.time
                q_arrival_times.append(arrival_timestamp)
            elif stop_time_update.stop_id == DEKALB_Q_MANHATTAN_STOP_ID and "B" in entity.trip_update.trip.route_id:
                print(entity.trip_update.trip.route_id)
                arrival_timestamp = stop_time_update.arrival.time
                b_arrival_times.append(arrival_timestamp)

    if q_arrival_times or b_arrival_times:
        q_arrival_times.sort()
        q_minutes_away = int((q_arrival_times[0] - time()) / 60)
        b_arrival_times.sort()
        b_minutes_away = int((b_arrival_times[0] - time()) / 60)
        return jsonify({
            "q_next_arrival_unix": q_arrival_times[0],
            "q_minutes_away": q_minutes_away,
            "b_next_arrival_unix": q_arrival_times[0],
            "b_minutes_away": b_minutes_away
        })
    else:
        return jsonify({"error": "No arrivals found"}), 404

@app.route("/")
def root():
    return "MTA Q Train API is running"

