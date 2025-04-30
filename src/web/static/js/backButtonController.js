function setupBackButton(show = false, backUrl = null) {

    if (show && backUrl) {
        tg.BackButton.show();
        tg.offEvent('backButtonClicked');
        tg.onEvent('backButtonClicked', () => {
            window.location.href = backUrl;
        });
    } else {
        tg.BackButton.hide();
        tg.offEvent('backButtonClicked');
    }
}
