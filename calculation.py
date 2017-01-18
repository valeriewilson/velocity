from math import cos, sin, radians
from random import randrange, choice, uniform
import googlemaps
import requests
from markov import *

google_api_key = "AIzaSyBlY0gdpn-82bFjwWdaAPdQ_oOtJwd9Y3s"
gmaps = googlemaps.Client(key=google_api_key)


class RouteMetadata(object):

    def __init__(self, user_id, route_type, lat_1, lon_1, miles):
        self.route_type = route_type
        self.miles_lats = 69
        self.miles_lons = 55
        self.user_id = user_id
        self.lat_1 = lat_1
        self.lon_1 = lon_1
        self.miles = miles
        self.total_miles = 0
        self.total_minutes = 0
        self.mid_lat = 0
        self.mid_lon = 0

    def calculate_waypoints(self):
        """
        For loop routes, come up with random route based on start location &
        miles specified

        """

        # Generate a random number of waypoints
        num_legs = randrange(3, 4)

        # Calculate leg distance
        miles_leg = self.miles / (num_legs + 1)

        # Calculate variation in leg distance
        mile_var = uniform((-miles_leg / 2), (miles_leg / 2))

        # Calculate number of elevation samples to request for elevation data
        self.elevation_sample_size = int(self.miles * 5)

        # Generate random direction for first leg of route, calculate waypoints
        markov_angle = MarkovCalculation(self.user_id, self.lat_1, self.lon_1)

        weighted_angle = markov_angle.calculate_weighted_angle()
        angle = weighted_angle if weighted_angle else randrange(0, 360)

        lat_2 = self.lat_1 + (sin(radians(angle)) * (miles_leg + mile_var)) / self.miles_lats
        lon_2 = self.lon_1 + (cos(radians(angle)) * (miles_leg + mile_var)) / self.miles_lons

        # Random choice of clockwise vs. count-clockwise loop
        angle_diff = choice([-360/num_legs, 360/num_legs])

        # Initialize waypoints list with first 2 pairs of lat/lons
        self.waypoints = [[self.lat_1, self.lon_1], [lat_2, lon_2]]

        for index, leg in enumerate(range(num_legs - 2)):
            prev_lat = self.waypoints[index - 1][0]
            prev_lon = self.waypoints[index - 1][1]

            lat = prev_lat + (sin(radians(angle + angle_diff)) * (miles_leg - mile_var)) / self.miles_lats
            lon = prev_lon + (cos(radians(angle + angle_diff)) * (miles_leg - mile_var)) / self.miles_lons

            self.waypoints.append([lat, lon])

        return self.waypoints, self.elevation_sample_size

    def calculate_distance_time(self):
        """ Calculate total miles and minutes for route """

        index = 0

        while index < len(self.waypoints):
            # Extract start waypoint for one leg of the route
            lat_a = self.waypoints[index][0]
            lon_a = self.waypoints[index][1]

            # Extract end waypoint for one leg of the route, looping to beginning
            #  of list to complete round trip
            if index + 1 == len(self.waypoints):
                lat_b = self.waypoints[0][0]
                lon_b = self.waypoints[0][1]
            else:
                lat_b = self.waypoints[index + 1][0]
                lon_b = self.waypoints[index + 1][1]

            # Call Google Maps API to get mileage & time information
            directions = gmaps.directions(("{}, {}").format(lat_a, lon_a),
                                          ("{}, {}").format(lat_b, lon_b),
                                          mode="bicycling")

            time = directions[0]["legs"][0]["duration"]["text"].split()
            hours = int(time[-4]) * 60 if len(time) == 4 else 0

            self.total_miles += float(directions[0]["legs"][0]["distance"]["text"][:-3])
            self.total_minutes += int(time[-2]) + hours

            index += 1

        return self.total_miles, self.total_minutes

    def calculate_elevation(self):
        """ Calculate elevation (in feet) for route """

        # Format lat/lon pairs according to API format
        path = ""
        for lat_lon in self.waypoints:
            lat = str(lat_lon[0])
            lon = str(lat_lon[1])
            path += "%s,%s|" % (lat, lon)

        # Add original lat/lon pair to conclude round-trip path
        lat_1 = str(self.waypoints[0][0])
        lon_1 = str(self.waypoints[0][1])
        path += "%s,%s" % (lat_1, lon_1)

        if self.route_type == "midpoint":
            self.elevation_sample_size = 20

        # Obtain elevation data from Google Elevation API
        r = requests.get("https://maps.googleapis.com/maps/api/elevation/json?path=%s&samples=%s&key=%s"
                         % (path, self.elevation_sample_size, google_api_key))

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

        self.ascent_feet = ascent_meters * 3.28
        self.descent_feet = descent_meters * 3.28

        return self.ascent_feet, self.descent_feet

    def calculate_midpoint(self):
        """ Calculate midpoint of lat/lon points to center maps """

        for lat_lon in self.waypoints:
            self.mid_lat += lat_lon[0]
            self.mid_lon += lat_lon[1]

        self.mid_lat = self.mid_lat / len(self.waypoints)
        self.mid_lon = self.mid_lon / len(self.waypoints)

        return self.mid_lat, self.mid_lon


def geocode_address(address):
    """ Geocode address, extract latitude & longitude for route calculations """
    geocoded_address = gmaps.geocode(address)

    start_lat = geocoded_address[0]['geometry']['location']['lat']
    start_lon = geocoded_address[0]['geometry']['location']['lng']

    return start_lat, start_lon
