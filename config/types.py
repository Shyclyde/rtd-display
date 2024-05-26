from dataclasses import dataclass
from datetime import datetime


@dataclass
class BusTrip:
    block_id: str
    route_id: str
    direction_id: int
    trip_headsign: str
    shape_id: str
    service_id: str
    trip_id: str

@dataclass
class BusStopTime:
    trip_id: str
    arrival_time: datetime
    departure_time: datetime
    stop_id: str
    stop_sequence: int
    stop_headsign: str
    pickup_type: str
    drop_off_type: str
    shape_dist_traveled: str
    timepoint: str

@dataclass
class BusStop:
    stop_id: str
    stop_code: str
    stop_name: str
    stop_desc: str
    stop_lat: float
    stop_lon: float
    zone_id: str
    stop_url: str
    location_type: int
    parent_station: str
    stop_timezone: str
    wheelchair_boarding: int

@dataclass
class BusRoute:
    route_long_name: str
    route_type: int
    route_text_color: str
    route_color: str
    agency_id: str
    route_id: str
    route_url: str
    route_desc: str
    route_short_name: str

@dataclass
class BusCalendar:
    service_id: str
    monday: int
    tuesday: int
    wednesday: int
    thursday: int
    friday: int
    saturday: int
    sunday: int
    start_date: datetime.date
    end_date: datetime.date

@dataclass
class BusCalendarDate:
    service_id: str
    date: datetime.date
    exception_type: int