# Vélocity

Dynamically creates round-trip bike routes based on a user-specified start location, total distance, and past user preferences.

I. Tech stack
-------------------------
* Python
* Javascript (including jQuery, AJAX)
* Flask
* Bootstrap
* Google Maps APIs (Elevation, Directions, Geocode)

II. Getting Started
-------------------------
After cloning or forking this repo, do the following steps:
  1. Install and activate a virtual environment on Vagrant
  2. pip install -r requirements.txt
  3. Create an account_keys.sh file, add your Google Maps API key (export GOOGLE_API_KEY="key") and Flask key (export FLASK_KEY="key")
  4. source account_keys.sh
  5. Run the program:
    * python server.py
    * Navigate to http://localhost:5000/
