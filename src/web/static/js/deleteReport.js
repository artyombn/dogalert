function initDeleteReport(reportId) {
    // Найти кнопку удаления по data-report-id
    const deleteBtn = document.querySelector(`.delete-btn[data-report-id="${reportId}"]`);

    if (!deleteBtn) {
        console.error('Кнопка удаления отчета не найдена');
        return;
    }

    deleteBtn.addEventListener('click', async function(e) {
        e.preventDefault();

        // Показать подтверждение
        const confirmed = confirm('Вы уверены, что хотите удалить это объявление? Это действие нельзя отменить.');

        if (!confirmed) {
            return;
        }

        try {
            // Отключить кнопку во время запроса
            deleteBtn.style.pointerEvents = 'none';
            deleteBtn.style.opacity = '0.6';

            // Показать индикатор загрузки
            const originalText = deleteBtn.innerHTML;
            deleteBtn.innerHTML = `
                <svg class="btn-icon" style="animation: spin 1s linear infinite;" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 12a9 9 0 11-6.219-8.56"/>
                </svg>
                Удаление...
            `;

            const response = await fetch(`/reports/delete/${reportId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.status === 'success') {
                // Показать сообщение об успехе
                alert('Объявление успешно удалено!');

                // Перенаправить на список отчетов
                window.location.href = '/reports';
            } else {
                throw new Error(data.message || 'Ошибка при удалении объявления');
            }

        } catch (error) {
            console.error('Ошибка при удалении объявления:', error);
            alert('Произошла ошибка при удалении объявления: ' + error.message);

            // Восстановить кнопку
            deleteBtn.innerHTML = originalText;
            deleteBtn.style.pointerEvents = 'auto';
            deleteBtn.style.opacity = '1';
        }
    });

    // Добавить CSS для анимации загрузки
    const style = document.createElement('style');
    style.textContent = `
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(style);
}