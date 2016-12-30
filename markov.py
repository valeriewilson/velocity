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
            self.generate_weighted_angles()

        # Generate angle based on weighted values
        new_angle = self.generate_new_angle()

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

                route_info.append((route.score, self.calculate_direction(lat_1, lon_1,
                                                                         lat_2, lon_2)))

        return route_info

    def calculate_direction(self, lat_1, lon_1, lat_2, lon_2):
        """ Calculate the angle of the route's first leg """

        # Calculate the angle based on the change in latitude & longitude
        y = lat_2 - lat_1
        x = (lon_2 - lon_1) if abs(lon_2 - lon_1) > 0 else 0.0001

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
        that go in a given direction """

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

        """

        ratio_total = 0
        non_normalized_rates = {}
        self.normalized_rates = {}
        self.normalized_angles = {}

        # Create dictionary of non-normalized rates if all directions available
        for direction in range(0, 360, 45):
            if direction not in self.accepted_vs_total:
                return None

            ratio = float(self.accepted_vs_total[direction]['accepted']) / \
                self.accepted_vs_total[direction]['total']

            ratio_total += ratio

            if ratio_total in non_normalized_rates.values():
                self.normalized_angles[direction] = 0
            else:
                non_normalized_rates[direction] = ratio_total

        # Create normalized keys for Markov Chain angle calculation
        for direction in non_normalized_rates:
            normalized_ratio = non_normalized_rates[direction] / ratio_total

            self.normalized_rates[normalized_ratio] = direction

        # Create the normalized percentage by angle for D3 integration
        sorted_rates = sorted(self.normalized_rates)

        for i in range(len(sorted_rates)):
            direction = self.normalized_rates[sorted_rates[i]]

            if i == 0:
                self.normalized_angles[direction] = sorted_rates[i]
            else:
                self.normalized_angles[direction] = sorted_rates[i] - sorted_rates[i - 1]

        return non_normalized_rates

    def generate_new_angle(self):
        """ Generate random angle based on historical user trends """

        # Select a random float value between 0 and the non-normalized sum of ratios
        seed = random.uniform(0, 1)

        # Set a generically large value that will never be approached
        closest_key = 100

        # Determine which key is the closest upper limit to the seed value
        for key in self.normalized_rates.keys():
            if seed < key and key < closest_key:
                closest_key = key

        # Determine lower bound of angle, calculate a new angle within 45-degree range
        degree_min = self.normalized_rates[closest_key]
        self.new_angle = random.randrange(degree_min, degree_min + 45)

        return self.new_angle
