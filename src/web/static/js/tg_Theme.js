function setThemeParams() {
    const theme = tg.themeParams || {};
    const setVar = (varName, value) => {
        if (value) {
            document.documentElement.style.setProperty(varName, value);
        }
    };

    setVar('--tg-theme-bg-color', theme.bg_color);
    setVar('--tg-theme-text-color', theme.text_color);
    setVar('--tg-theme-hint-color', theme.hint_color);
    setVar('--tg-theme-link-color', theme.link_color);
    setVar('--tg-theme-button-color', theme.button_color);
    setVar('--tg-theme-button-text-color', theme.button_text_color);

    const bgColor = theme.bg_color || '#1a1a1a';
    const isLightTheme = isLightColor(bgColor);

    if (isLightTheme) {
        setVar('--icon-color', '#888888');
        setVar('--icon-color-active', '#ffffff');
    } else {
        setVar('--icon-color', '#cccccc');
        setVar('--icon-color-active', theme.link_color || '#51afff');
    }
}

function isLightColor(color) {
    const hex = color.replace('#', '');
    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);
    const luma = 0.299 * r + 0.587 * g + 0.114 * b;
    return luma > 128;
}
