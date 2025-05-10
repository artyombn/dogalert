const spinner = document.getElementById("spinner");
const btn = document.getElementById("send-location-btn");
const clickedCoords = document.getElementById("clicked-coords");
const cityInputContainer = document.getElementById("city-input-container");
const confirmBtnContainer = document.getElementById("confirm-btn-container");
const confirmLocationBtn = document.getElementById("confirm-location-btn");
const cityInput = document.getElementById("city-input");
const geolocationIntro = document.getElementById("geolocation-intro");

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

    const saveResp = await fetch("/geo/get-location", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ lat: latitude, lon: longitude })
    });

    const saveData = await saveResp.json();

    if (saveData.status === "success" && saveData.redirect_url) {
      alert(`Город ${saveData.city} сохранён.`);
      window.location.href = saveData.redirect_url;
      return;
    } else {
      alert("Ошибка при сохранении данных: " + saveData.message);
    }

  } catch (e) {
    console.error("Ошибка определения геолокации:", e);
    alert("Не удалось определить местоположение. Выберите точку вручную.");
    showManualLocation();
  } finally {
    spinner.style.display = "none";
  }
}

function showManualLocation() {
  btn.style.display = "none";
  spinner.style.display = "none";

  if (geolocationIntro) {
    geolocationIntro.style.display = "none";
  }

  cityInputContainer.style.display = "block";
  clickedCoords.textContent = "Найдите город и выберите точку на карте.";

  enableManualMapFromCoords(DEFAULT_COORDS);
}

async function handleCitySearch() {
  const cityInput = document.getElementById("city-input").value.trim().toLowerCase();
  const searchBtn = document.getElementById("search-city-btn");

  if (!cityInput) {
    alert("Введите название города");
    return;
  }

  searchBtn.disabled = true;

  try {
    const response = await fetch(`/geo/get-city-coords?city=${encodeURIComponent(cityInput)}`);
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
  confirmBtnContainer.style.display = "block";

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
    selectedLatLng = e.latlng;
    clickedCoords.textContent = `Вы выбрали: ${selectedLatLng.lat.toFixed(5)}, ${selectedLatLng.lng.toFixed(5)}`;

    if (!isSubmitted) {
      confirmLocationBtn.disabled = false;
    }

    if (marker) {
      marker.setLatLng(selectedLatLng);
    } else {
      marker = L.marker(selectedLatLng).addTo(map);
    }
  });
}

function confirmLocation() {
  if (!selectedLatLng) {
    alert("Сначала выберите точку на карте");
    return;
  }

  if (isSubmitted) {
    alert("Вы уже подтвердили местоположение!");
    return;
  }

  const confirmSend = confirm(`Вы уверены, что это координаты вашего дома? (${selectedLatLng.lat.toFixed(5)}, ${selectedLatLng.lng.toFixed(5)})`);
  if (!confirmSend) return;

  fetch("/geo/get-location", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ lat: selectedLatLng.lat, lon: selectedLatLng.lng })
  })
    .then(response => response.json())
    .then(data => {
      if (data.status === "success" && data.redirect_url) {
        alert(`Город: ${data.city}. Координаты сохранены.`);
        confirmLocationBtn.disabled = true;
        isSubmitted = true;
        window.location.href = data.redirect_url;
      } else {
        alert("Ошибка при сохранении координат: " + data.message);
      }
    })
    .catch(err => {
      console.error(err);
      alert("Ошибка при отправке координат");
    });
}

document.getElementById("search-city-btn").addEventListener("click", handleCitySearch);

cityInput.addEventListener("keypress", function(event) {
  if (event.key === "Enter") {
    event.preventDefault();
    handleCitySearch();
  }
});