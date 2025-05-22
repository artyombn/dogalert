async function checkUserPooling(reportId) {
    const tg = window.Telegram.WebApp;
    const initData = tg.initData;


    if (!initData) {
        console.error("No initData from Telegram WebApp");
        window.location.href = "/no_telegram_login";
        return;
    }

    localStorage.setItem('initData', initData);

    const response = await fetch('/reports/auth', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            initData: initData,
            reportId: reportId
        })
    });

    const data = await response.json();
        if (data.redirect_url) {
            console.log('Redirecting to:', data.redirect_url);
            window.location.href = data.redirect_url;
        } else {
            console.error('Error:', data.detail || 'No redirect URL provided');
            window.location.href = '/error';
        }
}
