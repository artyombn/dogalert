/**
 * Инициализация формы редактирования здоровья питомца
 * @param {string} petId - ID питомца
 */
function initHealthForm(petId) {
    const form = document.getElementById('healthForm');
    const saveButton = document.getElementById('saveButton');
    const loadingOverlay = document.getElementById('loadingOverlay');

    if (!form || !petId) {
        console.error('Form or petId not found');
        return;
    }

    // Обработчик отправки формы
    form.addEventListener('submit', async (event) => {
        event.preventDefault();

        console.log('Form submitted');

        // Показываем индикатор загрузки
        showLoadingState(true, saveButton, loadingOverlay);

        try {
            const formData = new FormData(form);
            console.log('Original form data:', Object.fromEntries(formData.entries()));

            const response = await updatePetHealth(petId, formData);

            if (response.status === 'success') {
                showSuccessMessage('Данные о здоровье питомца обновлены!');

                // Перенаправляем на указанный URL через небольшую задержку
                setTimeout(() => {
                    if (response.redirect_url) {
                        window.location.href = response.redirect_url;
                    }
                }, 500);
            } else {
                showErrorMessage(response.message || 'Произошла ошибка при сохранении');
            }
        } catch (error) {
            console.error('Error updating pet health:', error);
            showErrorMessage('Произошла ошибка при отправке данных');
        } finally {
            showLoadingState(false, saveButton, loadingOverlay);
        }
    });
}

/**
 * Отправка запроса на обновление здоровья питомца
 * @param {string} petId - ID питомца
 * @param {FormData} formData - Данные формы
 * @returns {Promise<Object>} - Ответ сервера
 */
async function updatePetHealth(petId, formData) {
    // Создаем новую FormData только с заполненными полями
    const cleanFormData = new FormData();

    // Проверяем каждое поле и добавляем только если оно не пустое
    for (let [key, value] of formData.entries()) {
        if (value && value.trim() !== '') {
            cleanFormData.append(key, value);
        }
    }

    console.log('Sending data:', Object.fromEntries(cleanFormData.entries()));

    const response = await fetch(`/health/update_pet_health/${petId}`, {
        method: 'PATCH',
        body: cleanFormData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    });

    if (!response.ok) {
        const errorText = await response.text();
        console.error('Response error:', errorText);
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
}

/**
 * Показать/скрыть состояние загрузки
 * @param {boolean} isLoading - Состояние загрузки
 * @param {HTMLElement} button - Кнопка сохранения
 * @param {HTMLElement} overlay - Overlay загрузки
 */
function showLoadingState(isLoading, button, overlay) {
    if (isLoading) {
        button.disabled = true;
        button.textContent = 'Сохранение...';
        overlay.style.display = 'flex';
    } else {
        button.disabled = false;
        button.textContent = 'Сохранить изменения';
        overlay.style.display = 'none';
    }
}

/**
 * Показать сообщение об успехе
 * @param {string} message - Текст сообщения
 */
function showSuccessMessage(message) {
    showNotification(message, 'success');
}

/**
 * Показать сообщение об ошибке
 * @param {string} message - Текст сообщения
 */
function showErrorMessage(message) {
    showNotification(message, 'error');
}

/**
 * Показать уведомление
 * @param {string} message - Текст сообщения
 * @param {string} type - Тип уведомления (success, error)
 */
function showNotification(message, type = 'info') {
    // Удаляем предыдущие уведомления
    const existingNotification = document.querySelector('.notification');
    if (existingNotification) {
        existingNotification.remove();
    }

    // Создаем новое уведомление
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;

    // Добавляем уведомление в DOM
    document.body.appendChild(notification);

    // Показываем уведомление с анимацией
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);

    // Автоматически скрываем уведомление через 3 секунды
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 300);
    }, 3000);
}