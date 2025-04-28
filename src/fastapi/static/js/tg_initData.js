async function checkUser() {
    const tg = window.Telegram.WebApp;
    const initData = tg.initData;

    const response = await fetch('/check_user', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ initData: initData })
    });

    const data = await response.json();

    if (data.exists) {
        window.location.href = `/profile?initData=${encodeURIComponent(initData)}`;
    } else {
        window.location.href = `/agreement?initData=${encodeURIComponent(initData)}`;
    }
}
