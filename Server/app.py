from flask import Flask, jsonify
from google.transit import gtfs_realtime_pb2
import requests
from time import time

app = Flask(__name__)

Q_FEED_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw"
B_FEED_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm"
DEKALB_Q_MANHATTAN_STOP_ID = "R30N"

@app.route("/next_train")
def next_q_train():
    qfeed = gtfs_realtime_pb2.FeedMessage()
    qresponse = requests.get(Q_FEED_URL)
    qfeed.ParseFromString(qresponse.content)

    bfeed = gtfs_realtime_pb2.FeedMessage()
    bresponse = requests.get(B_FEED_URL)
    bfeed.ParseFromString(bresponse.content)

    q_arrival_times = []
    b_arrival_times = []

    for entity in qfeed.entity:
        if not entity.HasField("trip_update"):
            continue
        for stop_time_update in entity.trip_update.stop_time_update:
            if stop_time_update.stop_id == DEKALB_Q_MANHATTAN_STOP_ID:
                print(entity.trip_update.trip.route_id)
            if stop_time_update.stop_id == DEKALB_Q_MANHATTAN_STOP_ID and "Q" in entity.trip_update.trip.route_id:
                arrival_timestamp = stop_time_update.arrival.time
                q_arrival_times.append(arrival_timestamp)
            elif stop_time_update.stop_id == DEKALB_Q_MANHATTAN_STOP_ID and "B" in entity.trip_update.trip.route_id:
                arrival_timestamp = stop_time_update.arrival.time
                b_arrival_times.append(arrival_timestamp)
    for entity in bfeed.entity:
        if not entity.HasField("trip_update"):
            continue
        for stop_time_update in entity.trip_update.stop_time_update:
            if stop_time_update.stop_id == DEKALB_Q_MANHATTAN_STOP_ID and "B" in entity.trip_update.trip.route_id:
                arrival_timestamp = stop_time_update.arrival.time
                b_arrival_times.append(arrival_timestamp)

    if q_arrival_times:
        b_arrive_time = -1;
        q_arrive_time = -1;
        q_arrival_times.sort()
        if(len(q_arrival_times) > 0):
            q_arrive_time = q_arrival_times[0] if q_arrival_times[0] > time() else q_arrival_times[1]
            q_minutes_away = int((q_arrive_time - time()) / 60)
        else:
            q_minutes_away = -1
        b_arrival_times.sort()
        if(len(b_arrival_times) > 0):
            b_arrive_time = b_arrival_times[0] if b_arrival_times[0] > time() else b_arrival_times[1]
            b_minutes_away = int((b_arrive_time - time()) / 60)
        else:
            b_minutes_away = -1
        print("unixtime for Q: "+ str(q_arrive_time) + ", " + str(q_minutes_away)+ " Minutes Away, Current Time: "+ str(time()) + ", " + str(q_arrive_time - time()) + "Seconds Away")
        print("unixtime for B: "+ str(b_arrive_time) + ", " + str(b_minutes_away)+ " Minutes Away, Current Time: "+ str(time()) + ", " + str(b_arrive_time - time()) + "Seconds Away")
        return jsonify({
            "q_next_arrival_unix": q_arrive_time,
            "q_minutes_away": q_minutes_away,
            "b_next_arrival_unix": b_arrive_time,
            "b_minutes_away": b_minutes_away
        })
    else:
        return jsonify({"error": "No arrivals found"}), 404

@app.route("/")
def root():
    return "MTA Q Train API is running"

