from flask import Flask, request, redirect, flash, session, render_template, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy import desc
from model import connect_to_db, db, User, Route, Waypoint, Address
from calculation import *
from markov import *
import googlemaps
import os
import bcrypt


app = Flask(__name__)

app.secret_key = os.environ.get("FLASK_SECRET_KEY", "FLASK_KEY")

google_api_key = "AIzaSyBlY0gdpn-82bFjwWdaAPdQ_oOtJwd9Y3s"
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
    password_given = password.encode('utf-8')

    # Find user (if any) with this email address
    user_entry = db.session.query(User.email, User.password).\
        filter_by(email=email).first()

    # Check if user already exists and if password is correct
    if user_entry:
        actual_email, actual_password = user_entry
        password_stored = actual_password.encode('utf-8')

        if bcrypt.checkpw(password_given, password_stored):
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
    password = request.form.get('password')
    password = password.encode('utf-8')

    password_stored = bcrypt.hashpw(password, bcrypt.gensalt())

    # Find any user with this email address
    user_email = db.session.query(User.email).filter_by(email=email).first()

    # Check if user already exists, redirect to login page if so
    if user_email:
        flash('A user with that email address already exists')
        return redirect('/login')

    # Creates new user in users table, logs user in, redirects to homepage
    new_user = User(first_name=first_name, last_name=last_name,
                    email=email, password=password_stored)

    db.session.add(new_user)
    db.session.commit()
    session['user_email'] = email

    flash('Successfully registered')
    return redirect('/')


@app.route('/', methods=['GET'])
def display_home_page():
    """ Display homepage of the app """

    try:
        email = session['user_email']
        user_id = db.session.query(User.user_id).filter_by(email=email).first()
        addresses = db.session.query(Address.label, Address.is_default)\
            .filter_by(user_id=user_id).order_by(desc("is_default"), "label").all()

    except KeyError:
        return redirect("/login")

    # Adding in logic for eventual D3 integration
    default_address = db.session.query(Address)\
        .filter_by(user_id=user_id).order_by(desc("is_default"), "label").first()

    # Generate directional preferences
    if default_address:
        markov = MarkovCalculation(user_id, default_address.latitude, default_address.longitude)
        markov.calculate_weighted_angle(return_angle=False)

    return render_template("home.html", email=email, addresses=addresses)


@app.route('/update-stats', methods=['POST'])
def update_route_statistics():
    """ Update normalized angles for chart """

    email = session['user_email']
    user_id = db.session.query(User.user_id).filter_by(email=email).first()

    # Obtain address from home.js AJAX call
    start = request.form.get("start-location")
    address = db.session.query(Address).filter_by(user_id=user_id, label=start).first()

    # Generate directional preferences
    if address:
        markov = MarkovCalculation(address.user_id, address.latitude, address.longitude)
        markov.calculate_weighted_angle(return_angle=False)

        if markov.normalized_angles == {}:
            return jsonify({})

        return jsonify({"stats": markov.normalized_angles})
    else:
        return jsonify({})


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
def display_results():
    email = session['user_email']
    user_id = db.session.query(User.user_id).filter_by(email=email).first()

    start_address = request.form.get('start')
    route_type = request.form.get('route')

    lat_1, lon_1 = db.session.query(Address.latitude, Address.longitude).\
        filter_by(user_id=user_id).filter_by(label=start_address).first()

    if route_type == "loop":
        specified_miles = float(request.form.get('num_miles'))

        # Instantiate route_info object
        route_info = RouteMetadata(user_id, "loop", lat_1, lon_1, specified_miles)

        # Calculate waypoints for route
        midpoints, elevation_sample_size = route_info.calculate_waypoints()

    elif route_type == "midpoint":
        midpoint_address = request.form.get('midpoint')

        # Instantiate route_info object
        route_info = RouteMetadata(user_id, "midpoint", lat_1, lon_1, miles=0)

        # Geocode midpoint address
        lat_2, lon_2 = geocode_address(midpoint_address)

        # Define waypoints attribute
        route_info.waypoints = [(lat_1, lon_1), (lat_2, lon_2)]

    # Calculate total elevation changes for route
    ascent, descent = route_info.calculate_elevation()

    # Calculate total distance and time for route
    total_miles, total_minutes = route_info.calculate_distance_time()

    # Add route to routes table
    route = Route(total_ascent=ascent, total_descent=descent,
                  is_accepted=True, user_id=route_info.user_id,
                  total_miles=route_info.total_miles,
                  total_minutes=route_info.total_minutes)

    db.session.add(route)
    db.session.commit()

    route_waypoints = []

    # Format lat/lon pairs for results.html, add to waypoints table
    for waypoint in route_info.waypoints:
        lat = waypoint[0]
        lon = waypoint[1]
        route_waypoints.append([lat, lon])

        lat_lon = Waypoint(route_id=route.route_id, latitude=lat, longitude=lon)
        db.session.add(lat_lon)

    db.session.commit()

    # Calculate midpoint, format for results.html
    mid_lat, mid_lon = route_info.calculate_midpoint()

    # Format and pass results to displayResults function
    results = {"miles": route_info.total_miles, "elevation": route_info.ascent_feet,
               "minutes": route_info.total_minutes, "waypoints": route_waypoints,
               "mid_lat": route_info.mid_lat, "mid_lon": route_info.mid_lon}

    return jsonify(results)


