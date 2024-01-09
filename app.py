import requests
from google.transit import gtfs_realtime_pb2


def get_next_bus(feed_url, stop_id):
    feed = gtfs_realtime_pb2.FeedMessage()
    response = requests.get(feed_url)
    feed.ParseFromString(response.content)
    print(feed)
    for entity in feed.entity:
        print(entity)
        #print(entity.alert.header_text.translation[0].text)
        # if entity.HasField('trip_update'):
        #     for stop_time_update in entity.trip_update.stop_time_update:
        #         if stop_time_update.stop_id == stop_id:
        #             return stop_time_update.arrival.time

    return None

def main() -> None:
    feed_url = 'https://www.rtd-denver.com/files/gtfs-rt/TripUpdate.pb'
    stop_id = 'D25N'
    next_bus = get_next_bus(feed_url, stop_id)
    print(next_bus)

if __name__ == '__main__':
    main()
