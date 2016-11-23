var dropdown = document.getElementById("address-dropdown");

dropdown.onchange = function(){
   // Hide "new address" fields by default
   $('#new-address-information').addClass("hidden");

   // Display fields when "+ new address" is selected in "Start address" dropdown
   if(dropdown.value=="create-new-address"){
     $('#new-address-information').removeClass();
   }
};

var route_dropdown = document.getElementById("route-type");

route_dropdown.onchange = function(){
    // Hide midpoint & miles fields by default
    $('#midpoint-field').addClass("hidden");
    $('#miles-field').addClass("hidden");
    
    // Display miles field when "Loop" route is selected
    if(route_dropdown.value=="loop"){
        $('#miles-field').removeClass();
    }

    // Display midpoint field when "To midpoint and back" route is selected
    else if(route_dropdown.value=="midpoint"){
        $('#midpoint-field').removeClass();
    }
};

function updateAddressDropdown(result) {
    // Hide "new address" fields when triggered
    $("#new-address-information").addClass("hidden");
    
    // Remove current addresses from "Start address" dropdown
    $('#address-dropdown').empty();

    var addresses = result.addresses;
    
    // Add all addresses (including new) to "Start address" dropdown
    for (var step = 0; step < addresses.length; step++) {
        $('#address-dropdown').append($('<option></option>').html(addresses[step][0]));
    }
    $('#address-dropdown').append('<option value="create-new-address">+ new address</option>');
}

function addAddress(evt) {
    evt.preventDefault();

    // Passes new address information to server.py route for processing
    var formInputs = {
        "new-address-field": $("#new-address-field").val(),
        "label-field": $("#label-field").val(),
        "default-address": $('#default-address').is(':checked')
    };
    $.post("/new-address", formInputs, updateAddressDropdown);
}

$('#new-address-form').on("submit", addAddress);

var yes_selected = document.getElementById("yes-option");
yes_selected.onchange = function(){
    $('#accepted-route-form').removeClass();
    $('#rejected-route-form').addClass("hidden");
};

var no_selected = document.getElementById("no-option");
no_selected.onchange = function(){
    $('#accepted-route-form').addClass("hidden");
    $('#rejected-route-form').removeClass();
};

function initMap(waypoints, mid_lat, mid_lon) {
    var midpoint = {"lat": mid_lat, "lng": mid_lon};
    var start_point = {"lat": waypoints[0][0], "lng": waypoints[0][1]};

    // Instantiate map
    var directionsService = new google.maps.DirectionsService();
    var directionsDisplay = new google.maps.DirectionsRenderer({suppressMarkers: true});

    // Configure map, pass lat/lon pairs to displayRoute
    var map = new google.maps.Map(document.getElementById('map'), {
        zoom: 25,
        center: midpoint,
        mapTypeControl: false,
        streetViewControl: false,
    });

    // Place marker for start/end point
    var marker = new google.maps.Marker({
      position: start_point,
      map: map
    });

    // Display map based on configuration
    directionsDisplay.setMap(map);

    // Call displayRoute function to display bike route
    displayRoute(directionsService, directionsDisplay, waypoints);
}

function displayRoute(directionsService, directionsDisplay, waypoints) {

    // Prepare start/end point
    var start_lat = waypoints[0][0];
    var start_lng = waypoints[0][1];
    var start_point = start_lat + ', ' + start_lng;

    // Prepare waypoints along route
    var waypts = [];

    for (var i = 1; i < waypoints.length; i++) {
        waypts.push({location: String(waypoints[i][0]) + ', ' + String(waypoints[i][1])});
    }

    // Create route, starting & ending at origin, passing through waypoints
    directionsService.route({
        origin: start_point,
        destination: start_point,
        waypoints: waypts,
        travelMode: 'BICYCLING'
    },

    // Error handling
    function(response, status) {
        if (status === 'OK') {
            directionsDisplay.setDirections(response);
        } else {
            console.log('Directions request failed due to ' + status);
        }
    });
}

function displayResults(results) {
    $('#results-dropdowns').removeClass();

    var total_miles = results.miles;
    var total_elevation = results.elevation;
    var total_time = results.minutes;
    var waypoints = results.waypoints;
    var mid_lat = results.mid_lat;
    var mid_lon = results.mid_lon;

    $('#loading-image').addClass("hidden");
    $('#ride-stats').text("Miles: "+ total_miles.toFixed(1) + " miles | Time: " + Math.round(total_time) + " minutes | Total climb: " + Math.round(total_elevation) + " ft");
    $('#map').removeClass("hidden");

    initMap(waypoints, mid_lat, mid_lon);
}

function createRoute(evt) {
    evt.preventDefault();

    var formInputs = {
        "start": $("#address-dropdown").val(),
        "route": $("#route-type").val(),
        "num_miles": $('#total-miles').val(),
        "midpoint": $('#midpoint-address').val()
    };
    $('#generator-options').addClass("hidden");
    $('#loading-image').removeClass();
    $.post("/results", formInputs, displayResults);
}

$('#route-form').on("submit", createRoute);

function returnToSearch() {

    // After saving route, restore Home page to original format
    $('#generator-options').removeClass("hidden");
    $('#results-dropdowns').addClass("hidden");
    $('#map').addClass("hidden");
}

function saveScore(evt) {
    evt.preventDefault();

    var formInputs = {
        "score": $("#rating").val()
    };

    // Pass score to /add-score route
    $.post("/add-score", formInputs, returnToSearch);
}

$('#accepted-route-form').on("submit", saveScore);

function rejectRoute(evt) {
    evt.preventDefault();

    var formInputs = {
        "issue": $("#issue").val()
    };

    // Pass issue to /reject-route route
    $.post("/reject-route", formInputs, returnToSearch);
}

$('#rejected-route-form').on("submit", rejectRoute);
