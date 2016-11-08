from flask import Flask, request, redirect, flash, session, render_template, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy import desc
from model import connect_to_db, db, User, Route, Waypoint, Address
from math import cos, sin, radians
from random import randrange, choice
import googlemaps
import requests
import os

app = Flask(__name__)
app.secret_key = os.environ["FLASK_KEY"]

google_api_key = os.environ["GOOGLE_API_KEY"]
gmaps = googlemaps.Client(key=google_api_key)

MILES_BETWEEN_LATS = 69
MILES_BETWEEN_LONS = 55


@app.route('/login', methods=['GET'])
def display_login_form():
    """ Display log-in form """

    return render_template('login.html')


@app.route('/login', methods=['POST'])
def log_in_user():
    """ Log in user with correct credentials """

    email = request.form.get('email')
    password = request.form.get('password')

    # Find user (if any) with this email address
    user_entry = db.session.query(User.email, User.password).\
        filter_by(email=email).first()

    # Check if user already exists and if password is correct; logs user in and
    #  redirects to homepage, or returns an error message
    if user_entry:
        actual_email, actual_password = user_entry
        if actual_password == password:
            session['user_email'] = actual_email
            flash('Successfully logged in')
            return redirect('/')
        else:
            flash('Incorrect password')
            return redirect('/login')
    else:
        flash('Invalid email address')
        return redirect('/login')


@app.route('/register', methods=['GET'])
def display_registration_form():
    """ Display registration form """

    return render_template('register.html')


@app.route('/register', methods=['POST'])
def register_login_user():
    """ Register user and log them in """

    # Retrieve user-input data
    first_name = request.form.get('first-name')
    last_name = request.form.get('last-name')
    email = request.form.get('email')
    phone = request.form.get('phone-number')
    password = request.form.get('password')

    # Find any user with this email address
    user_email = db.session.query(User.email).filter_by(email=email).first()

    # Check if user already exists, redirect to login page if so
    if user_email:
        flash('A user with that email address already exists')
        return redirect('/login')

    # Creates new user in users table, logs user in, redirects to homepage
    new_user = User(first_name=first_name, last_name=last_name,
                    email=email, phone=phone, password=password)
    db.session.add(new_user)
    db.session.commit()
    session['user_email'] = email

    flash('Successfully registered')
    return redirect('/')


@app.route('/', methods=['GET'])
def display_home_page():
    """ Display homepage of the app """

    email = session['user_email']
    user_id = db.session.query(User.user_id).filter_by(email=email).first()
    addresses = db.session.query(Address.label, Address.is_default)\
        .filter_by(user_id=user_id).order_by(desc("is_default"), "label").all()

    return render_template("home.html", email=email, addresses=addresses)


@app.route('/new_address', methods=["POST"])
def create_new_address():

    email = session['user_email']
    user_id = db.session.query(User.user_id).filter_by(email=email).first()

    new_address = request.form.get('new-address-field')
    new_label = request.form.get('label-field')
    default = request.form.get('default-address')

    if default == "true":
        # Set current addresses to false, new address to true
        existing_addresses = Address.query.filter_by(user_id=user_id).all()
        for address in existing_addresses:
            address.is_default = False
        db.session.commit()
        is_default = True
    else:
        is_default = False

    # Geocode address, extract latitude & longitude for route calculations
    geocoded_address = gmaps.geocode(new_address)
    latitude = geocoded_address[0]['geometry']['location']['lat']
    longitude = geocoded_address[0]['geometry']['location']['lng']

    # Add new address to addresses table
    new_address = Address(user_id=user_id, label=new_label, address_str=new_address,
                          latitude=latitude, longitude=longitude, is_default=is_default)
    db.session.add(new_address)
    db.session.commit()

    addresses = db.session.query(Address.label).filter_by(user_id=user_id).order_by(desc("is_default"), "label").all()

    # Return list of addresses in JSON format
    return jsonify({"addresses": addresses})


@app.route('/', methods=['POST'])
def return_to_home_page():
    """ Return to homepage if user accepts route """

    email = session['user_email']

    return render_template("home.html", email=email)


