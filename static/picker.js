(function () {
    var latInput = document.getElementById("latitude");
    var lngInput = document.getElementById("longitude");
    var map = L.map("picker").setView([20.5937, 78.9629], 5);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors"
    }).addTo(map);

    var marker = null;

    function setPoint(lat, lng, zoom) {
        latInput.value = lat.toFixed(5);
        lngInput.value = lng.toFixed(5);
        if (marker) {
            marker.setLatLng([lat, lng]);
        } else {
            marker = L.marker([lat, lng], { draggable: true }).addTo(map);
            marker.on("dragend", function () {
                var p = marker.getLatLng();
                setPoint(p.lat, p.lng);
            });
        }
        if (zoom) {
            map.setView([lat, lng], zoom);
        }
    }

    // Show the saved location (edit page, or form re-shown after an error)
    var lat0 = parseFloat(latInput.value);
    var lng0 = parseFloat(lngInput.value);
    if (!isNaN(lat0) && !isNaN(lng0)) {
        setPoint(lat0, lng0, 13);
    }

    map.on("click", function (e) {
        setPoint(e.latlng.lat, e.latlng.lng);
    });

    function onTyped() {
        var lat = parseFloat(latInput.value);
        var lng = parseFloat(lngInput.value);
        if (!isNaN(lat) && !isNaN(lng) && Math.abs(lat) <= 90 && Math.abs(lng) <= 180) {
            setPoint(lat, lng, 13);
        }
    }
    latInput.addEventListener("change", onTyped);
    lngInput.addEventListener("change", onTyped);

    document.getElementById("gps-btn").addEventListener("click", function () {
        if (!navigator.geolocation) {
            alert("Your browser does not support GPS location.");
            return;
        }
        navigator.geolocation.getCurrentPosition(
            function (pos) {
                setPoint(pos.coords.latitude, pos.coords.longitude, 15);
            },
            function () {
                alert("Could not get your location. Allow location access, or click on the map instead.");
            }
        );
    });
})();