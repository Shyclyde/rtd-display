import argparse
import csv
import datetime
import os
from zipfile import ZipFile

import requests
import proto.gtfs_realtime_pb2 as pb

from config.types import BusTrip, BusStopTime, BusStop, BusRoute
from config.config import load_config, Config

def get_bus_trips(route_id: str, service_ids: list[str]) -> list[BusTrip]:
    """Returns a list of bus trips from the GTFS data."""

    bus_trips = []

    with open("rtd_inventory/trips.txt", "r", encoding="UTF-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["route_id"] != route_id or row["service_id"] not in service_ids:
                continue

            bus_trips.append(BusTrip(
                block_id=row["block_id"],
                route_id=row["route_id"],
                direction_id=int(row["direction_id"]),
                trip_headsign=row["trip_headsign"],
                shape_id=row["shape_id"],
                service_id=row["service_id"],
                trip_id=row["trip_id"]
            ))

    return bus_trips

def get_bus_stop_times(trip_ids: list[str], stop_id: str) -> list[BusStopTime]:
    """Returns a list of bus stop times from the GTFS data."""

    bus_stop_times = []

    with open("rtd_inventory/stop_times.txt", "r", encoding="UTF-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["trip_id"] in trip_ids:
                if row["stop_id"] != stop_id:
                    continue

                temp_time = datetime.datetime.now().replace(microsecond=0)
                hrs, mins, secs = map(int, row["arrival_time"].split(':'))

                if int(row["arrival_time"][0:2]) > 23:
                    # this means the bus is the next day, so we need to adjust the date to tomorrow
                    temp_time = temp_time + datetime.timedelta(days=1)
                    temp_time = temp_time.replace(hour=hrs - 24, minute=mins, second=secs)
                else:
                    temp_time = temp_time.replace(hour=hrs, minute=mins, second=secs)

                bus_stop_times.append(BusStopTime(
                    trip_id=row["trip_id"],
                    arrival_time=temp_time,
                    departure_time=temp_time, # RTD seems to use the same time for arrival and departure
                    stop_id=row["stop_id"],
                    stop_sequence=int(row["stop_sequence"]),
                    stop_headsign=row["stop_headsign"],
                    pickup_type=row["pickup_type"],
                    drop_off_type=row["drop_off_type"],
                    shape_dist_traveled=row["shape_dist_traveled"],
                    timepoint=row["timepoint"]
                ))

    bus_stop_times.sort(key=lambda x: x.arrival_time)
    return bus_stop_times

def get_bus_stop(stop_id: str) -> BusStop:
    """Returns a list of bus stops from the GTFS data."""

    with open("rtd_inventory/stops.txt", "r", encoding="UTF-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["stop_id"] == stop_id:
                return BusStop(
                    stop_id=row["stop_id"],
                    stop_code=row["stop_code"],
                    stop_name=row["stop_name"],
                    stop_desc=row["stop_desc"],
                    stop_lat=float(row["stop_lat"]),
                    stop_lon=float(row["stop_lon"]),
                    zone_id=row["zone_id"],
                    stop_url=row["stop_url"],
                    location_type=int(row["location_type"]),
                    parent_station=row["parent_station"],
                    stop_timezone=row["stop_timezone"],
                    wheelchair_boarding=int(row["wheelchair_boarding"])
                )

    return None

def get_bus_route(route_id: str) -> BusRoute:
    """Returns a list of bus routes from the GTFS data."""

    with open("rtd_inventory/routes.txt", "r", encoding="UTF-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["route_id"] == route_id:
                return BusRoute(
                    route_long_name=row["route_long_name"],
                    route_type=int(row["route_type"]),
                    route_text_color=row["route_text_color"],
                    route_color=row["route_color"],
                    agency_id=row["agency_id"],
                    route_id=row["route_id"],
                    route_url=row["route_url"],
                    route_desc=row["route_desc"],
                    route_short_name=row["route_short_name"],
                )

    return None


def get_next_scheduled_bus(config: Config, route_id: str, stop_id: str, service_ids: list[str]) -> str:
    """Returns the remaining time until the next scheduled bus arrives at the given stop."""

    bus_trips = get_bus_trips(route_id, service_ids)
    bus_stop_times = get_bus_stop_times([bus_trip.trip_id for bus_trip in bus_trips], stop_id)
    
    for stop_time in bus_stop_times:
        
        if stop_time.arrival_time.time() >= datetime.datetime.now().time():
            return get_remaining_time(stop_time.arrival_time)
    return None


def get_next_bus(config: Config, route_id, stop_id) -> str:
    """Returns the remaining time until the next live data bus arrives at the given stop."""

    try:
        feed = pb.FeedMessage()
        response = requests.get(config.rtd_urls.trip_update, timeout=10)
        feed.ParseFromString(response.content)
    except Exception as e:
        print(f"Failed to get GTFS feed: {e}")
        return None

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
    if minutes > 60:
        return f"{minutes // 60}h"
    return f"{minutes}m"


def get_remaining_time_text(date: datetime.datetime) -> str:
    """Returns a string of the remaining time until the given date."""

    now = datetime.datetime.now()
    minutes = int((date - now).total_seconds() / 60)
    return f"At {date.time()}, {minutes} minutes"


def get_current_service_ids(config: Config) -> list[str]:
    current_day = datetime.datetime.now().weekday()
    if current_day == 4:
        return config.day_schedules.friday
    if current_day == 5:
        return config.day_schedules.saturday
    if current_day == 6:
        return config.day_schedules.sunday
    return config.day_schedules.monday_to_thursday


def parse_args():
    """Parses the command line arguments"""

    parser = argparse.ArgumentParser(description="Get the next bus arrival time")
    parser.add_argument("route_id", type=str, help="The route ID")
    parser.add_argument("stop_id", type=str, help="The stop ID")
    return parser.parse_args()


def write_csv(data: list[list]) -> None:
    """Writes the given data to a CSV file"""

    if not os.path.exists("out"):
        os.makedirs("out")

    with open("out/buses", "w", encoding="UTF-8") as file:
        writer = csv.writer(file)
        writer.writerows(data)

def check_inventory(config: Config):
    if not os.path.exists("rtd_inventory"):
        os.makedirs("rtd_inventory")
        print("Downloading GTFS data...")
        response = requests.get(config.rtd_urls.gtfs)
        zip_file_path = os.path.join("rtd_inventory", "google_transit.zip")
        with open(zip_file_path, "wb") as file:
            file.write(response.content)
        with ZipFile(zip_file_path, "r") as zip_file:
            zip_file.extractall("rtd_inventory")
        os.remove(zip_file_path)


def main() -> None:
    """Main entry point"""

    config = load_config()
    check_inventory(config)
    #args = parse_args()
    #route_id = args.route_id
    #stop_id = args.stop_id
    service_ids = get_current_service_ids(config)


    # next_bus = get_next_bus(config, route_id, stop_id)
    # if next_bus is not None:
    #     print(f"Next bus live data: {next_bus}")
    buses_to_save = []
    for bus in config.buses:
        next_dir1_bus = get_next_scheduled_bus(config, bus.num, bus.dir1.stop, service_ids)
        next_dir2_bus = get_next_scheduled_bus(config, bus.num, bus.dir2.stop, service_ids)
        buses_to_save.append([
            bus.num,
            bus.dir1.short,
            next_dir1_bus,
            bus.dir2.short,
            next_dir2_bus
        ])
    write_csv(buses_to_save)
    # next_scheduled_bus = get_next_scheduled_bus(config, route_id, stop_id, service_ids)
    # print(f"Next bus scheduled data: {next_scheduled_bus}")


if __name__ == "__main__":
    main()
