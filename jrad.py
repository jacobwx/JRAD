from opensky_api import OpenSkyApi
from pathlib import Path
import datetime, time
from urllib3.exceptions import ReadTimeoutError

# Use the OpenSky library
api = OpenSkyApi()

# Origin of flight aircraft's position
sources = {0: "ADS-B", 1: "ASTERISX", 2: "MLAT", 3: "FLARM"}

starttime = time.time()

# Ensure that the data folder exists
data = Path("data")
data.mkdir(exist_ok=True, parents=True)

# The files utilized by this script
pfname = data.joinpath("jrad.txt")
icon = data.joinpath("planes.png")

print("\nJRAD\n====\nYou can utilize the placefile located at data/jrad.txt")
print("\nPress Ctrl+C to exit")

# Continuously runs until Ctrl+C
try:
    while True:
        # Wait 60 seconds (without drift) to contact the API
        time.sleep(60.0 - ((time.time() - starttime) % 60.0))

        # Collect all of the API data from OpenSky
        flight_data = api.get_states()

        # Get current time in ISO 8601 format without microseconds
        utc_offset_sec = time.altzone if time.localtime().tm_isdst else time.timezone
        utc_offset = datetime.timedelta(seconds=-utc_offset_sec)
        current = (
            datetime.datetime.now()
            .replace(tzinfo=datetime.timezone(offset=utc_offset))
            .replace(microsecond=0)
            .isoformat()
        )

        # Write the header to the placefile
        with pfname.open("w") as file:
            header = [
                "Refresh: 1",
                "Threshold: 999",
                "Title: JRAD - Flight Positions - %s" % current,
                'Font: 1, 11, 0, "Tahoma"',
                'IconFile: 1, 22, 22, 11, 11, "%s"\n' % icon.resolve(),
            ]
            file.writelines("%s\n" % line for line in header)

            # Analyze each flight with the data received
            for s in flight_data.states:
                # Flight does not exist without a latitude
                if "None" in str(s.latitude):
                    continue
                # Flight does not exist without a longitutde
                elif "None" in str(s.longitude):
                    continue

                # 1 = Yellow
                # 2 = Orange (No contact in last 3 minutes)
                # 3 = Red (If grounded)
                if s.on_ground:
                    status = 3
                elif s.last_contact < time.time() - 180:
                    status = 2
                else:
                    status = 1

                # Check if there is a callsign
                if not s.callsign:
                    callsign = "No Callsign"
                else:
                    callsign = s.callsign.rstrip()

                # Map to the dictionary of sources
                position_source = sources.get(s.position_source)

                # Convert timestamp to ISO 8601 without microseconds
                time_position = (
                    datetime.datetime.fromtimestamp(s.time_position)
                    .replace(tzinfo=datetime.timezone(offset=utc_offset))
                    .replace(microsecond=0)
                    .isoformat()
                )

                # Convert timestamp to ISO 8601 without microseconds
                last_contact = (
                    datetime.datetime.fromtimestamp(s.last_contact)
                    .replace(tzinfo=datetime.timezone(offset=utc_offset))
                    .replace(microsecond=0)
                    .isoformat()
                )

                # Write this flight's information to the placefile
                file_buffer = [
                    "Object: %s, %s" % (s.latitude, s.longitude),
                    "Icon: 0,0,%s,1,%s,Callsign: %s\\nICAO24: %s\\nSquawk: %s\\nSPI: %s\\nSensors: %s\\n===================================\\nOrigin country: %s\\nLast position report: %s\\nLast contact: %s\\nPosition source: %s\\n===================================\\nOn ground: %s\\nLongitude: %s\\nLatitude: %s\\nAltitude: %s\\nVelocity: %s\\nVertical Rate: %s\\nHeading: %s\\nBarometric Altitude: %s"
                    % (
                        s.heading,
                        status,
                        callsign,
                        s.icao24,
                        s.squawk,
                        s.spi,
                        s.sensors,
                        s.origin_country,
                        time_position,
                        last_contact,
                        position_source,
                        s.on_ground,
                        s.longitude,
                        s.latitude,
                        s.geo_altitude,
                        s.velocity,
                        s.vertical_rate,
                        s.heading,
                        s.baro_altitude,
                    ),
                    "End:\n",
                ]
                file.writelines("%s\n" % line for line in file_buffer)

# On Ctrl+C
except KeyboardInterrupt:
    print("\nExiting...")
    pass

# In the event that the connection times out
except ReadTimeoutError:
    print("There was a timeout...trying again.")
