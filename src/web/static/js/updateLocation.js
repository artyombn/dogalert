const spinner = document.getElementById("spinner");
const btn = document.getElementById("send-location-btn");
const openMapBtn = document.getElementById("open-map-btn");
const clickedCoords = document.getElementById("clicked-coords");
const cityInputContainer = document.getElementById("city-input-container");
const confirmBtnContainer = document.getElementById("confirm-btn-container");
const confirmLocationBtn = document.getElementById("confirm-location-btn");
const cityInput = document.getElementById("city-input");
const geolocationIntro = document.getElementById("geolocation-intro");
const manualLocationInfo = document.getElementById("manual-location-info");

let selectedLatLng = null;
let map;
let marker;
let isSubmitted = false;

const DEFAULT_COORDS = [55.7558, 37.6173]; // Moscow

async function requestLocation() {
  if (btn.disabled) return;

  if (!navigator.geolocation) {
    alert("Геолокация не поддерживается вашим браузером");
    showManualLocation();
    return;
  }

  try {
    btn.disabled = true;
    openMapBtn.disabled = true;
    spinner.style.display = "block";

    const position = await new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
      });
    });

    const latitude = position.coords.latitude;
    const longitude = position.coords.longitude;
    
    // Set the selected coordinates after getting them from the browser
    selectedLatLng = { lat: latitude, lon: longitude };

    const resolveResp = await fetch(`/geo/get-city-name?lat=${latitude}&lon=${longitude}`);
    const resolveData = await resolveResp.json();

    if (resolveData.status !== "success") {
      alert(resolveData.message || "Ошибка при определении города");
      showManualLocation();
      return;
    }

    const confirm = window.confirm(
      `Ваш город: ${resolveData.city}.\nКоординаты: ${latitude.toFixed(5)}, ${longitude.toFixed(5)}.\nПодтвердить?`
    );

    if (!confirm) {
      showManualLocation();
      return;
    }

    // Show confirm button after location is confirmed
    showConfirmButton();

  } catch (e) {
    console.error("Ошибка определения геолокации:", e);
    alert("Не удалось определить местоположение. Выберите точку вручную.");
    showManualLocation();
  } finally {
    spinner.style.display = "none";
    btn.disabled = false;
    openMapBtn.disabled = false;
  }
}

function showManualLocation() {
  btn.disabled = true;
  openMapBtn.disabled = true;
  spinner.style.display = "none";
  manualLocationInfo.style.display = "none";

  cityInputContainer.style.display = "block";
  clickedCoords.textContent = "Найдите город и выберите точку на карте.";

  enableManualMapFromCoords(DEFAULT_COORDS);
}

function showConfirmButton() {
  confirmBtnContainer.style.display = "block";
  confirmLocationBtn.disabled = false;
}

async function handleCitySearch() {
  const cityName = document.getElementById("city-input").value.trim();
  const searchBtn = document.getElementById("search-city-btn");

  if (!cityName) {
    alert("Введите название города");
    return;
  }

  searchBtn.disabled = true;

  try {
    const response = await fetch(`/geo/get-city-coords?city=${encodeURIComponent(cityName)}`);
    const data = await response.json();

    if (data.status === "success") {
      enableManualMapFromCoords([data.lat, data.lon]);
    } else {
      alert("Город не найден. Проверьте название");
    }
  } catch (err) {
    console.error("Ошибка при поиске города:", err);
    alert("Ошибка при поиске координат");
  } finally {
    searchBtn.disabled = false;
  }
}

function enableManualMapFromCoords(cityCoords) {
  const mapContainer = document.getElementById("map");
  mapContainer.style.display = "block";

  if (map) {
    map.invalidateSize();
    map.setView(cityCoords, 12);
    return;
  }

  map = L.map("map").setView(cityCoords, 12);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);

  map.on("click", function (e) {
    selectedLatLng = {
      lat: e.latlng.lat,
      lon: e.latlng.lng
    };
    clickedCoords.textContent = `Вы выбрали: ${selectedLatLng.lat.toFixed(5)}, ${selectedLatLng.lon.toFixed(5)}`;

    if (!isSubmitted) {
      confirmLocationBtn.disabled = false;
    }

    if (marker) {
      marker.setLatLng(selectedLatLng);
    } else {
      marker = L.marker(selectedLatLng).addTo(map);
    }
    
    showConfirmButton();
  });
}

async function confirmLocation() {
  if (!selectedLatLng) {
    alert("Сначала выберите точку на карте");
    return;
  }

  if (isSubmitted) {
    alert("Вы уже подтвердили местоположение!");
    return;
  }
  
  const confirmSend = confirm(`Вы уверены, что хотите обновить местоположение? (${selectedLatLng.lat.toFixed(5)}, ${selectedLatLng.lon.toFixed(5)})`);
  if (!confirmSend) return;
  
  confirmLocationBtn.disabled = true;
  
  try {
    const response = await fetch(`/users/update/geo`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        lat: selectedLatLng.lat,
        lon: selectedLatLng.lon
      })
    });

    const data = await response.json();

    if (data.status === "success") {
      alert(data.message || "Геолокация успешно обновлена");
      isSubmitted = true;

      window.location.reload();
    } else {
      alert("Ошибка при обновлении геолокации: " + (data.message || "Неизвестная ошибка"));
      confirmLocationBtn.disabled = false;
    }
  } catch (err) {
    console.error("Ошибка при обновлении геолокации:", err);
    alert("Ошибка при отправке данных на сервер");
    confirmLocationBtn.disabled = false;
  }
}

document.getElementById("search-city-btn").addEventListener("click", handleCitySearch);

cityInput.addEventListener("keypress", function(event) {
  if (event.key === "Enter") {
    event.preventDefault();
    handleCitySearch();
  }
});
