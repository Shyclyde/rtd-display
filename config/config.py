"""Import the configuration settings from the config.yaml file."""

from dataclasses import dataclass
from typing import List

from yaml import safe_load
from pydantic import BaseModel

CONFIG_FILE = "config.yaml"

@dataclass
class BusServiceRoute:
    short: str
    stop: str

@dataclass
class BusService:
    num: str
    dir1: BusServiceRoute
    dir2: BusServiceRoute

class Buses(BaseModel):
    buses: List[BusService]

class RTDUrls(BaseModel):
    gtfs: str
    trip_update: str
    vehicle_position: str
    alerts: str

class DaySchedules(BaseModel):
    monday_to_thursday: List[str]
    friday: List[str]
    saturday: List[str]
    sunday: List[str]

class Config(BaseModel):
    rtd_urls: RTDUrls
    day_schedules: DaySchedules
    buses: List[BusService]

def load_config() -> Config:
    with open(CONFIG_FILE, "r", encoding="UTF-8") as file:
        config = safe_load(file)
    return Config(**config)


if __name__ == "__main__":
    print("testing config: \n", load_config())