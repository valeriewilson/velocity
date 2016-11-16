from flask import Flask, request, redirect, flash, session, render_template, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy import desc
from model import connect_to_db, db, User, Route, Waypoint, Address
from calculation import *
from time import sleep
import googlemaps
import os

app = Flask(__name__)
app.secret_key = os.environ["FLASK_KEY"]

google_api_key = os.environ["GOOGLE_API_KEY"]
gmaps = googlemaps.Client(key=google_api_key)


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


@app.route('/new-address', methods=["POST"])
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

    latitude, longitude = geocode_address(new_address)

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

        # Calculate waypoints for route
        lat_2, lon_2, lat_3, lon_3, elevation_sample_size = calculate_waypoints(lat_1, lon_1, specified_miles)

        # Set up waypoints for functions below
        waypoints = [[lat_1, lon_1], [lat_2, lon_2], [lat_3, lon_3]]

        # Calculate total elevation changes for route
        ascent, descent = calculate_elevation(waypoints, elevation_sample_size)

    elif route_type == "midpoint":
        # Geocoding address as proof of concept, will likely change with
        #  addition of GMaps Directions API

        midpoint_address = request.form.get('midpoint-address')
        lat_2, lon_2 = geocode_address(midpoint_address)

        # Calculate total elevation changes for route (sample size hard-coded for now)
        waypoints = [(lat_1, lon_1), (lat_2, lon_2)]
        ascent, descent = calculate_elevation(waypoints, 20)

    # Calculate total distance and time for route
    total_miles, total_minutes = calculate_distance_time(waypoints)

    # Add route to routes table
    route = Route(total_ascent=ascent, total_descent=descent, is_accepted=True,
                  user_id=user_id, total_miles=total_miles, total_minutes=total_minutes)

    db.session.add(route)
    db.session.commit()

    route_waypoints = []

    # Format lat/lon pairs for results.html, add to waypoints table
    for waypoint in waypoints:
        lat = waypoint[0]
        lon = waypoint[1]
        route_waypoints.append([lat, lon])

        lat_lon = Waypoint(route_id=route.route_id, latitude=lat, longitude=lon)
        db.session.add(lat_lon)

    db.session.commit()

    # Calculate midpoint, format for results.html
    mid_lat, mid_lon = calculate_midpoint(waypoints)

    return render_template("results.html", email=email, route_type=route_type,
                           mid_lat=mid_lat, mid_lon=mid_lon, waypoints=route_waypoints,
                           elevation=ascent, miles=total_miles, minutes=total_minutes,
                           api_key=google_api_key)


@app.route('/routes')
def display_routes():
    """ Display routes saved by user """

    email = session['user_email']
    user_id = db.session.query(User.user_id).filter_by(email=email).first()

    routes = Route.query.filter((Route.user_id == user_id) & (Route.score.isnot(None) & (Route.is_accepted))).all()

    return render_template("routes.html", email=email, routes=routes, api_key=google_api_key)


@app.route('/waypoints.json')
def get_waypoints():
    """ Return all waypoints for specified route_id to display on maps """

    # Retrieve waypoints given route_id
    route_id = request.args.get("route-id")
    waypoints = Waypoint.query.filter_by(route_id=route_id).all()

    route_waypoints = []
    all_lats = []
    all_lons = []

    # Extract lat/lon pairs from query results
    for waypoint in waypoints:
        route_waypoints.append({"lat": waypoint.latitude, "lng": waypoint.longitude})
        all_lats.append(waypoint.latitude)
        all_lons.append(waypoint.longitude)

    # Calculate map midpoint
    mid_lat = min(all_lats) + ((max(all_lats) - min(all_lats)) / len(all_lats))
    mid_lon = min(all_lons) + ((max(all_lons) - min(all_lons)) / len(all_lons))
    route_midpoint = {"lat": mid_lat, "lng": mid_lon}

    # Bundle information to pass to front-end
    route = {"route_id": route_id, "waypoints": route_waypoints, "midpoint": route_midpoint}

    # Throttle Google Maps API calls server-side
    sleep(1)

    return jsonify(route)


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


if __name__ == "__main__":
    app.debug = True

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(host="0.0.0.0")
