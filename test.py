from unittest import TestCase
from server import app
from model import db, connect_to_db, example_data
import unittest
from calculation import *
from markov import *


class FlaskTests(TestCase):

    def setUp(self):
        """ Set-up for each test """

        self.client = app.test_client()
        app.config['TESTING'] = True

    def test_login_route(self):
        """ Verify that login page renders correctly """

        result = self.client.get("/login")
        self.assertEqual(result.status_code, 200)
        self.assertIn('<h3>Log In / <a href="/register">Register</a></h3>', result.data)

    def test_register_route_get(self):
        """ Verify that register page renders correctly """

        result = self.client.get("/register")
        self.assertEqual(result.status_code, 200)
        self.assertIn('<h3><a href="/login">Log In</a> / Register</h3>', result.data)


class FlaskTestsLoggedIn(TestCase):

    def setUp(self):
        """ Set-up for each test """

        app.config['TESTING'] = True
        self.client = app.test_client()

        # Connect to test database
        connect_to_db(app, "postgresql:///testdb")

        # Set up database with sample data
        db.create_all()
        example_data()

        with self.client as c:
            with c.session_transaction() as sess:
                sess['user_email'] = 'test@test.com'

    def tearDown(self):
        """ Drop session and database following each test """

        db.session.close()
        db.drop_all()

    def test_home_route(self):
        """ Verify that home page renders correctly """

        result = self.client.get("/")
        self.assertEqual(result.status_code, 200)
        self.assertIn('<h3>Route Creator</h3>', result.data)

    def test_routes_route(self):
        """ Verify that routes page renders correctly """

        result = self.client.get("/routes")
        self.assertEqual(result.status_code, 200)
        self.assertIn('<h3>Filter Options</h3>', result.data)

    def test_filter_route(self):
        """ Verify that filter endpoint returns correct results """

        result = self.client.get("/filter?min-miles=12",
                                 follow_redirects=False)

        self.assertEqual(result.status_code, 200)
        self.assertIn("15.0", result.data)
        self.assertNotIn("10.0", result.data)

    def test_update_stats_route(self):
        """ Verify that update-stats endpoint returns no results for too few routes """

        result = self.client.post("/update-stats",
                                  data={"start-location": "Avenue Cyclery"},
                                  follow_redirects=True)

        self.assertEqual(result.status_code, 200)
        self.assertIn("{}", result.data)

    def test_new_address_route(self):
        """ Verify that new address endpoint returns correct results """

        result = self.client.post("/new-address",
                                  data={"new-address-field": "1073 Market St, San Francisco, CA, United States",
                                        "label-field": "Huckleberry Bicycles",
                                        "default-address": "False"},
                                  follow_redirects=False)

        self.assertEqual(result.status_code, 200)
        self.assertIn("Huckleberry", result.data)

    def test_waypoints_route(self):
        """ Verify that waypoints endpoint returns correct waypoints """

        result = self.client.get("/waypoints.json?route-id=1",
                                 follow_redirects=False)

        self.assertEqual(result.status_code, 200)
        self.assertIn('"lat": 37.7694811467305', result.data)
        self.assertIn('"lng": -122.399497857258', result.data)
        self.assertIn('"lat": 37.74020601769157', result.data)
        self.assertIn('"lng": -122.44485190051067', result.data)


class FlashTestLoggingIn(TestCase):

    def setUp(self):
        """ Set-up for each test """

        app.config['TESTING'] = True
        self.client = app.test_client()

        # Connect to test database
        connect_to_db(app, "postgresql:///testdb")

        # Set up database with sample data
        db.create_all()
        example_data()

    def tearDown(self):
        """ Drop session and database following each test """

        db.session.close()
        db.drop_all()

    def test_login_route_post(self):
        """ Verify that login page processes data correctly """

        result = self.client.post("/login",
                                  data={"email": "test@test.com", "password": "test123"},
                                  follow_redirects=True)

        self.assertIn("Successfully logged in", result.data)

    def test_login_route_post_bad_username(self):
        """ Verify that login page processes data correctly """

        result = self.client.post("/login",
                                  data={"email": "testclient@test.com", "password": "test123"},
                                  follow_redirects=True)

        self.assertIn("Invalid email address", result.data)

    def test_login_route_post_bad_password(self):
        """ Verify that login page processes data correctly """

        result = self.client.post("/login",
                                  data={"email": "test@test.com", "password": "incorrect"},
                                  follow_redirects=True)

        self.assertIn("Incorrect password", result.data)

    def test_register_route_post(self):
        """ Verify that register page processes data correctly """

        result = self.client.post("/register",
                                  data={"email": "test@client.com",
                                        "password": "test123",
                                        "first-name": "Test",
                                        "last-name": "Client"},
                                  follow_redirects=True)

        self.assertIn("Successfully registered", result.data)

    def test_register_route_post_existing(self):
        """ Verify that previously registered user cannot be re-registered """

        result = self.client.post("/register",
                                  data={"email": "test@test.com",
                                        "password": "test123",
                                        "first-name": "Test",
                                        "last-name": "Client"},
                                  follow_redirects=True)

        self.assertIn("A user with that email address already exists", result.data)