@app.route('/routes')
def display_routes():
    """ Display routes saved by user """

    email = session['user_email']
    user_id = db.session.query(User.user_id).filter_by(email=email).first()

    routes = Route.query.filter((Route.user_id == user_id) & (Route.score.isnot(None))).\
        order_by(Route.score.desc()).limit(10).all()

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
    route.score = 0
    db.session.commit()

    return "Success"


@app.route('/add-score', methods=["POST"])
def add_score():
    """ Updated rating for accepted route """
    email = session['user_email']
    user_id = db.session.query(User.user_id).filter_by(email=email).first()
    rating = request.form.get('score')

    route = Route.query.filter_by(user_id=user_id).order_by(Route.route_id.desc()).first()

    route.score = rating
    db.session.commit()

    return "Success"


@app.route('/filter', methods=["GET"])
def filter_results():
    """ Filter results displayed on Routes page """

    email = session['user_email']
    user_id = db.session.query(User.user_id).filter_by(email=email).first()

    # Extract information from "filter" form
    route_approved = request.args.get('route-approval') or "True"

    if route_approved == "True":
        approved = True
    elif route_approved == "False":
        approved = False

    min_miles = request.args.get('min-miles') if request.args.get('min-miles') else 0
    max_miles = request.args.get('max-miles') if request.args.get('max-miles') else 1000

    min_minutes = request.args.get('min-minutes') if request.args.get('min-minutes') else 0
    max_minutes = request.args.get('max-minutes') if request.args.get('max-minutes') else 1000

    min_ascent = request.args.get('min-elevation') if request.args.get('min-elevation') else 0
    max_ascent = request.args.get('max-elevation') if request.args.get('max-elevation') else 5000

    min_score = request.args.get('min-score') if request.args.get('min-score') else 0
    max_score = request.args.get('max-score') if request.args.get('max-score') else 5

    # Extract and handle sort options
    sort_option = request.args.get('sort-options') or "Score"

    order = request.args.get('sort-method') or "desc"

    if sort_option == "Score":
        sort_column = getattr(Route.score, order)()
    elif sort_option == "Date created":
        sort_column = getattr(Route.route_id, order)()
    elif sort_option == "Time":
        sort_column = getattr(Route.total_minutes, order)()
    elif sort_option == "Elevation":
        sort_column = getattr(Route.total_ascent, order)()
    elif sort_option == "Miles":
        sort_column = getattr(Route.total_miles, order)()
    else:
        sort_column = getattr(Route.score, order)()

    # Filter routes based on the above parameters
    routes = Route.query.filter((Route.user_id == user_id)
                                & (Route.is_accepted == approved)
                                & (Route.total_miles >= min_miles)
                                & (Route.total_miles <= max_miles)
                                & (Route.total_minutes >= min_minutes)
                                & (Route.total_minutes <= max_minutes)
                                & (Route.total_ascent >= min_ascent)
                                & (Route.total_ascent <= max_ascent)
                                & (Route.score >= min_score)
                                & (Route.score <= max_score)).\
        order_by(sort_column).\
        limit(10).offset(0).all()

    results = []

    for route in routes:
        results.append({"miles": route.total_miles, "elevation": route.total_ascent,
                        "minutes": route.total_minutes, "route_id": route.route_id,
                        "score": route.score, "issue": route.issue,
                        "is_accepted": route.is_accepted})

    return jsonify(results)


@app.route('/logout')
def log_user_out():
    del session['user_email']
    flash('Logged out')
    return redirect('/login')


if __name__ == "__main__":

    connect_to_db(app, db_uri=os.environ.get("DATABASE_URL"))
    db.create_all()

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    DEBUG = "NO_DEBUG" not in os.environ
    PORT = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)
