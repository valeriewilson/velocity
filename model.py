""" Models and database functions """

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """ User information """

    __tablename__ = "users"

    user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    email = db.Column(db.String(30), unique=True, nullable=False)
    password = db.Column(db.String(20), nullable=False)
    first_name = db.Column(db.Unicode(30), nullable=False)
    last_name = db.Column(db.Unicode(30), nullable=False)
    phone = db.Column(db.String(20), nullable=False)

    addresses = db.relationship('Address', backref=db.backref('user'))
    routes = db.relationship('Route', backref=db.backref('user'))

    def __repr__(self):
        return "<User id=%s email=%s>" % (self.user_id, self.email)


class Address(db.Model):
    """ Saved addresses for a user """

    __tablename__ = "addresses"

    address_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    label = db.Column(db.String(20), nullable=False)
    address_str = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    is_default = db.Column(db.Boolean, nullable=False)

    def __repr__(self):
        return "<Address id=%s name=%s user=%s>" % \
            (self.address_id, self.label, self.user.user_id)


class Route(db.Model):
    """ Routes created for a user """

    __tablename__ = "routes"

    route_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    total_ascent = db.Column(db.Float, nullable=False)
    total_descent = db.Column(db.Float, nullable=False)
    is_accepted = db.Column(db.Boolean, nullable=False)
    score = db.Column(db.Integer, nullable=True)
    issue = db.Column(db.String(50), nullable=True)
    total_miles = db.Column(db.Float, nullable=False)
    total_minutes = db.Column(db.Float, nullable=False)

    waypoints = db.relationship('Waypoint', backref=db.backref('route'))
    rides = db.relationship('Ride', backref=db.backref('route'))

    def __repr__(self):
        return "<Route id=%s accepted=%s>" % \
            (self.route_id, self.is_accepted)


class Ride(db.Model):
    """ All rides a user does for specific routes """

    __tablename__ = "rides"

    ride_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    route_id = db.Column(db.Integer, db.ForeignKey('routes.route_id'), nullable=False)
    time_of_ride = db.Column(db.DateTime, nullable=False)
    comments = db.Column(db.UnicodeText, nullable=True)

    def __repr__(self):
        return "<Ride id=%s time_of_ride=%s route_id:%s>" % \
            (self.ride_id, self.time_of_ride, self.route.route_id)


class Waypoint(db.Model):
    """ Waypoints for each route """

    __tablename__ = "waypoints"

    waypoint_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    route_id = db.Column(db.Integer, db.ForeignKey('routes.route_id'), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return "<Waypoint id=%s route=%s>" % (self.waypoint_id, self.route.route_id)


def example_data():

    test_user = User(email="test@test.com", password="test123", last_name="Cohen", first_name="Leonard", phone="1231231234")
    db.session.add(test_user)
    db.session.commit()


def connect_to_db(app, db_uri='postgresql:///bike_routes'):
    """Connect the database to our Flask app."""

    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_ECHO'] = True
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.app = app
    db.init_app(app)


if __name__ == "__main__":

    from server import app
    connect_to_db(app)

    db.create_all()

    print "Connected to DB."
