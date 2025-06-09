/**
 * Инициализация формы редактирования здоровья питомца
 * @param {string} petId - ID питомца
 */
function initHealthForm(petId) {
    const form = document.getElementById('healthForm');
    const saveButton = document.getElementById('saveButton');
    const loadingOverlay = document.getElementById('loadingOverlay');

    console.log('Initializing health form with petId:', petId);

    if (!form) {
        console.error('Form not found');
        return;
    }

    if (!petId || petId === 'null') {
        console.error('Pet ID not found or is null');
        return;
    }

    // Обработчик отправки формы
    form.addEventListener('submit', async (event) => {
        event.preventDefault();

        console.log('Form submitted for pet:', petId);

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
                }, 1000);
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
    console.log('Sending update request for pet:', petId);

    // Отправляем все данные формы, включая пустые поля
    // Сервер сам решит, что обновлять
    console.log('Sending data:', Object.fromEntries(formData.entries()));

    const response = await fetch(`/health/update_pet_health/${petId}`, {
        method: 'PATCH',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    });

    if (!response.ok) {
        const errorText = await response.text();
        console.error('Response error:', response.status, errorText);
        throw new Error(`HTTP error! status: ${response.status}, text: ${errorText}`);
    }

    const result = await response.json();
    console.log('Server response:', result);
    return result;
}

/**
 * Показать/скрыть состояние загрузки
 * @param {boolean} isLoading - Состояние загрузки
 * @param {HTMLElement} button - Кнопка сохранения
 * @param {HTMLElement} overlay - Overlay загрузки
 */
function showLoadingState(isLoading, button, overlay) {
    if (isLoading) {
        if (button) {
            button.disabled = true;
            button.textContent = 'Сохранение...';
        }
        if (overlay) {
            overlay.style.display = 'flex';
        }
    } else {
        if (button) {
            button.disabled = false;
            button.textContent = 'Сохранить изменения';
        }
        if (overlay) {
            overlay.style.display = 'none';
        }
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

    // Добавляем базовые стили, если их нет
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 5px;
        color: white;
        font-weight: bold;
        z-index: 10000;
        opacity: 0;
        transition: opacity 0.3s ease;
        max-width: 300px;
        word-wrap: break-word;
    `;

    if (type === 'success') {
        notification.style.backgroundColor = '#4CAF50';
    } else if (type === 'error') {
        notification.style.backgroundColor = '#f44336';
    } else {
        notification.style.backgroundColor = '#2196F3';
    }

    // Добавляем уведомление в DOM
    document.body.appendChild(notification);

    // Показываем уведомление с анимацией
    setTimeout(() => {
        notification.style.opacity = '1';
    }, 100);

    // Автоматически скрываем уведомление через 4 секунды
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 300);
    }, 4000);
}