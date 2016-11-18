from model import Route
from math import degrees, atan
import random


def calculate_route_direction(lat_1, lon_1, lat_2, lon_2):
    """ Calculate the angle of the route's first leg """

    # Calculate the angle based on the change in latitude & longitude
    y = lat_2 - lat_1
    x = lon_2 - lon_1
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


def compile_routes_and_directions(start_lat, start_lon, routes):
    """ Compile a list of routes and angle associated with each """

    route_info = []

    for route in routes:
        lat_1 = route.waypoints[0].latitude
        lon_1 = route.waypoints[0].longitude

        # Limit routes to loops starting at the specified start location
        if len(route.waypoints) > 2 and lat_1 == start_lat and lon_1 == start_lon:
            lat_2 = route.waypoints[1].latitude
            lon_2 = route.waypoints[1].longitude

            route_info.append((route.score, calculate_route_direction(lat_1, lon_1, lat_2, lon_2)))

    return route_info


def tally_route_by_accepted(all_routes):
    """
    Determine how often a route's direction is accepted + total number of routes
    that go in a given direction
    """

    accepted_vs_total = {}

    for item in all_routes:
        scored = item[0]
        angle = item[1]

        # Build dictionary for each new key
        # Future refactor: dict.get
        if angle not in accepted_vs_total:
            accepted_vs_total[angle] = {}
            accepted_vs_total[angle]['accepted'] = 0
            accepted_vs_total[angle]['total'] = 0

        # Count as 'accepted' if user has scored the route
        if scored:
            accepted_vs_total[angle]['accepted'] += 1

        accepted_vs_total[angle]['total'] += 1

    return accepted_vs_total


def generate_weighted_angles(accepted_vs_total):
    """
    Create dictionary where:
       key = sum(accepted/total) up to that point
       value = degree range
    """

    acceptance_rate = {}
    ratio_total = 0

    # Return None if not all cardinal directions are represented
    # Future refactor: base user 'iteritems' instead of 'range'
    for direction in range(0, 360, 45):
        if direction not in accepted_vs_total:
            return None

        ratio = float(accepted_vs_total[direction]['accepted']) / accepted_vs_total[direction]['total']

        # Add ratio to non-normalized total
        ratio_total += ratio

        # Create non-normalized keys for Markov Chain
        acceptance_rate[ratio_total] = direction

    return (ratio_total, acceptance_rate)


def generate_new_angle(ratio_total, acceptance_rate):
    """ Generate random angle based on historical user trends """

    # Select a random float value between 0 and the non-normalized sum of ratios
    seed = random.uniform(0, ratio_total)

    # Set a generically large value that will never be approached
    closest_key = 100

    # Determine which key is the closest upper limit to the seed value
    for key in acceptance_rate.keys():
        if seed < key and key < closest_key:
            closest_key = key

    # Determine lower bound of angle, calculate a new angle within 45-degree range
    degree_min = acceptance_rate[closest_key]
    new_angle = random.randrange(degree_min, degree_min + 45)

    return new_angle


def calculate_weighted_angle(user_id, start_lat, start_lon):
    """ Calculate angle based on user's direction preferences """

    # FUTURE ADDITION: make user_id dynamic

    # Generate a list of route objects
    routes = Route.query.filter(Route.user_id == user_id).all()

    # For each route object, obtain score & direction of first leg
    route_info = compile_routes_and_directions(start_lat, start_lon, routes)

    # Tally the number of accepted vs. total routes for each cardinal direction
    accepted_vs_total = tally_route_by_accepted(route_info)

    # Determine acceptance rate for each cardinal direction, come up with weighted values
    if generate_weighted_angles(accepted_vs_total) is None:
        return None
    else:
        ratio_total, acceptance_rate = generate_weighted_angles(accepted_vs_total)

    # Generate angle based on weighted values
    new_angle = generate_new_angle(ratio_total, acceptance_rate)

    return new_angle
