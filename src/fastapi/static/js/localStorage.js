function setlocalStorage(){
    const initData = localStorage.getItem('initData');
    if (initData) {
        const acceptAgreement = document.getElementById('accept-agreement');
        if (acceptAgreement) {
            acceptAgreement.href = `/registration?initData=${encodeURIComponent(initData)}`;
        }

        const goBack = document.getElementById('go-back');
        if (goBack) {
            goBack.href = `/?initData=${encodeURIComponent(initData)}`;
        }
    } else {
        console.warn('initData not found in localStorage.');
    }
}