@app.route('/results', methods=['POST'])
def select_preference():
    """ Display results based on form inputs """

    email = session['user_email']
    user_id = db.session.query(User.user_id).filter_by(email=email).first()

    # Extract start position from user-selected starting point (removing default *)
    address_label = request.form.get('address-options').strip('*')
    lat_1, lon_1 = db.session.query(Address.latitude, Address.longitude).\
        filter_by(user_id=user_id).filter_by(label=address_label).first()

    route_type = request.form.get('route-type')

    if route_type == "loop":
        specified_miles = float(request.form.get('total-miles'))

        lat_2, lon_2, lat_3, lon_3, elevation_sample_size = calculate_waypoints(lat_1, lon_1, specified_miles)

        r = requests.get("https://maps.googleapis.com/maps/api/elevation/json?path=%s,%s|%s,%s|%s,%s|%s,%s&samples=%s&key=%s"
                         % (lat_1, lon_1, lat_2, lon_2, lat_3, lon_3, lat_1,
                            lon_1, elevation_sample_size, google_api_key))

        elevation_data = r.json()
        elevation_list = elevation_data["results"]

        ascent_meters = 0
        descent_meters = 0

        for index, elevation_point in enumerate(elevation_list):
            if index > 0:
                last_ele = elevation_point["elevation"]
                this_ele = elevation_list[index-1]["elevation"]
                if this_ele > last_ele:
                    ascent_meters += (this_ele - last_ele)
                else:
                    descent_meters += (last_ele - this_ele)

        ascent_feet = ascent_meters * 3.28
        descent_feet = descent_meters * 3.28

        # Google Maps doesn't handle round trips in the Python module, so I split the route
        directions_1 = gmaps.directions(("{}, {}").format(lat_1, lon_1),
                                        ("{}, {}").format(lat_3, lon_3),
                                        waypoints=("{}, {}").format(lat_2, lon_2),
                                        mode="bicycling")

        directions_2 = gmaps.directions(("{}, {}").format(lat_3, lon_3),
                                        ("{}, {}").format(lat_1, lon_1),
                                        mode="bicycling")

        miles_leg_1 = float(directions_1[0]["legs"][0]["distance"]["text"][:-3])
        minutes_leg_1 = float(directions_1[0]["legs"][0]["duration"]["text"][:-5])

        miles_leg_2 = float(directions_1[0]["legs"][1]["distance"]["text"][:-3])
        minutes_leg_2 = float(directions_1[0]["legs"][1]["duration"]["text"][:-5])

        miles_leg_3 = float(directions_2[0]["legs"][0]["distance"]["text"][:-3])
        minutes_leg_3 = float(directions_2[0]["legs"][0]["duration"]["text"][:-5])

        total_miles = miles_leg_1 + miles_leg_2 + miles_leg_3
        total_minutes = minutes_leg_1 + minutes_leg_2 + minutes_leg_3

        # Add route to routes table
        route = Route(total_ascent=ascent_feet, total_descent=descent_feet,
                      is_accepted=True, user_id=user_id, total_miles=total_miles,
                      total_minutes=total_minutes)
        db.session.add(route)
        db.session.commit()

        # Add points to waypoints table with new route_id
        waypoint_1 = Waypoint(route_id=route.route_id, latitude=lat_1, longitude=lon_1)
        waypoint_2 = Waypoint(route_id=route.route_id, latitude=lat_2, longitude=lon_2)
        waypoint_3 = Waypoint(route_id=route.route_id, latitude=lat_3, longitude=lon_3)
        db.session.add(waypoint_1)
        db.session.add(waypoint_2)
        db.session.add(waypoint_3)
        db.session.commit()

        return render_template("map_results.html", email=email, route_type=route_type,
                               lat_1=lat_1, lon_1=lon_1, lat_2=lat_2, lon_2=lon_2,
                               lat_3=lat_3, lon_3=lon_3, elevation=ascent_feet, miles=total_miles, minutes=total_minutes, api_key=google_api_key)

    elif route_type == "midpoint":
        # Geocoding address as proof of concept, will likely change with
        #  addition of GMaps Directions API
        midpoint_address = request.form.get('midpoint-address')
        geocoded_midpoint = gmaps.geocode(midpoint_address)

        lat_2 = geocoded_midpoint[0]['geometry']['location']['lat']
        lon_2 = geocoded_midpoint[0]['geometry']['location']['lng']

        r = requests.get("https://maps.googleapis.com/maps/api/elevation/json?path=%s,%s|%s,%s|%s,%s&samples=20&key=%s"
                         % (lat_1, lon_1, lat_2, lon_2, lat_1, lon_1, google_api_key))

        elevation_data = r.json()
        elevation_list = elevation_data["results"]

        ascent = 0
        descent = 0

        for index, elevation_point in enumerate(elevation_list):
            if index > 0:
                last_ele = elevation_point["elevation"]
                this_ele = elevation_list[index-1]["elevation"]
                if this_ele > last_ele:
                    ascent += (this_ele - last_ele)
                else:
                    descent += (last_ele - this_ele)

        route = Route(total_ascent=ascent, total_descent=descent, is_accepted=True, user_id=user_id)
        db.session.add(route)
        db.session.commit()

        waypoint_1 = Waypoint(route_id=route.route_id, latitude=lat_1, longitude=lon_1)
        waypoint_2 = Waypoint(route_id=route.route_id, latitude=lat_2, longitude=lon_2)
        db.session.add(waypoint_1)
        db.session.add(waypoint_2)
        db.session.commit()

        return render_template("map_results.html", email=email, route_type=route_type,
                               lat_1=lat_1, lon_1=lon_1, lat_2=lat_2, lon_2=lon_2, elevation=ascent_feet)


