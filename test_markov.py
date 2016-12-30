import unittest
from markov import *


class MarkovUnitTestCase(unittest.TestCase):

    def test_calculate_direction_1(self):
        """ 1st positive test for calculate_direction function """

        user_id = 1
        lat_1 = 37.7472843749906
        lon_1 = -122.448249748807
        lat_2 = 37.7631673875554
        lon_2 = -122.407395473975

        route = MarkovCalculation(user_id, lat_1, lon_1)

        assert route.calculate_direction(lat_1, lon_1, lat_2, lon_2) == 0

    def test_calculate_direction_2(self):
        """ 2nd positive test for calculate_direction function """

        user_id = 1
        lat_1 = 37.774034
        lon_1 = -122.452745
        lat_2 = 37.745577
        lon_2 = -122.452037

        route = MarkovCalculation(user_id, lat_1, lon_1)

        assert route.calculate_direction(lat_1, lon_1, lat_2, lon_2) == 270

    def test_tally_route_by_accepted(self):
        """ Positive test for finding number accepted and total number of all_routes
        by angle

        """

        user_id = 1
        lat_1 = 37.774034
        lon_1 = -122.452745

        route = MarkovCalculation(user_id, lat_1, lon_1)

        all_routes = [(5, 270), (None, 270), (None, 90), (2, 180), (None, 180), (None, 225), (5, 90), (None, 135), (None, 45), (None, 135), (None, 270), (None, 45), (None, 45), (None, 45), (None, 45), (4, 225), (None, 45), (None, 45), (2, 135), (None, 45), (None, 270), (None, 270), (None, 0), (None, 270), (None, 45), (None, 45), (None, 45), (None, 315), (None, 270), (None, 315), (3, 315), (3, 270), (2, 270), (1, 270), (3, 270), (1, 270), (5, 45), (1, 45), (3, 45), (1, 45), (1, 270), (2, 315), (None, 0), (5, 270), (None, 315), (3, 45), (5, 45), (4, 270)]
        assert route.tally_route_by_accepted(all_routes) == {0: {'total': 2, 'accepted': 0}, 225: {'total': 2, 'accepted': 1}, 135: {'total': 3, 'accepted': 1}, 45: {'total': 17, 'accepted': 6}, 270: {'total': 15, 'accepted': 9}, 180: {'total': 2, 'accepted': 1}, 90: {'total': 2, 'accepted': 1}, 315: {'total': 5, 'accepted': 2}}

    def test_generate_weighted_angle(self):
        """ Positive test for creating dict with non-normalized ratio by angle """

        user_id = 1
        lat_1 = 37.774034
        lon_1 = -122.452745

        route = MarkovCalculation(user_id, lat_1, lon_1)

        route.accepted_vs_total = {0: {'total': 2, 'accepted': 0}, 225: {'total': 2, 'accepted': 1}, 135: {'total': 3, 'accepted': 1}, 45: {'total': 17, 'accepted': 6}, 270: {'total': 15, 'accepted': 9}, 180: {'total': 2, 'accepted': 1}, 90: {'total': 2, 'accepted': 1}, 315: {'total': 5, 'accepted': 2}}

        assert route.generate_weighted_angles() == {0: 0.0, 225: 2.186274509803922, 135: 1.1862745098039216, 45: 0.35294117647058826, 270: 2.786274509803922, 180: 1.6862745098039216, 90: 0.8529411764705883, 315: 3.186274509803922}


if __name__ == "__main__":
    unittest.main()
