import argparse
import csv
import datetime

import requests
from google.transit import gtfs_realtime_pb2


GTFS_FEED_URL = "https://www.rtd-denver.com/files/gtfs-rt/TripUpdate.pb"


def get_next_schedule(route_id, stop_id):
    """Returns the remaining time until the next scheduled bus arrives at the given stop."""

    with open("rtd_inventory/stop_times.txt", "r", encoding="UTF-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["stop_id"] == stop_id:
                print(row)
                #return get_remaining_time(datetime.datetime.strptime(row["arrival_time"], "%H:%M:%S"))
    return None

def get_next_bus(route_id, stop_id):
    """Returns the remaining time until the next live data bus arrives at the given stop."""

    feed = gtfs_realtime_pb2.FeedMessage()
    response = requests.get(GTFS_FEED_URL, timeout=10)
    feed.ParseFromString(response.content)

    for entity in feed.entity:
        if not entity.HasField("trip_update") and not entity.trip_update.trip.route_id == route_id:
            continue
        for stop_time_update in entity.trip_update.stop_time_update:
            if stop_time_update.stop_id == stop_id:
                print(stop_time_update)
                return get_remaining_time(datetime.datetime.fromtimestamp(stop_time_update.arrival.time))
    return None

def get_remaining_time(date: datetime.datetime) -> str:
    """Returns a string of the remaining time until the given date."""

    now = datetime.datetime.now()
    minutes = int((date - now).total_seconds() / 60)
    return f"At {date.time()}, {minutes} minutes"

def parse_args():
    """Parses the command line arguments"""

    parser = argparse.ArgumentParser(description="Get the next bus arrival time")
    parser.add_argument("route_id", type=str, help="The route ID")
    parser.add_argument("stop_id", type=str, help="The stop ID")
    return parser.parse_args()

def main() -> None:
    """Main entry point"""

    args = parse_args()
    route_id = args.route_id
    stop_id = args.stop_id

    next_bus = get_next_bus(route_id, stop_id)
    print(next_bus)
    print(get_next_schedule(route_id, stop_id))

if __name__ == "__main__":
    main()