@app.route('/saved_routes')
def display_saved_routes():
    """ Display routes saved by user """

    email = session['user_email']
    user_id = db.session.query(User.user_id).filter_by(email=email).first()

    routes = Route.query.filter((Route.user_id == user_id) & (Route.score.isnot(None))).all()

    return render_template("saved_routes.html", email=email, routes=routes)


@app.route('/rejected_routes')
def display_rejected_routes():
    """ Display routes rejected by user """

    email = session['user_email']
    user_id = db.session.query(User.user_id).filter_by(email=email).first()

    routes = Route.query.filter_by(user_id=user_id).all()

    return render_template("rejected_routes.html", email=email, routes=routes)


@app.route('/reject-route', methods=["POST"])
def reject_route():
    """ Updated rejected route to is_accepted = False """
    email = session['user_email']
    user_id = db.session.query(User.user_id).filter_by(email=email).first()
    issue = request.form.get('issue')

    route = Route.query.filter_by(user_id=user_id).order_by(Route.route_id.desc()).first()

    route.is_accepted = False
    route.issue = issue
    db.session.commit()

    return redirect("/")


@app.route('/add-score', methods=["POST"])
def add_score():
    """ Updated rejected route to is_accepted = False """
    email = session['user_email']
    user_id = db.session.query(User.user_id).filter_by(email=email).first()
    rating = request.form.get('rating')

    route = Route.query.filter_by(user_id=user_id).order_by(Route.route_id.desc()).first()

    route.score = rating
    db.session.commit()

    return redirect("/")


@app.route('/logout')
def log_user_out():
    del session['user_email']
    flash('Logged out')
    return redirect('/login')


def calculate_waypoints(lat_1, lon_1, miles):
    """ For loop routes, come up with random route based on start location &
        miles specified """

    # Given the unpredictable results of Google Maps API, miles / 4 as buffer
    miles_leg = miles / 4.0
    elevation_sample_size = int(miles * 5)

    # Random direction for first leg of route
    angle = randrange(0, 360)

    # Random choice of clockwise vs. count-clockwise loop
    angle_diff = choice([-120, 120])

    # Calculate waypoints based on above information
    lat_2 = lat_1 + (sin(radians(angle))*miles_leg)/MILES_BETWEEN_LATS
    lon_2 = lon_1 + (cos(radians(angle))*miles_leg)/MILES_BETWEEN_LONS
    lat_3 = lat_2 + (sin(radians(angle+angle_diff))*miles_leg)/MILES_BETWEEN_LATS
    lon_3 = lon_2 + (cos(radians(angle+angle_diff))*miles_leg)/MILES_BETWEEN_LONS

    return lat_2, lon_2, lat_3, lon_3, elevation_sample_size


if __name__ == "__main__":
    app.debug = True

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(host="0.0.0.0")
