window.onload = () => {
    // DOM Elements
    const deleteButton = document.querySelector('.delete-btn');
    const spinner = document.getElementById('spinner');
    
    let currentPetId = null;
    let isDeleting = false;

    // Автоматическое получение ID питомца из data-атрибута кнопки (как в addPet.js)
    function initializePetId() {
        if (deleteButton && deleteButton.getAttribute('data-pet-id')) {
            currentPetId = parseInt(deleteButton.getAttribute('data-pet-id'));
            console.log('Pet ID получен из data-pet-id:', currentPetId);
        } else {
            console.warn('Pet ID не найден в data-pet-id атрибуте кнопки удаления');
        }
    }

    function initDeletePet(petId) {
        currentPetId = petId;
        console.log('Pet ID установлен вручную:', currentPetId);
    }

    // Функция подтверждения удаления
    function confirmDelete() {
        if (!currentPetId) {
            console.error('Pet ID не установлен');
            if (window.Telegram && window.Telegram.WebApp) {
                window.Telegram.WebApp.showAlert('Ошибка: ID питомца не установлен');
            } else {
                alert('Ошибка: ID питомца не установлен');
            }
            return;
        }

        // Создаем модальное окно подтверждения
        const isConfirmed = confirm(
            'Вы уверены, что хотите удалить этого питомца?\n\n' +
            'Это действие нельзя отменить. Все данные о питомце будут безвозвратно удалены.'
        );

        if (isConfirmed) {
            deletePet(currentPetId);
        }
    }

    async function deletePet(petId) {
        if (isDeleting) return;

        isDeleting = true;
        showLoadingState();

        try {
            console.log(`Attempting to delete pet with ID: ${petId}`);

            const response = await fetch(`/pets/delete/${petId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin'
            });

            const data = await response.json();

            if (response.ok && data.status === 'success') {
                if (window.Telegram && window.Telegram.WebApp) {
                    window.Telegram.WebApp.showAlert(data.message || 'Питомец успешно удален');
                } else {
                    alert(data.message || 'Питомец успешно удален');
                }

                // Перенаправляем на профиль через 1.5 секунды
                setTimeout(() => {
                    window.location.href = '/profile';
                }, 100);

            } else {
                throw new Error(data.message || 'Произошла ошибка при удалении питомца');
            }

        } catch (error) {
            console.error('Ошибка при удалении питомца:', error);
            if (window.Telegram && window.Telegram.WebApp) {
                window.Telegram.WebApp.showAlert(error.message || 'Произошла ошибка при удалении питомца');
            } else {
                alert(error.message || 'Произошла ошибка при удалении питомца');
            }
        } finally {
            isDeleting = false;
            hideLoadingState();
        }
    }

    // Функции управления состоянием загрузки
    function showLoadingState() {
        if (deleteButton) {
            deleteButton.style.opacity = '0.6';
            deleteButton.style.pointerEvents = 'none';
            deleteButton.disabled = true;

            const originalText = deleteButton.innerHTML;
            deleteButton.setAttribute('data-original-text', originalText);
            deleteButton.innerHTML = `
                <svg class="btn-icon" style="animation: spin 1s linear infinite;" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 12a9 9 0 11-6.219-8.56"/>
                </svg>
                Удаление...
            `;
        }

        if (spinner) {
            spinner.classList.add('show');
        }
    }

    function hideLoadingState() {
        if (deleteButton) {
            deleteButton.style.opacity = '1';
            deleteButton.style.pointerEvents = 'auto';
            deleteButton.disabled = false;

            const originalText = deleteButton.getAttribute('data-original-text');
            if (originalText) {
                deleteButton.innerHTML = originalText;
                deleteButton.removeAttribute('data-original-text');
            }
        }

        if (spinner) {
            spinner.classList.remove('show');
        }
    }

    // Обработчик клика по кнопке удаления
    if (deleteButton) {
        deleteButton.addEventListener('click', function(e) {
            e.preventDefault();
            confirmDelete();
        });
    }

    // Добавляем стили анимации если их еще нет
    if (!document.querySelector('#notification-styles')) {
        const style = document.createElement('style');
        style.id = 'notification-styles';
        style.textContent = `
            @keyframes spin {
                from {
                    transform: rotate(0deg);
                }
                to {
                    transform: rotate(360deg);
                }
            }
        `;
        document.head.appendChild(style);
    }

    // Инициализируем ID питомца при загрузке страницы
    initializePetId();

    // Экспортируем функцию инициализации в глобальную область видимости
    window.initDeletePet = initDeletePet;

    console.log('Delete pet script initialized');
};