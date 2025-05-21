window.onload = () => {
    // DOM Elements
    const fileInput = document.getElementById('fileInput');
    const imagePreviewsContainer = document.getElementById('image-previews');
    const photoCountElement = document.getElementById('photo-count');
    const submitButton = document.getElementById('submit-btn');
    const spinner = document.getElementById('spinner');
    const dropdownButton = document.getElementById('reportDropdown');
    const dropdownItems = document.querySelectorAll('.dropdown-menu .dropdown-item');
    const viewportHeight = window.visualViewport ? window.visualViewport.height : window.innerHeight;

    const MAX_PHOTOS = 5;
    let uploadedFiles = [];
    let optimizedFiles = []; // Добавляем массив для оптимизированных изображений
    let isUploading = false;
    let isFormTouched = false;
    let selectedPetId = null;

    const inputs = {
        reportTitle: document.getElementById("reportTitle"),
        reportContent: document.getElementById("reportContent"),
    };

    const touchedFields = {
        reportTitle: false,
        reportContent: false,
    };

    // Правила валидации для каждого поля
    const validationRules = {
        reportTitle: { required: true, minLength: 2, maxLength: 50 },
        reportContent: { required: true, minLength: 10, maxLength: 500 },
    };

    // Setup dropdown functionality
    dropdownItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const petId = this.getAttribute('data-pet-id');
            const petName = this.textContent.trim();
            selectedPetId = petId;

            // Update dropdown button text
            dropdownButton.textContent = petName;

            // Mark form as touched
            isFormTouched = true;
            updateSubmitButton();
        });
    });

    // Функция оптимизации изображения
    async function optimizeImage(file) {
        return new Promise((resolve) => {
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onloadend = function() {
                const img = new Image();
                img.src = reader.result;
                img.onload = function() {
                    // Определяем целевой размер (макс. 1200px по длинной стороне)
                    const MAX_SIZE = 1200;
                    let width = img.width;
                    let height = img.height;
                    let quality = 0.7; // Уровень качества JPEG

                    // Уменьшаем размер если изображение слишком большое
                    if (width > height && width > MAX_SIZE) {
                        height = Math.round((height * MAX_SIZE) / width);
                        width = MAX_SIZE;
                    } else if (height > MAX_SIZE) {
                        width = Math.round((width * MAX_SIZE) / height);
                        height = MAX_SIZE;
                    }

                    // Создаем canvas для изменения размера
                    const canvas = document.createElement('canvas');
                    canvas.width = width;
                    canvas.height = height;

                    // Рисуем изображение на canvas
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(img, 0, 0, width, height);

                    // Получаем оптимизированное изображение в формате Blob
                    canvas.toBlob(
                        (blob) => {
                            // Создаем новый файл из blob
                            const optimizedFile = new File(
                                [blob],
                                file.name,
                                { type: 'image/jpeg', lastModified: Date.now() }
                            );
                            resolve(optimizedFile);
                        },
                        'image/jpeg',
                        quality
                    );
                };
            };
        });
    }

    // Функция валидации поля
    function validateField(input, errorElementId, rules, touched, forceValidate = false) {
        const errorElement = document.getElementById(errorElementId);
        const value = input.value.trim();
        let error = '';

        // Проверяем поле, если оно затронуто или требуется принудительная валидация (при отправке)
        if (touched || forceValidate) {
            if (value === '' && rules.required) {
                error = 'Это поле обязательно';
            } else if (value !== '') {
                if (rules.minLength && value.length < rules.minLength) {
                    error = `Минимум ${rules.minLength} символа(ов)`;
                } else if (rules.maxLength && value.length > rules.maxLength) {
                    error = `Максимум ${rules.maxLength} символа(ов)`;
                }
            }

            // Update UI based on validation
            if (error) {
                input.classList.add('invalid');
                errorElement.textContent = error;
                errorElement.classList.add('show');
            } else {
                input.classList.remove('invalid');
                errorElement.textContent = '';
                errorElement.classList.remove('show');
            }
        }

        return error === '';
    }

    // Debounce
    function debounce(func, wait) {
        let timeout;
        return function (...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    // Валидация всех полей формы
    function validateForm(forceValidate = false) {
        let isValid = true;
        Object.keys(inputs).forEach(key => {
            const input = inputs[key];
            const rules = validationRules[key];
            const errorElementId = `error-${key}`;
            const touched = touchedFields[key];

            // Проверяем поле, если оно затронуто или требуется принудительная валидация
            const fieldValid = validateField(input, errorElementId, rules, touched, forceValidate);

            // Поле недействительно, если оно пустое и обязательное
            if (rules.required && input.value.trim() === '') {
                isValid = false;
            } else if ((touched || forceValidate) && !fieldValid) {
                isValid = false;
            }
        });
        return isValid;
    }

    // Улучшенная функция прокрутки к активному полю при фокусировке
    function scrollToInput(input) {
        // Откладываем выполнение, чтобы дать клавиатуре время появиться
        setTimeout(() => {

            const viewportHeight = window.visualViewport ? window.visualViewport.height : window.innerHeight;

            // Получаем позицию элемента
            const rect = input.getBoundingClientRect();

            // Получаем текущую позицию прокрутки
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

            // Позиция элемента относительно всего документа
            const elementTop = rect.top + scrollTop;

            // Оценка высоты клавиатуры (приблизительно 40% высоты экрана на мобильных устройствах)
            const estimatedKeyboardHeight = isMobile() ? viewportHeight * 0.4 : 0;

            // Определяем доступную высоту для контента с учетом клавиатуры
            const availableHeight = viewportHeight - estimatedKeyboardHeight;

            // Вычисляем, сколько нужно прокрутить, чтобы элемент был виден
            // Добавляем отступ сверху для комфортного просмотра (например, 100px)
            const offsetTop = window.visualViewport ? window.visualViewport.offsetTop : 0;
            const scrollTo = elementTop - 100 - offsetTop;


            // Если элемент находится слишком низко (будет перекрыт клавиатурой)
            if (rect.bottom > availableHeight) {
                window.scrollTo({
                    top: scrollTo,
                    behavior: 'smooth'
                });
            }
        }, 500); // Задержка для появления клавиатуры
    }

    // Функция для определения мобильного устройства
    function isMobile() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }

    // Добавляем обработчики событий input для моментальной валидации
    Object.keys(inputs).forEach(key => {
        const input = inputs[key];

        input.addEventListener('input', () => {
            touchedFields[key] = true;
            isFormTouched = true;
            validateField(input, `error-${key}`, validationRules[key], true);
            updateSubmitButton();
        });

        input.addEventListener('blur', () => {
            touchedFields[key] = true;
            isFormTouched = true;
            validateField(input, `error-${key}`, validationRules[key], true);
            updateSubmitButton();
        });

        // Улучшенное поведение при фокусе
        input.addEventListener('focus', () => {
            scrollToInput(input);
        });

        // Добавляем обработчик для устройств iOS
        if (isMobile() && /iPad|iPhone|iPod/.test(navigator.userAgent)) {
            input.addEventListener('touchstart', () => {
                scrollToInput(input);
            });
        }
    });

    // Handle file selection
    const handleFiles = debounce(async function (files) {
        if (!files || files.length === 0) return;

        const imageFiles = Array.from(files).filter(file => file.type.startsWith('image/'));
        const newFiles = imageFiles.filter(file => {
            return !uploadedFiles.some(existing => existing.name === file.name && existing.size === file.size);
        });

        const remainingSlots = MAX_PHOTOS - uploadedFiles.length;
        if (newFiles.length > remainingSlots) {
            alert(`Вы можете загрузить максимум ${MAX_PHOTOS} фотографий.`);
        }

        for (const file of newFiles.slice(0, remainingSlots)) {
            if (file.size > 5 * 1024 * 1024) {
                alert(`Файл ${file.name} превышает допустимый размер (5MB).`);
                continue;
            }

            uploadedFiles.push(file);
            // Создаем превью и добавляем файл в список для отправки
            previewFile(file);

            // Оптимизируем файл для отправки
            const optimizedFile = await optimizeImage(file);
            optimizedFiles.push({
                originalName: file.name,
                originalSize: file.size,
                file: optimizedFile
            });
        }

        updateUI();
        fileInput.value = '';
    }, 300);

    fileInput.addEventListener('change', function (e) {
        if (this.files && this.files.length > 0) {
            handleFiles(this.files);
            isFormTouched = true;
            updateSubmitButton();
        }
    });

    // Обновление состояния кнопки отправки
    function updateSubmitButton() {
        const isFormValid = validateForm();
        const hasPhotos = uploadedFiles.length > 0;
        const hasPetSelected = selectedPetId !== null;

        submitButton.disabled = !isFormValid || !hasPhotos || !hasPetSelected;
    }

    // Создание превью файла
    function previewFile(file) {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onloadend = function () {
            const tempImg = new Image();
            tempImg.src = reader.result;
            tempImg.onload = function () {
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                const maxSize = 200;
                let width = tempImg.width;
                let height = tempImg.height;

                if (width > height && width > maxSize) {
                    height = Math.round((height * maxSize) / width);
                    width = maxSize;
                } else if (height > maxSize) {
                    width = Math.round((width * maxSize) / height);
                    height = maxSize;
                }
                canvas.width = width;
                canvas.height = height;
                ctx.drawImage(tempImg, 0, 0, width, height);
                const resizedDataUrl = canvas.toDataURL('image/jpeg', 0.8);
                const previewElement = document.createElement('div');
                previewElement.className = 'image-preview';
                previewElement.dataset.fileName = file.name;
                previewElement.dataset.fileSize = file.size;

                const img = document.createElement('img');
                img.src = resizedDataUrl;

                const removeButton = document.createElement('button');
                removeButton.className = 'remove-btn';
                removeButton.innerHTML = '×';
                removeButton.addEventListener('click', function () {
                    removeFile(file.name, file.size);
                });

                previewElement.appendChild(img);
                previewElement.appendChild(removeButton);
                imagePreviewsContainer.appendChild(previewElement);
            };
        };
    }

    // Удаление файла
    function removeFile(fileName, fileSize) {
        uploadedFiles = uploadedFiles.filter(file => !(file.name === fileName && file.size === fileSize));
        optimizedFiles = optimizedFiles.filter(item => !(item.originalName === fileName && item.originalSize === fileSize));

        const previewToRemove = imagePreviewsContainer.querySelector(`[data-file-name="${fileName}"][data-file-size="${fileSize}"]`);
        if (previewToRemove) {
            imagePreviewsContainer.removeChild(previewToRemove);
        }
        updateUI();
    }

    // Обновление UI
    function updateUI() {
        photoCountElement.textContent = uploadedFiles.length;
        fileInput.disabled = uploadedFiles.length >= MAX_PHOTOS;
        if (isFormTouched) {
            updateSubmitButton();
        }
    }

    // Отправка формы
    async function submitForm() {
        // Mark all fields as touched before submission
        Object.keys(touchedFields).forEach(key => {
            touchedFields[key] = true;
            validateField(inputs[key], `error-${key}`, validationRules[key], true, true);
        });

        if (isUploading || !validateForm(true)) {
            return;
        }

        isUploading = true;
        spinner.classList.add('show');
        submitButton.disabled = true;

        try {
            const formData = new FormData();

            // Используем оптимизированные файлы вместо оригинальных
            optimizedFiles.forEach(item => {
                formData.append("photos", item.file, item.originalName);
            });

            formData.append("title", inputs.reportTitle.value);
            formData.append("content", inputs.reportContent.value);
            formData.append("pet_id", selectedPetId);

            console.log("Current URL:", window.location.href);
            console.log("Submitting to /reports/create_with_photos");

            // Разделяем на части, если размер данных большой
            const MAX_CHUNK_SIZE = 1024 * 1024; // 1MB на чанк

            const response = await fetch("/reports/create_with_photos", {
                method: "POST",
                body: formData,
                // Добавляем заголовок, чтобы избежать проблем с таймаутом
                headers: {
                    // Не добавляем Content-Type, потому что браузер автоматически
                    // добавит правильный Content-Type с boundary для multipart/form-data
                }
            });

            const data = await response.json();

            if (data.status === "error") {
                alert(data.message);
                return;
            }

            if (data.status === "success" && data.redirect_url) {
                alert("Объявление добавлено!");
                window.location.href = data.redirect_url;
                return;
            }

            throw new Error("Неизвестный ответ от сервера");
        } catch (e) {
            console.error('Error:', e);
            alert("Произошла ошибка: " + e.message);
        } finally {
            isUploading = false;
            spinner.classList.remove('show');
            updateUI();
        }
    }

    // Для Telegram Web App - обработка изменений высоты viewport
    if (window.Telegram && window.Telegram.WebApp) {
        const tg = window.Telegram.WebApp;
        tg.ready();
        tg.onEvent('viewportChanged', function() {
            // Если есть активный элемент ввода, прокручиваем к нему
            const activeElement = document.activeElement;
            if (activeElement && ['INPUT', 'TEXTAREA'].includes(activeElement.tagName)) {
                scrollToInput(activeElement);
            }
        });
    }

    submitButton.addEventListener('click', submitForm);
    updateUI();
};
