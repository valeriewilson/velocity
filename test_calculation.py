import unittest
import calculation


class CalculationUnitTestCase(unittest.TestCase):

    def test_calculate_elevation(self):
        # Positive test for calculate_elevation function
        waypoints = [(37.7472843749906, -122.448249748807),
                     (37.7631673875554, -122.407395473975)]
        sample_size = 20

        assert calculation.calculate_elevation(waypoints, sample_size) == \
            (629.9725010681151, 629.9725010681151)

    def test_calculate_midpoint(self):
        # Positive test for calculate_midpoint function

        waypoints = [(37.7472843749906, -122.448249748807),
                     (37.7631673875554, -122.407395473975)]

        assert calculation.calculate_midpoint(waypoints) == \
            (37.755225881273, -122.42782261139101)


if __name__ == "__main__":
    unittest.main()
