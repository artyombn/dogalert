document.addEventListener('DOMContentLoaded', function() {
    const filterSelect = document.getElementById('filter-select');
    const loadingSpinner = document.getElementById('loading-spinner');
    const errorMessage = document.getElementById('error-message');
    const nearbyContainer = document.getElementById('nearby-reports-container');

    // Автоматически загружаем объявления при загрузке страницы
    loadReports('radius');

    filterSelect.addEventListener('change', function() {
        loadReports(this.value);
    });

    async function loadReports(filterType) {
        // Скрываем ошибки и показываем загрузку
        errorMessage.style.display = 'none';
        loadingSpinner.style.display = 'block';
        nearbyContainer.innerHTML = '';

        try {
            const response = await fetch(`/reports/nearby?filter_type=${filterType}`);

            if (!response.ok) {
                throw new Error('Ошибка сервера');
            }

            const data = await response.json();
            loadingSpinner.style.display = 'none';

            if (data.reports && data.reports.length > 0) {
                renderReports(data.reports);
            } else {
                nearbyContainer.innerHTML = `
                    <div class="report-no-ads-card">
                        <div class="report-content">
                            <h5 class="report-description">Объявления не найдены</h5>
                        </div>
                    </div>
                `;
            }

        } catch (error) {
            console.error('Ошибка:', error);
            loadingSpinner.style.display = 'none';
            errorMessage.style.display = 'block';
        }
    }

    function renderReports(reports) {
        const reportsHtml = reports.map(report => `
            <a href="/reports/${report.report_id}" class="report-card-link">
                <div class="report-card">
                    <img src="${report.report_first_photo_url || '/static/images/image.jpg'}"
                         alt="${report.report_title}" class="report-image">
                    <div class="report-content">
                        <h5 class="report-title">${report.report_title}</h5>
                        <p class="report-description">${report.report_content}</p>
                        <div class="report-meta">
                            <span class="region">Город: ${report.report_region}</span>
                            <span class="region">
                                ${report.geo_distance > 1 
                                    ? `${report.geo_distance}км от вас` 
                                    : 'менее 1 км от вас'
                                }
                            </span>
                            <span class="badge" style="font-size: 15px; margin-top: 10px; background-color: ${getBadgeColor(report.report_status)};">
                                ${getBadgeText(report.report_status)}
                            </span>
                        </div>
                    </div>
                </div>
            </a>
        `).join('');

        nearbyContainer.innerHTML = reportsHtml;
    }

    function getBadgeColor(status) {
        switch(status) {
            case 'active': return '#007bff';
            case 'found': return '#28a745';
            case 'cancelled': return '#dc3545';
            default: return '#6c757d';
        }
    }

    function getBadgeText(status) {
        switch(status) {
            case 'active': return 'Активно';
            case 'found': return 'Питомец найден';
            case 'cancelled': return 'Отменено';
            default: return 'Неизвестно';
        }
    }
});