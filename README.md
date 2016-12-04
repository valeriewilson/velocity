# Vélocity

## Introduction

Vélocity is a tool allowing cyclists to discover new and interesting bike routes.  This app dynamically generates and stores bike routes based on a user-specified location and either total distance or a midpoint location.

## Statement of Purpose

As an avid cyclist, I love finding new bike routes but find myself sticking to a handle of favorite rides (it's hard to beat the Marin Headlands).  The idea of a bike route generator was born.  To allow for the greatest variety of routes, the generator randomizes the direction of the first leg, the number of waypoints, the length of each leg, and the clockwise or counterclockwise direction of the route.  A predictive algorithm biases the routes in favor of the directions a user prefers riding.

## User Interface

The homepage allows the user to create a route based on:
  1. A saved address
  2. A route type ("loop" generates a round-trip route, while "midpoint" allows the user to specify the halfway point)
  3. Number of miles (for "loop" routes) or midpoint address (for "midpoint" routes)

On the backend, this project uses a predictive algorithm (Markov Chain) to determine the cardinal direction for the route based on the user's historical route choices, generates a loop based on this information, and displays the route with corresponding metrics using Google Maps APIs. 


![Route Creator](http://g.recordit.co/9Qdooe48PV.gif)

Saved routes can be filtered and sorted to allow the user to find a route suiting their needs.


![Saved Routes](http://g.recordit.co/nDYUNEomHV.gif)

## Behind the Scenes

In order to generate the largest number of unique bike routes, I perform the following:
  1. Generate a loop starting in a randomized direction
  2. Following the initial leg, randomize the clockwise / counter-clockwise direction of the loop
  3. Initially, I calculated latitude/longitude pairs by forming an equilateral triangle: I took the specified miles and divided them evenly, then through some trigonometry fun derived the latitude and longitude.  Now I randomize between 3 and 4 legs on each route and with varying leg lengths.

## Tech stack

* Python
* Javascript (including jQuery, AJAX)
* Jinja
* Flask
* SQLAlchemy
* Bootstrap
* Google Maps APIs (Elevation, Directions, Geocode)

## Getting Started

After cloning or forking this repo, do the following steps:
  1. Install and activate a virtual environment on Vagrant
  2. pip install -r requirements.txt
  3. Create an account_keys.sh file, add a Flask key (export FLASK_KEY="key")
  4. source account_keys.sh
  5. Run the program:
    * python server.py
    * Navigate to http://localhost:5000/
