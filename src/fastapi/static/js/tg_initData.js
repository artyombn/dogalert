async function checkUser() {
    const tg = window.Telegram.WebApp;
    const initData = tg.initData;


    localStorage.setItem('initData', tg.initData);

    const response = await fetch('/auth', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ initData: initData })
    });

    if (response.redirected) {
        window.location.href = response.url;
    } else {
        const data = await response.json();
        console.error(data.detail);
        window.location.href = '/error';
    }
}
