import unittest
from calculation import *


class CalculationUnitTestCase(unittest.TestCase):

    def test_calculate_elevation(self):
        """ Positive test for calculate_elevation function"""

        route = RouteMetadata(1, "loop", 37.7472843749906, -122.448249748807, 12)

        route.waypoints = [(37.7472843749906, -122.448249748807),
                           (37.7631673875554, -122.407395473975)]
        route.elevation_sample_size = 20

        assert route.calculate_elevation() == (629.9725010681151, 629.9725010681151)

    def test_calculate_midpoint(self):
        """ Positive test for calculate_midpoint function """

        route = RouteMetadata(1, "loop", 37.7472843749906, -122.448249748807, 12)

        route.waypoints = [(37.7472843749906, -122.448249748807),
                           (37.7631673875554, -122.407395473975)]

        assert route.calculate_midpoint() == (37.755225881273, -122.42782261139101)

    def test_geocode_address(self):
        """ Positive test for geocode_address function """

        address = '683 Sutter St San Francisco'
        assert geocode_address(address) == (37.7886679, -122.4114987)


if __name__ == "__main__":
    unittest.main()
