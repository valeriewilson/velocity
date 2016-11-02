from flask import Flask, request, redirect, flash, session, render_template
from flask_debugtoolbar import DebugToolbarExtension
from model import connect_to_db, db, User
from math import cos, sin, radians
import googlemaps
import os

app = Flask(__name__)
app.secret_key = 'ABCSECRETABC'

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
    user_entry = db.session.query(User.email, User.password).filter_by(email=email).first()

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
        print session
        flash('Invalid email address')
        return redirect('/login')


@app.route('/register', methods=['GET'])
def display_registration_form():
    """ Display registration form """

    return render_template('register.html')


@app.route('/register', methods=['POST'])
def register_login_user():
    """ Register user and log them in """

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

    return render_template("home.html", email=email)


@app.route('/', methods=['POST'])
def return_to_home_page():
    """ Return to homepage (for yes/no) """

    email = session['user_email']

    return render_template("home.html", email=email)


@app.route('/results', methods=['POST'])
def select_preference():
    """ Display results based on form inputs """

    email = session['user_email']
    address = request.form.get('start-address')
    route_type = request.form.get('route-type')
    total_miles = float(request.form.get('total-miles'))

    # Geocode start address, extract latitude & longitude for route calculations
    geocoded_start = gmaps.geocode(address)
    lat_1 = geocoded_start[0]['geometry']['location']['lat']
    lon_1 = geocoded_start[0]['geometry']['location']['lng']

    if route_type == "loop":
        # Given the unpredictable results of Google Maps API, miles / 4 as buffer
        miles_leg = total_miles / 4
        angle = 0

        lat_2 = lat_1 + (sin(radians(angle))*miles_leg)/MILES_BETWEEN_LATS
        lon_2 = lon_1 + (cos(radians(angle))*miles_leg)/MILES_BETWEEN_LONS

        lat_3 = lat_2 + (sin(radians(angle+120))*miles_leg)/MILES_BETWEEN_LATS
        lon_3 = lon_2 + (cos(radians(angle+120))*miles_leg)/MILES_BETWEEN_LONS

        return render_template("map_results.html", email=email, address=address,
                               lat_1=lat_1, lon_1=lon_1, lat_2=lat_2, lon_2=lon_2,
                               lat_3=lat_3, lon_3=lon_3, route_type=route_type)

    elif route_type == "midpoint":

        return render_template("map_results.html", email=email, address=address,
                               route_type=route_type)


@app.route('/saved_routes')
def display_saved_routes():
    """ Display routes saved by user """

    email = session['user_email']

    return render_template("saved_routes.html", email=email)


@app.route('/rejected_routes')
def display_rejected_routes():
    """ Display routes rejected by user """

    email = session['user_email']

    return render_template("rejected_routes.html", email=email)


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
