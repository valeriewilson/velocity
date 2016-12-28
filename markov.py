from model import Route
from math import degrees, atan
import random


class MarkovCalculation(object):

    def __init__(self, user_id, start_lat, start_lon):
        self.user_id = user_id
        self.lat_1 = start_lat
        self.lon_1 = start_lon

    def calculate_weighted_angle(self):
        """ Calculate angle based on user's direction preferences """

        # For each route object, obtain score & direction of first leg
        route_info = self.compile_routes_and_directions()

        # Tally the number of accepted vs. total routes for each cardinal direction
        self.tally_route_by_accepted(route_info)

        # Determine acceptance rate for each cardinal direction, come up with weighted values
        if self.generate_weighted_angles() is None:
            return None
        else:
            ratio_total, acceptance_rate = self.generate_weighted_angles()

        # Generate angle based on weighted values
        new_angle = self.generate_new_angle(ratio_total, acceptance_rate)

        return new_angle

    def compile_routes_and_directions(self):
        """ Compile a list of routes and angle associated with each """

        # Generate a list of route objects
        routes = Route.query.filter(Route.user_id == self.user_id).all()

        route_info = []

        for route in routes:
            lat_1 = route.waypoints[0].latitude
            lon_1 = route.waypoints[0].longitude

            # Limit routes to loops starting at the specified start location
            if len(route.waypoints) > 2 and lat_1 == self.lat_1 and lon_1 == self.lon_1:
                lat_2 = route.waypoints[1].latitude
                lon_2 = route.waypoints[1].longitude

                route_info.append((route.score, self.calculate_route_direction(lat_1, lon_1, lat_2, lon_2)))

        return route_info

    def calculate_route_direction(self, lat_1, lon_1, lat_2, lon_2):
        """ Calculate the angle of the route's first leg

        >>> lat_1 = 37.7472843749906
        >>> lon_1 = -122.448249748807
        >>> lat_2 = 37.7631673875554
        >>> lon_2 = -122.407395473975
        >>> calculate_route_direction(lat_1, lon_1, lat_2, lon_2)
        0

        >>> lat_1 = 37.774034
        >>> lon_1 = -122.452745
        >>> lat_2 = 37.745577
        >>> lon_2 = -122.452037
        >>> calculate_route_direction(lat_1, lon_1, lat_2, lon_2)
        270

        """

        # Calculate the angle based on the change in latitude & longitude
        y = lat_2 - lat_1
        x = (lon_2 - lon_1) if (lon_2 - lon_1) > 0 else 0.0001

        angle = degrees(atan(y / x))

        # If latitude is less than zero, angle should be offset by 180 degrees
        if x < 0:
            angle += 180

        # If angle is between -90 and 0, add 360 to make it positive
        if angle < 0:
            angle += 360

        # Return the route a group (where 0 represents the 0-45 degree range)
        direction = 45 * int(float(angle)/45)

        return direction

    def tally_route_by_accepted(self, all_routes):
        """
        Determine how often a route's direction is accepted + total number of routes
        that go in a given direction

        >>> all_routes = [(5, 270), (None, 270), (None, 90), (2, 180), (None, 180), (None, 225), (5, 90), (None, 135), (None, 45), (None, 135), (None, 270), (None, 45), (None, 45), (None, 45), (None, 45), (4, 225), (None, 45), (None, 45), (2, 135), (None, 45), (None, 270), (None, 270), (None, 0), (None, 270), (None, 45), (None, 45), (None, 45), (None, 315), (None, 270), (None, 315), (3, 315), (3, 270), (2, 270), (1, 270), (3, 270), (1, 270), (5, 45), (1, 45), (3, 45), (1, 45), (1, 270), (2, 315), (None, 0), (5, 270), (None, 315), (3, 45), (5, 45), (4, 270)]
        >>> tally_route_by_accepted(all_routes)
        {0: {'total': 2, 'accepted': 0}, 225: {'total': 2, 'accepted': 1}, 135: {'total': 3, 'accepted': 1}, 45: {'total': 17, 'accepted': 6}, 270: {'total': 15, 'accepted': 9}, 180: {'total': 2, 'accepted': 1}, 90: {'total': 2, 'accepted': 1}, 315: {'total': 5, 'accepted': 2}}

        """

        self.accepted_vs_total = {}

        for item in all_routes:
            scored = item[0]
            angle = item[1]

            # Build dictionary for each new key
            # Future refactor: dict.get
            if angle not in self.accepted_vs_total:
                self.accepted_vs_total[angle] = {}
                self.accepted_vs_total[angle]['accepted'] = 0
                self.accepted_vs_total[angle]['total'] = 0

            # Count as 'accepted' if user has scored the route
            if scored:
                self.accepted_vs_total[angle]['accepted'] += 1

            self.accepted_vs_total[angle]['total'] += 1

        return self.accepted_vs_total

    def generate_weighted_angles(self):
        """
        Create dictionary where:
           key = sum(accepted/total) up to that point
           value = degree range

        >>> accepted_vs_total = {0: {'total': 2, 'accepted': 0}, 225: {'total': 2, 'accepted': 1}, 135: {'total': 3, 'accepted': 1}, 45: {'total': 17, 'accepted': 6}, 270: {'total': 15, 'accepted': 9}, 180: {'total': 2, 'accepted': 1}, 90: {'total': 2, 'accepted': 1}, 315: {'total': 5, 'accepted': 2}}
        >>> generate_weighted_angles(accepted_vs_total)
        (3.186274509803922, {0.0: 0, 1.6862745098039216: 180, 2.786274509803922: 270, 1.1862745098039216: 135, 0.8529411764705883: 90, 2.186274509803922: 225, 0.35294117647058826: 45, 3.186274509803922: 315})

        """

        self.acceptance_rate = {}
        ratio_total = 0

        # Return None if not all cardinal directions are represented
        # Future refactor: base user 'iteritems' instead of 'range'
        for direction in range(0, 360, 45):
            if direction not in self.accepted_vs_total:
                return None

            ratio = float(self.accepted_vs_total[direction]['accepted']) / self.accepted_vs_total[direction]['total']

            # Add ratio to non-normalized total
            ratio_total += ratio

            # Create non-normalized keys for Markov Chain
            self.acceptance_rate[ratio_total] = direction

        return (ratio_total, self.acceptance_rate)

    def generate_new_angle(self, ratio_total):
        """ Generate random angle based on historical user trends """

        # Select a random float value between 0 and the non-normalized sum of ratios
        seed = random.uniform(0, ratio_total)

        # Set a generically large value that will never be approached
        closest_key = 100

        # Determine which key is the closest upper limit to the seed value
        for key in self.acceptance_rate.keys():
            if seed < key and key < closest_key:
                closest_key = key

        # Determine lower bound of angle, calculate a new angle within 45-degree range
        degree_min = self.acceptance_rate[closest_key]
        self.new_angle = random.randrange(degree_min, degree_min + 45)

        return self.new_angle
