from math import cos, sin, radians
from random import randrange, choice
import googlemaps
import requests
import os

google_api_key = os.environ["GOOGLE_API_KEY"]
gmaps = googlemaps.Client(key=google_api_key)

MILES_BETWEEN_LATS = 69
MILES_BETWEEN_LONS = 55


def calculate_waypoints(lat_1, lon_1, miles):
    """ For loop routes, come up with random route based on start location &
        miles specified """

    # Generate a random number of waypoints
    num_legs = randrange(3, 6)

    # Calculate length of each leg
    miles_leg = miles / (num_legs + 1)

    # Calculate number of elevation samples to request for elevation data
    elevation_sample_size = int(miles * 5)

    # Generate random direction for first leg of route, calculate waypoints
    angle = randrange(0, 360)
    lat_2 = lat_1 + (sin(radians(angle))*miles_leg)/MILES_BETWEEN_LATS
    lon_2 = lon_1 + (cos(radians(angle))*miles_leg)/MILES_BETWEEN_LONS

    # Random choice of clockwise vs. count-clockwise loop
    angle_diff = choice([-360/num_legs, 360/num_legs])

    # Initialize waypoints list with first 2 pairs of lat/lons
    waypoints = [[lat_1, lon_1], [lat_2, lon_2]]

    for index, leg in enumerate(range(num_legs - 2)):
        prev_lat = waypoints[index - 1][0]
        prev_lon = waypoints[index - 1][1]

        lat = prev_lat + (sin(radians(angle+angle_diff))*miles_leg)/MILES_BETWEEN_LATS
        lon = prev_lon + (cos(radians(angle+angle_diff))*miles_leg)/MILES_BETWEEN_LONS

        waypoints.append([lat, lon])

    return waypoints, elevation_sample_size


def calculate_distance_time(waypoints):
    """ Calculate total miles and minutes for route """

    index = 0
    total_miles = 0
    total_minutes = 0

    while index < len(waypoints):
        # Extract start waypoint for one leg of the route
        lat_a = waypoints[index][0]
        lon_a = waypoints[index][1]

        # Extract end waypoint for one leg of the route, looping to beginning
        #  of list to complete round trip
        if index + 1 == len(waypoints):
            lat_b = waypoints[0][0]
            lon_b = waypoints[0][1]
        else:
            lat_b = waypoints[index + 1][0]
            lon_b = waypoints[index + 1][1]

        # Call Google Maps API to get mileage & time information
        directions = gmaps.directions(("{}, {}").format(lat_a, lon_a),
                                      ("{}, {}").format(lat_b, lon_b),
                                      mode="bicycling")

        time = directions[0]["legs"][0]["duration"]["text"].split()
        hours = int(time[-4]) * 60 if len(time) == 4 else 0

        total_miles += float(directions[0]["legs"][0]["distance"]["text"][:-3])
        total_minutes += int(time[-2]) + hours

        index += 1

    return total_miles, total_minutes


def calculate_elevation(waypoints, sample_size):
    """ Calculate elevation (in feet) for route """

    # Format lat/lon pairs according to API format
    path = ""
    for lat_lon in waypoints:
        lat = str(lat_lon[0])
        lon = str(lat_lon[1])
        path += "%s,%s|" % (lat, lon)

    # Add original lat/lon pair to conclude round-trip path
    lat_1 = str(waypoints[0][0])
    lon_1 = str(waypoints[0][1])
    path += "%s,%s" % (lat_1, lon_1)

    # Obtain elevation data from Google Elevation API
    r = requests.get("https://maps.googleapis.com/maps/api/elevation/json?path=%s&samples=%s&key=%s"
                     % (path, sample_size, google_api_key))

    elevation_data = r.json()
    elevation_list = elevation_data["results"]

    ascent_meters = 0
    descent_meters = 0

    # Calculate change in elevation between sample points
    for index, elevation_point in enumerate(elevation_list):
        if index > 0:
            last_ele = elevation_point["elevation"]
            this_ele = elevation_list[index-1]["elevation"]
            if this_ele > last_ele:
                ascent_meters += (this_ele - last_ele)
            else:
                descent_meters += (last_ele - this_ele)

    ascent_feet = ascent_meters * 3.28
    descent_feet = descent_meters * 3.28

    return ascent_feet, descent_feet


def calculate_midpoint(waypoints):
    """ Calculate midpoint of lat/lon points to center maps """

    mid_lat = 0
    mid_lon = 0

    for lat_lon in waypoints:
        mid_lat += lat_lon[0]
        mid_lon += lat_lon[1]

    mid_lat = mid_lat / len(waypoints)
    mid_lon = mid_lon / len(waypoints)

    return mid_lat, mid_lon


def geocode_address(address):
    """ Geocode address, extract latitude & longitude for route calculations """
    geocoded_address = gmaps.geocode(address)

    latitude = geocoded_address[0]['geometry']['location']['lat']
    longitude = geocoded_address[0]['geometry']['location']['lng']

    return latitude, longitude
