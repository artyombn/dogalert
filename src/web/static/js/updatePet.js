window.onload = () => {
    // DOM Elements
    const fileInput = document.getElementById('fileInput');
    const imagePreviewsContainer = document.getElementById('image-previews');
    const photoCountElement = document.getElementById('photo-count');
    const submitButton = document.getElementById('submitBtn');
    const spinner = document.getElementById('spinner');
    const updateForm = document.getElementById('updateForm');
    const petId = updateForm?.dataset?.petId;

    // Проверяем наличие обязательных элементов
    if (!updateForm || !petId) {
        console.error('Форма обновления или ID питомца не найдены');
        return;
    }

    // Существующие фотографии питомца
    const existingPhotos = document.querySelectorAll('.pet-photo');
    let existingPhotoUrls = Array.from(existingPhotos).map(img => img.src);
    let photosToDelete = []; // URLs фотографий для удаления
    let deletedPhotoIds = []; // ID удаленных фото для отслеживания

    const originalPetAgeField = document.getElementById('petAge');
    if (!originalPetAgeField) {
        console.error('Поле возраста не найдено');
        return;
    }

    const minValue = 1;
    const maxValue = 30;
    const placeholder = originalPetAgeField.getAttribute('placeholder') || 'Введите возраст';

    const petAgeField = document.createElement('input');
    petAgeField.type = 'text';
    petAgeField.id = 'petAge';
    petAgeField.name = 'petAge';
    petAgeField.className = originalPetAgeField.className;
    petAgeField.placeholder = placeholder;
    petAgeField.value = originalPetAgeField.value;

    originalPetAgeField.parentNode.replaceChild(petAgeField, originalPetAgeField);

    const touchedFields = {
        petName: false,
        petBreed: false,
        petAge: false,
        petColor: false,
        petDescription: false
    };

    const inputs = {
        petName: document.getElementById("petName"),
        petBreed: document.getElementById("petBreed"),
        petAge: petAgeField,
        petColor: document.getElementById("petColor"),
        petDescription: document.getElementById("petDescription")
    };

    // Проверяем наличие всех полей
    for (const [key, input] of Object.entries(inputs)) {
        if (!input) {
            console.error(`Поле ${key} не найдено`);
            return;
        }
    }

    // Сохраняем исходные значения для сравнения
    const originalValues = {
        petName: inputs.petName.value,
        petBreed: inputs.petBreed.value,
        petAge: inputs.petAge.value,
        petColor: inputs.petColor.value,
        petDescription: inputs.petDescription.value
    };

    const MAX_PHOTOS = 5;
    let uploadedFiles = [];
    let optimizedFiles = [];
    let isUploading = false;
    let isFormTouched = false;

    // Правила валидации для каждого поля
    const validationRules = {
        petName: {required: true, minLength: 2, maxLength: 15},
        petBreed: {required: true, minLength: 2, maxLength: 50},
        petAge: {required: true, isInteger: true, minValue: minValue, maxValue: maxValue},
        petColor: {required: true, minLength: 2, maxLength: 30},
        petDescription: {required: true, minLength: 10, maxLength: 200}
    };

    // Функция для удаления существующей фотографии
    async function deleteExistingPhoto(photoId, photoElement) {
        if (!confirm('Точно удалить фото?')) {
            return;
        }

        console.log('Начинаем удаление фото ID:', photoId);
        console.log('Элемент фото:', photoElement);

        try {
            const response = await fetch(`/pets/photo_delete/${photoId}?pet_id=${petId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            console.log('Ответ сервера:', response.status, response.statusText);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('Данные ответа:', data);

            if (data.status === 'success') {
                console.log('Фото успешно удалено на сервере, скрываем элемент');

                // Скрываем контейнер фотографии
                photoElement.style.display = 'none';

                // Добавляем в список удаленных (если нужно для логики формы)
                if (!deletedPhotoIds.includes(parseInt(photoId))) {
                    deletedPhotoIds.push(parseInt(photoId));
                }

                isFormTouched = true;

                // Обновляем UI
                updatePhotoUI();
                updateSubmitButton();

                // Показываем сообщение об успехе
                alert('Фото удалено успешно!');
            } else {
                console.error('Сервер вернул ошибку:', data.message);
                alert(data.message || 'Ошибка при удалении фото');
            }
        } catch (error) {
            console.error('Ошибка при удалении фото:', error);
            alert('Произошла ошибка при удалении фото: ' + error.message);
        }
    }

    // Добавляем кнопки удаления к существующим фотографиям
    function addDeleteButtonsToExistingPhotos() {
        const removeButtons = document.querySelectorAll('.remove-existing-btn');

        console.log('Найдено кнопок удаления существующих фото:', removeButtons.length);

        removeButtons.forEach((button) => {
            const photoId = button.getAttribute('data-photo-id');
            const petIdAttr = button.getAttribute('data-pet-id');

            if (!photoId || !petIdAttr) {
                console.warn('Кнопка удаления без ID:', button);
                return;
            }

            console.log('Настраиваем кнопку для фото ID:', photoId);

            // Убираем старые обработчики если есть - клонируем кнопку
            const newButton = button.cloneNode(true);
            button.parentNode.replaceChild(newButton, button);

            // Применяем стили к новой кнопке - УМЕНЬШЕННЫЕ размеры
            newButton.style.cssText = `
                position: absolute;
                top: 2px;
                right: 2px;
                background: rgba(0, 0, 0, 0.7);
                color: white;
                border: none;
                border-radius: 50%;
                width: 24px;    /* Уменьшено с 30px */
                height: 24px;   /* Уменьшено с 30px */
                cursor: pointer;
                font-size: 14px; /* Уменьшено с 16px */
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10;
                line-height: 1;
                padding: 2px;   /* Уменьшено с 4px */
                min-width: 24px;
                min-height: 24px;
                transition: all 0.2s ease;
            `;

            // Добавляем hover эффекты
            newButton.addEventListener('mouseenter', function() {
                this.style.background = 'rgba(255, 0, 0, 0.9)';
                this.style.transform = 'scale(1.1)';
            });

            newButton.addEventListener('mouseleave', function() {
                this.style.background = 'rgba(0, 0, 0, 0.7)';
                this.style.transform = 'scale(1)';
            });

            // Добавляем обработчик клика
            newButton.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                console.log('Клик по кнопке удаления фото ID:', photoId);

                const photoContainer = this.closest('.existing-photo-container');
                if (!photoContainer) {
                    console.error('Не найден контейнер фото для удаления');
                    return;
                }

                deleteExistingPhoto(photoId, photoContainer);
            });
        });
    }

    // Функция для обновления UI фотографий и кнопки загрузки
    function updatePhotoUI() {
        // Правильный селектор для существующих фото
        const existingPhotoContainers = document.querySelectorAll('.existing-photo-container');
        const visibleExistingPhotos = Array.from(existingPhotoContainers).filter(container =>
            container.style.display !== 'none'
        ).length;

        const totalPhotos = uploadedFiles.length + visibleExistingPhotos;

        console.log('Видимых существующих фото:', visibleExistingPhotos);
        console.log('Загруженных новых фото:', uploadedFiles.length);
        console.log('Всего фото:', totalPhotos);

        if (photoCountElement) {
            photoCountElement.textContent = totalPhotos;
        }

        const uploadContainer = document.querySelector('.upload-photo-btn-container');
        if (uploadContainer) {
            uploadContainer.style.display = totalPhotos >= MAX_PHOTOS ? 'none' : 'inline-block';
        }

        if (fileInput) {
            fileInput.disabled = totalPhotos >= MAX_PHOTOS;
        }
    }

    // Проверяем, изменились ли данные формы
    function hasFormChanged() {
        // Проверяем текстовые поля
        const fieldsChanged = Object.keys(originalValues).some(key => {
            return inputs[key].value !== originalValues[key];
        });

        // Проверяем фотографии
        const photosChanged = uploadedFiles.length > 0 || deletedPhotoIds.length > 0;

        console.log('Изменились поля:', fieldsChanged);
        console.log('Изменились фото:', photosChanged);
        console.log('Удалено фото IDs:', deletedPhotoIds);

        return fieldsChanged || photosChanged;
    }

    // Добавляем специальную валидацию для поля возраста
    inputs.petAge.addEventListener('input', function () {
        const value = this.value.trim();
        const errorElement = document.getElementById('error-petAge');

        touchedFields.petAge = true;
        isFormTouched = true;

        if (value === '') {
            if (validationRules.petAge.required) {
                this.classList.add('invalid');
                if (errorElement) {
                    errorElement.textContent = 'Это поле обязательно';
                    errorElement.classList.add('show');
                }
            } else {
                this.classList.remove('invalid');
                if (errorElement) {
                    errorElement.textContent = '';
                    errorElement.classList.remove('show');
                }
            }
        } else {
            const num = Number(value);
            if (isNaN(num) || !Number.isInteger(num)) {
                this.classList.add('invalid');
                if (errorElement) {
                    errorElement.textContent = 'Должно быть целое число';
                    errorElement.classList.add('show');
                }
            } else if (num < minValue) {
                this.classList.add('invalid');
                if (errorElement) {
                    errorElement.textContent = `Возраст не может быть меньше ${minValue}`;
                    errorElement.classList.add('show');
                }
            } else if (num > maxValue) {
                this.classList.add('invalid');
                if (errorElement) {
                    errorElement.textContent = `Максимальный возраст: ${maxValue}`;
                    errorElement.classList.add('show');
                }
            } else {
                this.classList.remove('invalid');
                if (errorElement) {
                    errorElement.textContent = '';
                    errorElement.classList.remove('show');
                }
            }
        }

        updateSubmitButton();
    });

    // For number inputs, we use this instead of keypress to control input
    inputs.petAge.addEventListener('keydown', function (e) {
        // Allow: backspace, delete, tab, escape, enter
        if ([46, 8, 9, 27, 13].indexOf(e.keyCode) !== -1 ||
            // Allow: Ctrl+A
            (e.keyCode === 65 && e.ctrlKey === true) ||
            // Allow: Ctrl+C
            (e.keyCode === 67 && e.ctrlKey === true) ||
            // Allow: Ctrl+V
            (e.keyCode === 86 && e.ctrlKey === true) ||
            // Allow: Ctrl+X
            (e.keyCode === 88 && e.ctrlKey === true) ||
            // Allow: home, end, left, right
            (e.keyCode >= 35 && e.keyCode <= 39)) {
            // let it happen, don't do anything
            return;
        }

        // Ensure that it is a number and stop the keypress if not
        if ((e.shiftKey || (e.keyCode < 48 || e.keyCode > 57)) &&
            (e.keyCode < 96 || e.keyCode > 105)) {
            e.preventDefault();

            // Show error message
            const errorElement = document.getElementById('error-petAge');
            touchedFields.petAge = true;
            isFormTouched = true;

            this.classList.add('invalid');
            if (errorElement) {
                errorElement.textContent = 'Должно быть целое число';
                errorElement.classList.add('show');
            }
        }
    });

    // Force validation on blur to catch any values outside min/max range
    inputs.petAge.addEventListener('blur', function () {
        touchedFields.petAge = true;
        isFormTouched = true;

        const value = this.value.trim();
        const errorElement = document.getElementById('error-petAge');

        if (value !== '') {
            const num = Number(value);
            if (!isNaN(num) && Number.isInteger(num)) {
                if (num < validationRules.petAge.minValue) {
                    if (errorElement) {
                        errorElement.textContent = `Возраст не может быть меньше ${validationRules.petAge.minValue}`;
                        errorElement.classList.add('show');
                    }
                    this.classList.add('invalid');
                } else if (num > validationRules.petAge.maxValue) {
                    if (errorElement) {
                        errorElement.textContent = `Максимальный возраст: ${validationRules.petAge.maxValue}`;
                        errorElement.classList.add('show');
                    }
                    this.classList.add('invalid');
                }
            }
        }

        updateSubmitButton();
    });

    // Функция оптимизации изображения
    async function optimizeImage(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onerror = () => reject(new Error('Ошибка чтения файла'));
            reader.onloadend = function () {
                const img = new Image();
                img.onerror = () => reject(new Error('Ошибка загрузки изображения'));
                img.src = reader.result;
                img.onload = function () {
                    try {
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
                                if (blob) {
                                    // Создаем новый файл из blob
                                    const optimizedFile = new File(
                                        [blob],
                                        file.name,
                                        {type: 'image/jpeg', lastModified: Date.now()}
                                    );
                                    resolve(optimizedFile);
                                } else {
                                    reject(new Error('Ошибка создания оптимизированного файла'));
                                }
                            },
                            'image/jpeg',
                            quality
                        );
                    } catch (error) {
                        reject(error);
                    }
                };
            };
            reader.readAsDataURL(file);
        });
    }

    // Функция валидации поля
    function validateField(input, errorElementId, rules, touched) {
        const errorElement = document.getElementById(errorElementId);
        const value = input.value.trim();
        let error = '';

        if (touched) {
            if (input.id === 'petAge') {
                if (value === '') {
                    if (rules.required) {
                        error = 'Это поле обязательно';
                    }
                } else {
                    const num = Number(value);
                    if (isNaN(num) || !Number.isInteger(num)) {
                        error = 'Должно быть целое число';
                    } else if (num < minValue) {
                        error = `Возраст не может быть меньше ${minValue}`;
                    } else if (num > maxValue) {
                        error = `Максимальное значение: ${maxValue}`;
                    }
                }
            } else if (rules.isInteger) { // Для других числовых полей
                if (value === '') {
                    if (rules.required) {
                        error = 'Это поле обязательно';
                    }
                } else {
                    const num = Number(value);
                    if (isNaN(num) || !Number.isInteger(num)) {
                        error = 'Должно быть целое число';
                    } else if (rules.minValue !== undefined && num < rules.minValue) {
                        error = `Минимальное значение: ${rules.minValue}`;
                    } else if (rules.maxValue !== undefined && num > rules.maxValue) {
                        error = `Максимальное значение: ${rules.maxValue}`;
                    }
                }
            } else { // Для текстовых полей
                if (value === '') {
                    if (rules.required) {
                        error = 'Это поле обязательно';
                    }
                } else {
                    if (rules.minLength && value.length < rules.minLength) {
                        error = `Минимум ${rules.minLength} символа(ов)`;
                    } else if (rules.maxLength && value.length > rules.maxLength) {
                        error = `Максимум ${rules.maxLength} символа(ов)`;
                    }
                }
            }

            // Обновление UI
            if (error) {
                input.classList.add('invalid');
                if (errorElement) {
                    errorElement.textContent = error;
                    errorElement.classList.add('show');
                }
            } else {
                input.classList.remove('invalid');
                if (errorElement) {
                    errorElement.textContent = '';
                    errorElement.classList.remove('show');
                }
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

    // Загрузка файлов
    const handleFiles = debounce(async function (files) {
        if (!files || files.length === 0) return;

        const imageFiles = Array.from(files).filter(file => file.type.startsWith('image/'));
        const newFiles = imageFiles.filter(file => {
            return !uploadedFiles.some(existing => existing.name === file.name && existing.size === file.size);
        });

        // Подсчитываем доступные слоты (учитываем существующие фото, которые не удалены)
        const visibleExistingPhotos = Array.from(existingPhotos).filter(photo =>
            photo.parentElement.style.display !== 'none'
        ).length;
        const remainingSlots = MAX_PHOTOS - uploadedFiles.length - visibleExistingPhotos;

        if (newFiles.length > remainingSlots) {
            alert(`Вы можете загрузить максимум ${MAX_PHOTOS} фотографий.`);
        }

        for (const file of newFiles.slice(0, remainingSlots)) {
            if (file.size > 50 * 1024 * 1024) { // 50MB как в PATCH роуте
                alert(`Файл ${file.name} превышает допустимый размер (50MB).`);
                continue;
            }

            uploadedFiles.push(file);
            // Создаем превью и добавляем файл в список для отправки
            previewFile(file);

            try {
                // Оптимизируем файл для отправки
                const optimizedFile = await optimizeImage(file);
                optimizedFiles.push({
                    originalName: file.name,
                    originalSize: file.size,
                    file: optimizedFile
                });
            } catch (error) {
                console.error('Ошибка оптимизации файла:', error);
                alert(`Ошибка обработки файла ${file.name}`);
            }
        }

        updatePhotoUI();
        if (fileInput) fileInput.value = '';
    }, 300);

    if (fileInput) {
        fileInput.addEventListener('change', function (e) {
            if (this.files && this.files.length > 0) {
                handleFiles(this.files);
                isFormTouched = true;
            }
        });
    }

    // Валидация всех полей формы
    function validateForm() {
        let isValid = true;

        Object.keys(inputs).forEach(key => {
            const input = inputs[key];
            const rules = validationRules[key];
            const errorElementId = `error-${key}`;
            const touched = touchedFields[key];

            const fieldValid = validateField(input, errorElementId, rules, touched);

            // Поле считается невалидным, если:
            // 1. Оно обязательно и пустое, ИЛИ
            // 2. Оно тронуто и есть ошибка валидации
            if (rules.required && input.value.trim() === '') {
                isValid = false;
            } else if (touched && !fieldValid) {
                isValid = false;
            }
        });
        return isValid;
    }

    // Добавляем обработчики событий input для моментальной валидации
    Object.keys(inputs).forEach(key => {
        if (key === 'petAge') return; // Пропускаем petAge, т.к. у него своя обработка

        const input = inputs[key];
        input.addEventListener('input', () => {
            touchedFields[key] = true;
            isFormTouched = true; // Пользователь взаимодействовал с формой
            validateField(input, `error-${key}`, validationRules[key], touchedFields[key]);
            updateSubmitButton();
        });
        input.addEventListener('blur', () => {
            touchedFields[key] = true;
            isFormTouched = true; // Пользователь взаимодействовал с формой
            validateField(input, `error-${key}`, validationRules[key], touchedFields[key]);
            updateSubmitButton();
        });
    });

    // Обновление состояния кнопки отправки
    function updateSubmitButton() {
        if (!submitButton) return;

        const isValid = validateForm();
        const hasChanges = hasFormChanged();
        submitButton.disabled = !isValid || !hasChanges;
    }

    // Создание превью файла (как в addPet.js)
    function previewFile(file) {
        const reader = new FileReader();
        reader.onerror = () => {
            console.error('Ошибка чтения файла для превью');
            alert(`Ошибка чтения файла ${file.name}`);
        };
        reader.onloadend = function () {
            const tempImg = new Image();
            tempImg.onerror = () => {
                console.error('Ошибка загрузки изображения для превью');
                alert(`Ошибка обработки изображения ${file.name}`);
            };
            tempImg.src = reader.result;
            tempImg.onload = function () {
                try {
                    const canvas = document.createElement('canvas');
                    const ctx = canvas.getContext('2d');
                    const maxSize = 150; // Уменьшено с 200 до 150
                    let width = tempImg.width;
                    let height = tempImg.height;

                    // Логика изменения размера
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

                    // Создаем превью элемент
                    const previewElement = document.createElement('div');
                    previewElement.className = 'image-preview';
                    previewElement.dataset.fileName = file.name;
                    previewElement.dataset.fileSize = file.size;

                    const img = document.createElement('img');
                    img.src = resizedDataUrl;

                    // Создаем кнопку удаления для НОВЫХ фото
                    const removeButton = document.createElement('button');
                    removeButton.className = 'remove-btn';
                    removeButton.innerHTML = '×';
                    removeButton.type = 'button';

                    // Стили кнопки удаления для новых фото (остаются прежними)
                    removeButton.style.cssText = `
                        position: absolute;
                        top: 4px;
                        right: 4px;
                        background: rgba(0, 0, 0, 0.5);
                        color: white;
                        border: none;
                        border-radius: 50%;
                        width: 25px;
                        height: 25px;
                        font-size: 14px;
                        cursor: pointer;
                        line-height: 20px;
                        text-align: center;
                        z-index: 10;
                        transition: background-color 0.2s ease;
                    `;

                    // Hover эффект для новых фото
                    removeButton.addEventListener('mouseenter', function() {
                        this.style.backgroundColor = 'rgba(255, 0, 0, 0.9)';
                    });

                    removeButton.addEventListener('mouseleave', function() {
                        this.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
                    });

                    removeButton.addEventListener('click', function (e) {
                        e.preventDefault();
                        e.stopPropagation();
                        console.log('Удаляем новое фото:', file.name);
                        removeFile(file.name, file.size);
                    });

                    previewElement.appendChild(img);
                    previewElement.appendChild(removeButton);

                    if (imagePreviewsContainer) {
                        imagePreviewsContainer.appendChild(previewElement);
                    }

                    // Обновляем UI после добавления превью
                    updatePhotoUI();
                    updateSubmitButton();
                } catch (error) {
                    console.error('Ошибка создания превью:', error);
                    alert(`Ошибка создания превью для ${file.name}`);
                }
            };
        };
        reader.readAsDataURL(file);
    }

    // Удаление файла из загруженных
    function removeFile(fileName, fileSize) {
        // Удаляем из массива загруженных файлов
        uploadedFiles = uploadedFiles.filter(file =>
            !(file.name === fileName && file.size === fileSize)
        );

        // Удаляем из массива оптимизированных файлов
        optimizedFiles = optimizedFiles.filter(item =>
            !(item.originalName === fileName && item.originalSize === fileSize)
        );

        // Удаляем превью
        const preview = document.querySelector(
            `.image-preview[data-file-name="${fileName}"][data-file-size="${fileSize}"]`
        );
        if (preview) {
            preview.remove();
        }

        // Обновляем UI
        updatePhotoUI();
        updateSubmitButton();
        isFormTouched = true;
    }

    // Инициализация кнопок удаления для существующих фотографий
    addDeleteButtonsToExistingPhotos();

    // Обработчик отправки формы
    if (updateForm) {
        updateForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            if (isUploading) return;

            const isValid = validateForm();
            const hasChanges = hasFormChanged();

            if (!isValid || !hasChanges) {
                alert('Пожалуйста, заполните все поля корректно или внесите изменения');
                return;
            }

            isUploading = true;
            if (submitButton) submitButton.disabled = true;
            if (spinner) spinner.style.display = 'block';


            try {
                const formData = new FormData();

                const fieldMapping = {
                    'petName': 'name',
                    'petBreed': 'breed',
                    'petAge': 'age',
                    'petColor': 'color',
                    'petDescription': 'description'
                };

                // Добавляем текстовые поля с правильными именами
                Object.keys(inputs).forEach(key => {
                    const backendFieldName = fieldMapping[key];
                    const value = inputs[key].value.trim();

                    if (backendFieldName === 'age') {
                        const ageValue = parseInt(value, 10);
                        if (!isNaN(ageValue)) {
                            formData.append(backendFieldName, ageValue.toString());
                        }
                    } else {
                        formData.append(backendFieldName, value);
                    }
                });

                // Добавляем новые фотографии
                optimizedFiles.forEach((item, index) => {
                    formData.append('photos', item.file);
                });

                // Добавляем ID удаленных фотографий
                if (deletedPhotoIds.length > 0) {
                    formData.append('deletedPhotoIds', JSON.stringify(deletedPhotoIds));
                }

                console.log('Отправляемые данные:');
                for (let [key, value] of formData.entries()) {
                    console.log(key, value);
                }

                const response = await fetch(updateForm.action, {
                    method: 'PATCH',
                    body: formData
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const result = await response.json();

                if (result.status === 'success') {
                    alert('Информация о питомце успешно обновлена!');
                    // Перенаправляем или обновляем страницу
                    if (result.redirect_url) {
                        window.location.href = result.redirect_url;
                    } else {
                        window.location.reload();
                    }
                } else {
                    alert(result.message || 'Ошибка при обновлении информации');
                }

            } catch (error) {
                console.error('Ошибка при отправке формы:', error);
                alert('Произошла ошибка при обновлении информации');
            } finally {
                isUploading = false;
                if (submitButton) submitButton.disabled = false;
                if (spinner) spinner.style.display = 'none';
            }
        });
    }

    // Инициализация UI
    updatePhotoUI();
    updateSubmitButton();
};