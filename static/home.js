// Chart.js integration

function displayChart(result) {
    var stats = result.stats;

    console.log(stats);

    $('#polarChart').remove();
    $('#graph-container').append('<canvas id="polarChart"><canvas>');

    if (stats) {
        $("#polarChart").removeClass("hidden");
        $("#chartHeader").removeClass("hidden");

        var ctx = $("#polarChart").get(0).getContext("2d");

        ctx.canvas.width = 300;
        ctx.canvas.height = 300;

        var data = {
            labels: ["N/NE", "NE/E", "E/SE", "SE/S", "S/SW", "SW/W", "W/NW", "NW/N"],
            datasets: [{
                backgroundColor: [
                    "#9BA5D0",
                    "#DEB85F",
                    "#B1DB68",
                    "#914B9B",
                    "#4B5A97",
                    "#FFE9B5",
                    "#10700D",
                    "#C592CC"
                ],
              data: [stats[45], stats[0], stats[315], stats[270], stats[225], stats[180], stats[135], stats[90]]
            }]
        };

        var polarChart = new Chart(ctx, {
            type: 'polarArea',
            data: data,
            options: {
                responsive: true,
                legend: {
                    display: false,
                    labels: {
                        display: false
                    }
                },
                tooltips: {
                    enabled: true,
                    mode: 'single',
                    callbacks: {
                        label: function(tooltipItems, data) {
                            return tooltipItems.yLabel + '%';
                        }
                    }
                },
                scale: {
                    display: false
                }
            }
        });
    } else {
        $("#chartHeader").addClass("hidden");
    }
}

// Load chart for default address on document load
$(document).ready(function() {
    var statInputs = {
        "start-location": $('#address-dropdown').val(),
    };

    $.post("/update-stats", statInputs, displayChart);
});


// Autocomplete address fields (Google Maps Places API integration)
var autocomplete_address, autocomplete_midpoint;

function initAutocomplete() {
    autocomplete_address = new google.maps.places.Autocomplete(
        document.getElementById('new-address-field'));
    autocomplete_midpoint = new google.maps.places.Autocomplete(
        document.getElementById('midpoint-address'));
}


// Handle user actions around address dropdown
var address_dropdown = document.getElementById("address-dropdown");

address_dropdown.onchange = function(){
    $('#new-address-information').addClass("hidden");
    $('#submit-button').removeAttr("disabled");

    var formInputs = {
        "start-location": $('#address-dropdown').val(),
    };

    $.post("/update-stats", formInputs, displayChart);

    if(address_dropdown.value=="create-new-address"){
        $('#new-address-information').removeClass();
        $('#submit-button').attr("disabled", "disabled");
    }
};


// Handle user actions around route type dropdown
var route_dropdown = document.getElementById("route-type");

route_dropdown.onchange = function() {
    $('#midpoint-field').addClass("hidden");
    $('#miles-field').addClass("hidden");
    
    if(route_dropdown.value=="loop"){
        $('#miles-field').removeClass();
    }

    else if(route_dropdown.value=="midpoint"){
        $('#midpoint-field').removeClass();
    }
};


// Handle additional of new address, corresponding changes to address dropdown
function updateAddressDropdown(result) {
    $("#new-address-information").addClass("hidden");
    $('#address-dropdown').empty();
    $('#submit-button').removeAttr("disabled");

    var addresses = result.addresses;
    
    for (var step = 0; step < addresses.length; step++) {
        $('#address-dropdown').append($('<option></option>').html(addresses[step][0]));
    }
    $('#address-dropdown').append('<option value="create-new-address">+ new address</option>');
}

function addAddress(evt) {
    evt.preventDefault();

    var formInputs = {
        "new-address-field": $('#new-address-field').val(),
        "label-field": $("#label-field").val(),
        "default-address": $('#default-address').is(':checked')
    };
    $.post("/new-address", formInputs, updateAddressDropdown);
}

$('#new-address-form').on("submit", addAddress);


// Handle accepting or rejecting of route
var yes_selected = document.getElementById("yes-option");
var no_selected = document.getElementById("no-option");

yes_selected.onchange = function(){
    $('#star-rating').removeClass();
    $('#rejected-route-form').addClass("hidden");
};

no_selected.onchange = function(){
    $('#star-rating').addClass("hidden");
    $('#rejected-route-form').removeClass();
};


// Generate results map (Google Maps Javascript API integration)
function initMap(waypoints, mid_lat, mid_lon) {
    var midpoint = {"lat": mid_lat, "lng": mid_lon};
    var start_point = {"lat": waypoints[0][0], "lng": waypoints[0][1]};

    var directionsService = new google.maps.DirectionsService();
    var directionsDisplay = new google.maps.DirectionsRenderer({suppressMarkers: true});

    var map = new google.maps.Map(document.getElementById('map'), {
        zoom: 25,
        center: midpoint,
        mapTypeControl: false,
        streetViewControl: false,
    });

    var marker = new google.maps.Marker({
      position: start_point,
      map: map
    });

    directionsDisplay.setMap(map);
    displayRoute(directionsService, directionsDisplay, waypoints);
}


