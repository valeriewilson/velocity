# Vélocity

Vélocity is a tool allowing cyclists to discover new and interesting bike routes.  This app dynamically generates and stores bike routes based on a user-specified location and either total distance or a midpoint location.

On the backend, it uses a predictive algorithm (Markov Chain) to determine the cardinal direction for the route based on the user's historical route choices, generates a loop based on this information, and displays the route with corresponding metrics using Google Maps APIs. 


![Route Creator](http://g.recordit.co/9Qdooe48PV.gif)

Saved routes can be filtered and sorted to allow the user to find a route suiting their needs.


![Saved Routes](http://g.recordit.co/nDYUNEomHV.gif)

I. Tech stack
-------------------------
* Python
* Javascript (including jQuery, AJAX)
* Jinja
* Flask
* SQLAlchemy
* Bootstrap
* Google Maps APIs (Elevation, Directions, Geocode)

II. Getting Started
-------------------------
After cloning or forking this repo, do the following steps:
  1. Install and activate a virtual environment on Vagrant
  2. pip install -r requirements.txt
  3. Create an account_keys.sh file, add a Flask key (export FLASK_KEY="key")
  4. source account_keys.sh
  5. Run the program:
    * python server.py
    * Navigate to http://localhost:5000/
