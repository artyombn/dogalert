function setActiveFooterItem() {
    const currentPath = window.location.pathname;

    document.querySelectorAll('.footer-item').forEach(item => {
        item.classList.remove('active');
    });

    if (currentPath === '/profile' || currentPath === '/') {
        document.getElementById('profile-link').classList.add('active');
    } else if (currentPath === '/reports') {
        document.getElementById('reports-link').classList.add('active');
    } else if (currentPath === '/health') {
        document.getElementById('health-link').classList.add('active');
    } else if (currentPath === '/reminders') {
        document.getElementById('reminders-link').classList.add('active');
    }
}
