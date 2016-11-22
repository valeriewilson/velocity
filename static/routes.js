function displayFilteredRoutes(results) {
    // Clear previous routes
    $('#all-routes').empty();

    // Extract new information to pass to retrieveWaypoints
    for (var i = 0; i < results.length; i++) {
        var route_id = results[i].route_id;
        var miles = results[i].miles;
        var minutes = results[i].minutes;
        var elevation = results[i].elevation;
        var accepted = results[i].is_accepted;
        var score = results[i].score;
        var issue = results[i].issue;

        $('#all-routes').append("<div class='map' id='map" + route_id + "' data-id='" + route_id + "'></div>");
        $('#all-routes').append("<p>" + miles.toFixed(1) + " miles | " + Math.round(minutes) + " minutes | " + Math.round(elevation) + " ft</p>");

        if (accepted) {
            $('#all-routes').append("<p>Score: " + score + "</p>");
        } else {
            $('#all-routes').append("<p>Issue: " + issue + "</p>");
        }
    }

    retrieveWaypoints();
}

function filterRoutes(evt) {
    evt.preventDefault();

    var formInputs = {
        "min-miles": $("#min-miles").val(),
        "max-miles": $("#max-miles").val(),
        "min-minutes": $("#min-minutes").val(),
        "max-minutes": $("#max-minutes").val(),
        "min-elevation": $("#min-minutes").val(),
        "max-elevation": $("#max-minutes").val(),
        "min-score": $("#min-score").val(),
        "max-score": $("#max-score").val(),
        "route-approval": $(".route-approval[name=route-approval]:checked").val(),
        "sort-options": $("#sort-dropdown :selected").text(),
        "sort-method": $(".sort-method[name=sort-method]:checked").val()
    };

    $.get("/filter", formInputs, displayFilteredRoutes);
}

$('#apply-button').on("click", filterRoutes);

$('#accepted-routes').on('change', function () {
    // Enable & remove formatting for "score" fields if "Accepted" is selected for route type
    $('.score').removeAttr("disabled").removeClass("disable");
});

$('#rejected-routes').on('change', function () {
    // Disable & gray out "score" fields if "Rejected" is selected for route type
    $('.score').attr("disabled", "disabled").addClass("disable");
});

function retrieveWaypoints() {
    // Get list of maps
    var maps = document.getElementsByClassName('map');
    
    // Get route_id associated with each map, pass to waypoints route
    for (var i = 0; i < maps.length; i++) {
        var route_num = maps[i].getAttribute("data-id");
        $.get("/waypoints.json", {"route-id": route_num}, initMap);
    }
}

function initMap(data) {

    // Extract data returned from waypoints endpoint
    var waypoints = data.waypoints;
    var midpoint = data.midpoint;
    var route_id = data.route_id;

    // Instantiate map
    var directionsService = new google.maps.DirectionsService();
    var directionsDisplay = new google.maps.DirectionsRenderer({suppressMarkers: true});
    var map_id = "map" + String(route_id);

    // Configure map, pass lat/lon pairs to displayRoute
    var map = new google.maps.Map(document.getElementById(map_id), {
        zoom: 25,
        center: midpoint,
        mapTypeControl: false,
        streetViewControl: false
    });
    
    // Place marker for start/end point
    var marker = new google.maps.Marker({
        position: waypoints[0],
        map: map
    });

    // Display map based on configuration
    directionsDisplay.setMap(map);

    // Call displayRoute function to display bike route
    displayRoute(directionsService, directionsDisplay, waypoints);
}

function displayRoute(directionsService, directionsDisplay, waypoints) {

    // Prepare start/end point
    var start_lat = waypoints[0]["lat"];
    var start_lng = waypoints[0]["lng"];
    var start_point = start_lat + ', ' + start_lng;

    // Prepare waypoints along route
    var waypts = [];

    for (var i = 1; i < waypoints.length; i++) {
        waypts.push({location: String(waypoints[i]["lat"]) + ', ' + String(waypoints[i]["lng"])});
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