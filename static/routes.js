// Display routes based on filter options
function displayFilteredRoutes(results) {
    $('#all-routes').empty();

    for (var i = 0; i < results.length; i++) {
        var route_id = results[i].route_id;
        var miles = results[i].miles;
        var minutes = results[i].minutes;
        var elevation = results[i].elevation;
        var accepted = results[i].is_accepted;
        var score = results[i].score;
        var issue = results[i].issue;

        if (accepted) {
            addendum = '';

            for (var j = 0; j < score; j++) {
                addendum += '<span class="glyphicon glyphicon-star"></span> ';
            }
        } else {
            addendum = "Issue: " + issue;
        }

        $('#all-routes').append("<div class='col-xs-12 col-sm-6 col-md-6 col-lg-offset-1 col-lg-3 saved-routes'><p>" + miles.toFixed(1) + " miles | " + Math.round(minutes) + " minutes | " + Math.round(elevation) + " ft</p><p>" + addendum + "</p><div class='map' id='map" + route_id + "' data-id='" + route_id + "'></div></div>");
    }

    retrieveWaypoints();
}

// Extract information from filter options to send to the server
function filterRoutes(evt) {
    evt.preventDefault();

    var formInputs = {
        "min-miles": $("#min-miles").val(),
        "max-miles": $("#max-miles").val(),
        "min-minutes": $("#min-minutes").val(),
        "max-minutes": $("#max-minutes").val(),
        "min-elevation": $("#min-elevation").val(),
        "max-elevation": $("#max-elevation").val(),
        "min-score": $("#min-score").val(),
        "max-score": $("#max-score").val(),
        "route-approval": $(".route-approval[name=route-approval]:checked").val(),
        "sort-options": $("#sort-dropdown :selected").text(),
        "sort-method": $(".sort-method[name=sort-method]:checked").val()
    };

    $.get("/filter", formInputs, displayFilteredRoutes);
}

// Trigger filtering of routes displayed
$('#apply-button').on("click", filterRoutes);

// Display accepted or rejected routes, depending on selection
$('#accepted-routes').on('change', function () {
    $('.score').removeAttr("disabled").removeClass("disable");
});

$('#rejected-routes').on('change', function () {
    $('.score').attr("disabled", "disabled").addClass("disable");
});

// Retrieve list of maps
function retrieveWaypoints() {

    var maps = document.getElementsByClassName('map');
    
    // Get route_id associated with each map, pass to waypoints route
    for (var i = 0; i < maps.length; i++) {
        var route_num = maps[i].getAttribute("data-id");
        $.get("/waypoints.json", {"route-id": route_num}, initMap);
    }
}

// Initialize all maps
function initMap(data) {

    var waypoints = data.waypoints;
    var midpoint = data.midpoint;
    var route_id = data.route_id;

    var directionsService = new google.maps.DirectionsService();
    var directionsDisplay = new google.maps.DirectionsRenderer({suppressMarkers: true});
    var map_id = "map" + String(route_id);

    var map = new google.maps.Map(document.getElementById(map_id), {
        zoom: 25,
        center: midpoint,
        mapTypeControl: false,
        streetViewControl: false
    });

    var marker = new google.maps.Marker({
        position: waypoints[0],
        map: map
    });

    directionsDisplay.setMap(map);

    displayRoute(directionsService, directionsDisplay, waypoints);
}

// Add directions to map
function displayRoute(directionsService, directionsDisplay, waypoints) {

    var start_lat = waypoints[0]["lat"];
    var start_lng = waypoints[0]["lng"];
    var start_point = start_lat + ', ' + start_lng;

    var waypts = [];

    for (var i = 1; i < waypoints.length; i++) {
        waypts.push({location: String(waypoints[i]["lat"]) + ', ' + String(waypoints[i]["lng"])});
    }

    directionsService.route({
        origin: start_point,
        destination: start_point,
        waypoints: waypts,
        travelMode: 'BICYCLING'
    },

    function(response, status) {
        if (status === 'OK') {
            directionsDisplay.setDirections(response);
        } else {
            console.log('Directions request failed due to ' + status);
        }
    });
}