class CalculationUnitTestCase(unittest.TestCase):

    def test_calculate_distance_time(self):
        """ Positive test for calculate_distance_time method """

        route = RouteMetadata(1, "loop", 37.7680873, -122.452986, 8)

        route.waypoints = [[37.7680873, -122.452986],
                          [37.74046240241025, -122.45724130642759],
                          [37.75860030001992, -122.48743796849598]]

        assert route.calculate_distance_time() == (8.3, 56)

    def test_calculate_elevation(self):
        """ Positive test for calculate_elevation method """

        route = RouteMetadata(1, "loop", 37.7472843749906, -122.448249748807, 12)

        route.waypoints = [(37.7472843749906, -122.448249748807),
                           (37.7631673875554, -122.407395473975)]
        route.elevation_sample_size = 20

        assert route.calculate_elevation() == (629.9725010681151, 629.9725010681151)

    def test_calculate_midpoint(self):
        """ Positive test for calculate_midpoint method """

        route = RouteMetadata(1, "loop", 37.7472843749906, -122.448249748807, 12)

        route.waypoints = [(37.7472843749906, -122.448249748807),
                           (37.7631673875554, -122.407395473975)]

        assert route.calculate_midpoint() == (37.755225881273, -122.42782261139101)

    def test_geocode_address(self):
        """ Positive test for geocode_address function """

        address = '683 Sutter St San Francisco'
        assert geocode_address(address) == (37.7886679, -122.4114987)


class MarkovUnitTestCase(unittest.TestCase):

    def setUp(self):
        db.create_all()
        example_data()

        self.user_id = 1
        self.lat_1 = 37.7472843749906
        self.lon_1 = -122.448249748807
        self.lat_2 = 37.7631673875554
        self.lon_2 = -122.407395473975

        self.route = MarkovCalculation(self.user_id, self.lat_1, self.lon_1)

    def tearDown(self):
        """ Drop session and database following each test """

        db.session.close()
        db.drop_all()

    def test_compile_routes_and_directions(self):
        """ Positive test for compile_routes_and_directions method """

        assert self.route.compile_routes_and_directions() == [(4, 0), (3, 180), (0, 0)]

    def test_calculate_direction_1(self):
        """ 1st positive test for calculate_direction method """

        assert self.route.calculate_direction(self.lat_1, self.lon_1, self.lat_2, self.lon_2) == 0

    def test_calculate_direction_2(self):
        """ 2nd positive test for calculate_direction method """

        self.lat_1 = 37.774034
        self.lon_1 = -122.452745
        self.lat_2 = 37.745577
        self.lon_2 = -122.452037

        assert self.route.calculate_direction(self.lat_1, self.lon_1, self.lat_2, self.lon_2) == 270

    def test_tally_route_by_accepted(self):
        """ Positive test for finding number accepted and total number of all_routes
        by angle

        """

        all_routes = [(5, 270), (None, 270), (None, 90), (2, 180), (None, 180), (None, 225), (5, 90), (None, 135), (None, 45), (None, 135), (None, 270), (None, 45), (None, 45), (None, 45), (None, 45), (4, 225), (None, 45), (None, 45), (2, 135), (None, 45), (None, 270), (None, 270), (None, 0), (None, 270), (None, 45), (None, 45), (None, 45), (None, 315), (None, 270), (None, 315), (3, 315), (3, 270), (2, 270), (1, 270), (3, 270), (1, 270), (5, 45), (1, 45), (3, 45), (1, 45), (1, 270), (2, 315), (None, 0), (5, 270), (None, 315), (3, 45), (5, 45), (4, 270)]

        assert self.route.tally_route_by_accepted(all_routes) == {0: {'total': 2, 'accepted': 0}, 225: {'total': 2, 'accepted': 1}, 135: {'total': 3, 'accepted': 1}, 45: {'total': 17, 'accepted': 6}, 270: {'total': 15, 'accepted': 9}, 180: {'total': 2, 'accepted': 1}, 90: {'total': 2, 'accepted': 1}, 315: {'total': 5, 'accepted': 2}}

    def test_generate_weighted_angle(self):
        """ Positive test for creating dict with non-normalized ratio by angle """

        self.lat_1 = 37.774034
        self.lon_1 = -122.452745

        self.route.accepted_vs_total = {0: {'total': 2, 'accepted': 0}, 225: {'total': 2, 'accepted': 1}, 135: {'total': 3, 'accepted': 1}, 45: {'total': 17, 'accepted': 6}, 270: {'total': 15, 'accepted': 9}, 180: {'total': 2, 'accepted': 1}, 90: {'total': 2, 'accepted': 1}, 315: {'total': 5, 'accepted': 2}}

        assert self.route.generate_weighted_angles() == {0: 0.0, 225: 2.186274509803922, 135: 1.1862745098039216, 45: 0.35294117647058826, 270: 2.786274509803922, 180: 1.6862745098039216, 90: 0.8529411764705883, 315: 3.186274509803922}


if __name__ == "__main__":
    import unittest

    unittest.main()
