from flask import Flask, jsonify
from google.transit import gtfs_realtime_pb2
import requests
import time

app = Flask(__name__)

Q_FEED_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw"
B_FEED_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm"
DEKALB_Q_MANHATTAN_STOP_ID = "R30N"


def fetch_feed(feed_url):
    response = requests.get(feed_url)
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(response.content)
    return feed


def extract_arrival_times(feed, stop_id, route_id_filter=None):
    arrival_times = []

    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue

        trip = entity.trip_update.trip
        for stop_time in entity.trip_update.stop_time_update:
            if stop_time.stop_id != stop_id:
                continue

            if route_id_filter and route_id_filter not in trip.route_id:
                continue

            arrival_times.append(stop_time.arrival.time)

    return arrival_times


def get_next_arrival(arrival_times):
    now = time.time()
    future_arrivals = sorted(t for t in arrival_times if t > now)
    if future_arrivals:
        arrival_time = future_arrivals[0]
        minutes_away = int((arrival_time - now) / 60)
        return arrival_time, minutes_away
    return -1, -1


@app.route("/next_train")
def next_train():
    q_feed = fetch_feed(Q_FEED_URL)
    b_feed = fetch_feed(B_FEED_URL)

    q_times = extract_arrival_times(q_feed, DEKALB_Q_MANHATTAN_STOP_ID, route_id_filter="Q")
    b_times = extract_arrival_times(b_feed, DEKALB_Q_MANHATTAN_STOP_ID, route_id_filter="B")
    d_times = extract_arrival_times(b_feed, DEKALB_Q_MANHATTAN_STOP_ID, route_id_filter="D")

    q_arrival_unix, q_minutes_away = get_next_arrival(q_times)
    b_arrival_unix, b_minutes_away = get_next_arrival(b_times)
    d_arrival_unix, d_minutes_away = get_next_arrival(d_times)

    print(f"Q Train → Unix: {q_arrival_unix-time()}, {q_minutes_away} min away")
    print(f"B Train → Unix: {b_arrival_unix-time()}, {b_minutes_away} min away")
    print(f"D Train → Unix: {d_arrival_unix-time()}, {d_minutes_away} min away")

    return jsonify({
        "q_next_arrival_unix": q_arrival_unix,
        "q_minutes_away": q_minutes_away,
        "b_next_arrival_unix": b_arrival_unix,
        "b_minutes_away": b_minutes_away,
        "d_next_arrival_unix": d_arrival_unix,
        "d_minutes_away": d_minutes_away
    })


@app.route("/")
def root():
    return "MTA Q Train API is running"
