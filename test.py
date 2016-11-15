from unittest import TestCase
from server import app
from model import db, connect_to_db, example_data


class FlaskTests(TestCase):

    def setUp(self):
        """ Set-up for each test """

        self.client = app.test_client()
        app.config['TESTING'] = True

    def test_login_route(self):
        """ Verify that login page renders correctly """

        result = self.client.get("/login")
        self.assertEqual(result.status_code, 200)
        self.assertIn('<h2>Log In / <a href="/register">Register</a></h2>', result.data)

    def test_register_route_get(self):
        """ Verify that register page renders correctly """

        result = self.client.get("/register")
        self.assertEqual(result.status_code, 200)
        self.assertIn('<h2><a href="/login">Log In</a> / Register</h2>', result.data)


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
        self.assertIn('<h2>Bike Route Inputs</h2>', result.data)


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


if __name__ == "__main__":
    import unittest

    unittest.main()
