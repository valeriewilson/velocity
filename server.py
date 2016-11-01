from flask import Flask, request, redirect, flash, session, render_template
from flask_debugtoolbar import DebugToolbarExtension
from model import connect_to_db, db, User

app = Flask(__name__)
app.secret_key = 'ABCSECRETABC'


@app.route('/login', methods=['GET'])
def display_login_form():
    """ Display log-in form """

    return render_template('login.html')


@app.route('/login', methods=['POST'])
def log_in_user():
    """ Log in user with correct credentials """

    email = request.form.get('email')
    password = request.form.get('password')

    # Find the user with this email address
    user_entry = db.session.query(User.email, User.password).filter_by(email=email).first()
    provided_email, provided_password = user_entry

    # Check if user already exists and if password is correct; logs user in and
    #  redirects to homepage
    if user_entry and provided_password == password:
        session['useremail'] = provided_email
        return redirect('/')

    # For incorrect password, return flash message
    flash('Incorrect email or password')
    return redirect('/login')

    return render_template('/home.html')


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
        flash('User with that email address already exists')
        return redirect('/login')

    # Creates new user in users table, logs user in, redirects to homepage
    new_user = User(first_name=first_name, last_name=last_name,
                    email=email, phone=phone, password=password)
    db.session.add(new_user)
    db.session.commit()
    session['useremail'] = email

    flash('Successfully registered')
    return redirect('/home.html')


@app.route('/')
def display_home_page():
    """ Display homepage of the app """

    email = session['useremail']

    return render_template("home.html", email=email)


if __name__ == "__main__":
    app.debug = True

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(host="0.0.0.0")
