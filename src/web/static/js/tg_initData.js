async function checkUser() {
    const tg = window.Telegram.WebApp;
    const initData = tg.initData;


    localStorage.setItem('initData', tg.initData);

    const response = await fetch('/auth', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ initData: initData })
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
