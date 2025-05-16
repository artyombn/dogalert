const cityNotif = document.getElementById('cityNotif');
const radiusNotif = document.getElementById('radiusNotif');
const areaNotif = document.getElementById('areaNotif');
const radiusRange = document.getElementById('radiusRange');
const distanceValue = document.querySelector('.distance-value');
const saveButton = document.querySelector('.settings-actions .btn-primary');
const distanceSelector = document.querySelector('.distance-selector');

function initializeInterface() {
  if (radiusNotif.checked) {
    distanceSelector.style.display = 'block';
  } else {
    distanceSelector.style.display = 'none';
  }

  distanceValue.textContent = radiusRange.value + ' км';

  initialRadiusValue = radiusRange.value;
}

let initialRadiusValue;

function activateOnlyOne(activeCheckbox) {
  const checkboxes = [cityNotif, radiusNotif, areaNotif];

  checkboxes.forEach(checkbox => {
    if (checkbox !== activeCheckbox) {
      checkbox.checked = false;
    } else {
      checkbox.checked = true;
    }
  });

  distanceSelector.style.display = (activeCheckbox === radiusNotif) ? 'block' : 'none';
}

cityNotif.addEventListener('change', function() {
  if (this.checked) {
    activateOnlyOne(this);
  }
});

radiusNotif.addEventListener('change', function() {
  if (this.checked) {
    activateOnlyOne(this);
    radiusWasChanged = true;
  }
});

areaNotif.addEventListener('change', function() {
  if (this.checked) {
    activateOnlyOne(this);
  }
});

radiusRange.addEventListener('input', function() {
  distanceValue.textContent = this.value + ' км';
  if (!radiusNotif.checked) {
    activateOnlyOne(radiusNotif);
  }
  radiusWasChanged = true;
});

radiusRange.addEventListener('change', function() {
  radiusWasChanged = true;
});

saveButton.addEventListener('click', async function() {
  let filterType;
  let radius = null;

  if (cityNotif.checked) {
    filterType = "region";
  } else if (radiusNotif.checked) {
    filterType = "radius";
    radius = parseInt(radiusRange.value, 10) * 1000; // Конвертируем км в метры
  } else if (areaNotif.checked) {
    filterType = "polygon";
  } else {
    filterType = "region";
  }

  try {
    let url = `/users/update/geo/filter_type?filter_type=${filterType}`;
    if (filterType === "radius") {
      url += `&radius=${radius}`;
    }

    const response = await fetch(url, {
      method: 'PATCH',
    });

    const data = await response.json();

    if (data.status === "success") {
      alert("Настройки уведомлений успешно сохранены!");
      if (filterType === "radius") {
        initialRadiusValue = radiusRange.value;
        radiusWasChanged = false;
      }
    } else {
      alert("Ошибка при сохранении настроек: " + (data.message || "Неизвестная ошибка"));
    }
  } catch (error) {
    console.error("Ошибка при отправке запроса:", error);
    alert("Произошла ошибка при сохранении настроек. Пожалуйста, попробуйте позже.");
  }
});

document.addEventListener('DOMContentLoaded', initializeInterface);