// Display resulting route on map
function displayRoute(directionsService, directionsDisplay, waypoints) {
    var start_lat = waypoints[0][0];
    var start_lng = waypoints[0][1];
    var start_point = start_lat + ', ' + start_lng;

    var waypts = [];

    for (var i = 1; i < waypoints.length; i++) {
        waypts.push({location: String(waypoints[i][0]) + ', ' + String(waypoints[i][1])});
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

function displayResults(results) {
    $('#results-dropdowns').removeClass();

    var total_miles = results.miles;
    var total_elevation = results.elevation;
    var total_time = results.minutes;
    var waypoints = results.waypoints;
    var mid_lat = results.mid_lat;
    var mid_lon = results.mid_lon;

    $('#loading-image').addClass("hidden");
    $('#ride-stats-miles').text("Distance: "+ total_miles.toFixed(1) + " miles");
    $('#ride-stats-minutes').text("Time: " + Math.round(total_time) + " minutes ");
    $('#ride-stats-elevation').text("Total climb: " + Math.round(total_elevation) + " ft");
    $('#map').removeClass("hidden");

    initMap(waypoints, mid_lat, mid_lon);
}


// Trigger creation of route once user input is submitted
function createRoute(evt) {
    evt.preventDefault();

    var formInputs = {
        "start": $("#address-dropdown").val(),
        "route": $("#route-type").val(),
        "num_miles": $('#total-miles').val(),
        "midpoint": $('#midpoint-address').val()
    };
    $('#generator-options').addClass("hidden");
    $('#polarChart').addClass("hidden");
    $("#chartHeader").addClass("hidden");
    $('#loading-image').removeClass();
    $.post("/results", formInputs, displayResults);
}

$('#route-form').on("submit", createRoute);


// Handle restoring page after handling map results
function returnToSearch() {
    $('#generator-options').removeClass("hidden");
    $('#results-dropdowns').addClass("hidden");
    $('#map').addClass("hidden");

    var formInputs = {
        "start-location": $('#address-dropdown').val(),
    };

    $.post("/update-stats", formInputs, displayChart);
}


// Handle saving the route with a specified score
function saveScore(evt) {
    var score = evt.currentTarget.id.split("-")[1];

    var formInputs = {
        "score": score
    };

    $.post("/add-score", formInputs, returnToSearch);
}

$('#score-1').on("click", saveScore);
$('#score-2').on("click", saveScore);
$('#score-3').on("click", saveScore);
$('#score-4').on("click", saveScore);
$('#score-5').on("click", saveScore);

function rejectRoute(evt) {
    evt.preventDefault();

    var formInputs = {
        "issue": $("#issue").val()
    };

    $.post("/reject-route", formInputs, returnToSearch);

    var statInputs = {
        "start-location": $('#address-dropdown').val(),
    };

    $.post("/update-stats", statInputs, displayChart);
}

$('#rejected-route-form').on("submit", rejectRoute);

$('#score-1').hover(
    function() {
        $(this).removeClass("glyphicon-star-empty").addClass("glyphicon-star");
    },
    function() {
        $(this).removeClass("glyphicon-star").addClass("glyphicon-star-empty");
    }
);

$('#score-2').hover(
    function() {
        $(this).removeClass("glyphicon-star-empty").addClass("glyphicon-star");
        $('#score-1').removeClass("glyphicon-star-empty").addClass("glyphicon-star");
    },
    function() {
        $(this).removeClass("glyphicon-star").addClass("glyphicon-star-empty");
        $('#score-1').removeClass("glyphicon-star").addClass("glyphicon-star-empty");
    }
);

$('#score-3').hover(
    function() {
        $(this).removeClass("glyphicon-star-empty").addClass("glyphicon-star");
        $('#score-1').removeClass("glyphicon-star-empty").addClass("glyphicon-star");
        $('#score-2').removeClass("glyphicon-star-empty").addClass("glyphicon-star");
    },
    function() {
        $(this).removeClass("glyphicon-star").addClass("glyphicon-star-empty");
        $('#score-1').removeClass("glyphicon-star").addClass("glyphicon-star-empty");
        $('#score-2').removeClass("glyphicon-star").addClass("glyphicon-star-empty");
    }
);

$('#score-4').hover(
    function() {
        $(this).removeClass("glyphicon-star-empty").addClass("glyphicon-star");
        $('#score-1').removeClass("glyphicon-star-empty").addClass("glyphicon-star");
        $('#score-2').removeClass("glyphicon-star-empty").addClass("glyphicon-star");
        $('#score-3').removeClass("glyphicon-star-empty").addClass("glyphicon-star");
    },
    function() {
        $(this).removeClass("glyphicon-star").addClass("glyphicon-star-empty");
        $('#score-1').removeClass("glyphicon-star").addClass("glyphicon-star-empty");
        $('#score-2').removeClass("glyphicon-star").addClass("glyphicon-star-empty");
        $('#score-3').removeClass("glyphicon-star").addClass("glyphicon-star-empty");
    }
);

$('#score-5').hover(
    function() {
        $(this).removeClass("glyphicon-star-empty").addClass("glyphicon-star");
        $('#score-1').removeClass("glyphicon-star-empty").addClass("glyphicon-star");
        $('#score-2').removeClass("glyphicon-star-empty").addClass("glyphicon-star");
        $('#score-3').removeClass("glyphicon-star-empty").addClass("glyphicon-star");
        $('#score-4').removeClass("glyphicon-star-empty").addClass("glyphicon-star");
    },
    function() {
        $(this).removeClass("glyphicon-star").addClass("glyphicon-star-empty");
        $('#score-1').removeClass("glyphicon-star").addClass("glyphicon-star-empty");
        $('#score-2').removeClass("glyphicon-star").addClass("glyphicon-star-empty");
        $('#score-3').removeClass("glyphicon-star").addClass("glyphicon-star-empty");
        $('#score-4').removeClass("glyphicon-star").addClass("glyphicon-star-empty");
    }
);