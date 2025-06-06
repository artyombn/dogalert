function saveCurrentPathAsPrevious() {
    const currentPath = window.location.pathname;

    let pathStack = JSON.parse(sessionStorage.getItem('path_stack') || '[]');

    if (pathStack[pathStack.length - 1] !== currentPath) {
        pathStack.push(currentPath);

        if (pathStack.length > 10) {
            pathStack = pathStack.slice(-10);
        }

        sessionStorage.setItem('path_stack', JSON.stringify(pathStack));
    }
    console.log('Текущий путь:', window.location.pathname);
    console.log('Стек путей:', JSON.parse(sessionStorage.getItem('path_stack') || '[]'));
    console.log('Предыдущий путь:', getPreviousPath());
}

function removeCurrentPathFromStack() {
    const currentPath = window.location.pathname;
    let pathStack = JSON.parse(sessionStorage.getItem('path_stack') || '[]');

    const lastIndex = pathStack.lastIndexOf(currentPath);
    if (lastIndex !== -1) {
        pathStack.splice(lastIndex, 1);
        sessionStorage.setItem('path_stack', JSON.stringify(pathStack));
    }
}

function clearPathStack() {
    sessionStorage.removeItem('path_stack');
}

function isMainPage(path) {
    const mainPages = ['/profile', '/dashboard', '/'];
    return mainPages.includes(path);
}

function getPreviousPath() {
    const pathStack = JSON.parse(sessionStorage.getItem('path_stack') || '[]');
    const currentPath = window.location.pathname;

    if (isMainPage(currentPath)) {
        return null;
    }

    const currentIndex = pathStack.lastIndexOf(currentPath);
    if (currentIndex > 0) {
        return pathStack[currentIndex - 1];
    }

    if (pathStack.length > 0) {
        return pathStack[pathStack.length - 1];
    }

    return null;
}

function setupBackButton(show = false, backUrl = null) {
    tg.offEvent('backButtonClicked');

    if (show) {
        const previousPath = getPreviousPath();

        if (!backUrl && !previousPath) {
            tg.BackButton.hide();
            return;
        }

        tg.BackButton.show();
        tg.onEvent('backButtonClicked', () => {
            let targetUrl;

            if (backUrl) {
                targetUrl = backUrl;
            } else {
                targetUrl = previousPath || '/profile';
            }

            removeCurrentPathFromStack();

            if (isMainPage(targetUrl)) {
                clearPathStack();
            }

            console.log('Переходим на:', targetUrl);
            console.log('Стек после удаления:', JSON.parse(sessionStorage.getItem('path_stack') || '[]'));

            window.location.href = targetUrl;
        });
    } else {
        tg.BackButton.hide();
    }
}

function setupMainPage() {
    clearPathStack();
    saveCurrentPathAsPrevious();
    tg.BackButton.hide();
    tg.offEvent('backButtonClicked');
}
