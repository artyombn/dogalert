window.onload = () => {
    // DOM Elements
    const fileInput = document.getElementById('fileInput');
    const imagePreviewsContainer = document.getElementById('image-previews');
    const photoCountElement = document.getElementById('photo-count');
    const submitButton = document.getElementById('submit-btn');
    const spinner = document.getElementById('spinner');
    
    const petAgeField = document.getElementById('petAge');
    const minValue = petAgeField.getAttribute('min');
    const maxValue = petAgeField.getAttribute('max');
    const placeholder = petAgeField.getAttribute('placeholder');
    
    // Создаем новое текстовое поле
    const newPetAgeField = document.createElement('input');
    newPetAgeField.type = 'text';
    newPetAgeField.id = 'petAge';
    newPetAgeField.className = petAgeField.className;
    newPetAgeField.placeholder = placeholder;
    
    // Заменяем старое поле на новое
    petAgeField.parentNode.replaceChild(newPetAgeField, petAgeField);

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
        petAge: document.getElementById("petAge"), // Это уже новое текстовое поле
        petColor: document.getElementById("petColor"),
        petDescription: document.getElementById("petDescription")
    };

    const MAX_PHOTOS = 5;
    let uploadedFiles = [];
    let isUploading = false;
    let isFormTouched = false;

    // Правила валидации для каждого поля
    const validationRules = {
        petName: { required: true, minLength: 2, maxLength: 15 },
        petBreed: { required: true, minLength: 2, maxLength: 50 },
        petAge: { required: true, isInteger: true, minValue: parseInt(minValue) || 0, maxValue: parseInt(maxValue) || 30 },
        petColor: { required: true, minLength: 2, maxLength: 30 },
        petDescription: { required: true, minLength: 10, maxLength: 200 }
    };

    // Добавляем специальную валидацию для поля возраста
    inputs.petAge.addEventListener('input', function() {
        const value = this.value.trim();
        const errorElement = document.getElementById('error-petAge');
        
        touchedFields.petAge = true;
        isFormTouched = true;
        
        // Проверяем, является ли введенное значение числом
        if (value === '') {
            if (validationRules.petAge.required) {
                this.classList.add('invalid');
                errorElement.textContent = 'Это поле обязательно';
                errorElement.classList.add('show');
            } else {
                this.classList.remove('invalid');
                errorElement.textContent = '';
                errorElement.classList.remove('show');
            }
        } else {
            const num = Number(value);
            if (isNaN(num) || !Number.isInteger(num)) {
                this.classList.add('invalid');
                errorElement.textContent = 'Должно быть целое число';
                errorElement.classList.add('show');
            } else if (num < validationRules.petAge.minValue) {
                this.classList.add('invalid');
                errorElement.textContent = `Минимальное значение: ${validationRules.petAge.minValue}`;
                errorElement.classList.add('show');
            } else if (num > validationRules.petAge.maxValue) {
                this.classList.add('invalid');
                errorElement.textContent = `Максимальное значение: ${validationRules.petAge.maxValue}`;
                errorElement.classList.add('show');
            } else {
                this.classList.remove('invalid');
                errorElement.textContent = '';
                errorElement.classList.remove('show');
            }
        }
        
        updateSubmitButton();
    });
    
    // Разрешаем вводить только цифры в поле возраста
    inputs.petAge.addEventListener('keypress', function(e) {
        // Разрешаем только цифры (коды 48-57) и клавиши управления
        if (!/\d/.test(e.key)) {
            e.preventDefault();
            
            // Показываем сообщение об ошибке
            const errorElement = document.getElementById('error-petAge');
            touchedFields.petAge = true;
            isFormTouched = true;
            
            this.classList.add('invalid');
            errorElement.textContent = 'Должно быть целое число';
            errorElement.classList.add('show');
        }
    });

    // Функция валидации поля
    function validateField(input, errorElementId, rules, touched) {
        const errorElement = document.getElementById(errorElementId);
        const value = input.value.trim();
        let error = '';

        if (touched) {
            if (rules.isInteger) {
                // Проверяем пустое значение для обязательного поля
                if (value === '') {
                    if (rules.required) {
                        error = 'Это поле обязательно';
                    }
                } else {
                    const num = Number(value);
                    // Проверяем валидность числа и диапазон
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

    // Загрузка файлов
    const handleFiles = debounce(function (files) {
        if (!files || files.length === 0) return;
        const imageFiles = Array.from(files).filter(file => file.type.startsWith('image/'));
        const newFiles = imageFiles.filter(file => {
            return !uploadedFiles.some(existing => existing.name === file.name && existing.size === file.size);
        });
        const remainingSlots = MAX_PHOTOS - uploadedFiles.length;
        if (newFiles.length > remainingSlots) {
            alert(`Вы можете загрузить максимум ${MAX_PHOTOS} фотографий.`);
        }
        newFiles.slice(0, remainingSlots).forEach(file => {
            if (file.size > 5 * 1024 * 1024) {
                alert(`Файл ${file.name} превышает допустимый размер (5MB).`);
                return;
            }
            uploadedFiles.push(file);
            previewFile(file);
        });
        updateUI();
        fileInput.value = '';
    }, 300);

    fileInput.addEventListener('change', function (e) {
        if (this.files && this.files.length > 0) {
            handleFiles(this.files);
            isFormTouched = true;
        }
    });

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
            if (rules.required && input.value.trim() === '' && !fieldValid) {
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
        submitButton.disabled = !validateForm() || uploadedFiles.length === 0;
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
        const previewToRemove = imagePreviewsContainer.querySelector(`[data-file-name="${fileName}"][data-file-size="${fileSize}"]`);
        if (previewToRemove) {
            imagePreviewsContainer.removeChild(previewToRemove);
        }
        updateUI();
    }

    // Очистка формы
    function clearForm() {
        Object.values(inputs).forEach(input => input.value = '');
        uploadedFiles = [];
        imagePreviewsContainer.innerHTML = '';
        Object.keys(touchedFields).forEach(key => {
            touchedFields[key] = false;
            const errorElement = document.getElementById(`error-${key}`);
            errorElement.textContent = '';
            errorElement.classList.remove('show');
            inputs[key].classList.remove('invalid');
        });
        isFormTouched = false;
        updateUI();
    }

    // Обновление UI
    function updateUI() {
        photoCountElement.textContent = uploadedFiles.length;
        fileInput.disabled = uploadedFiles.length >= MAX_PHOTOS;
        if (isFormTouched) { // Обновляем кнопку только если пользователь взаимодействовал с формой
            updateSubmitButton();
        }
    }

    // Отправка формы
    async function submitForm() {
        // Помечаем все поля как тронутые перед отправкой
        Object.keys(touchedFields).forEach(key => {
            touchedFields[key] = true;
            validateField(inputs[key], `error-${key}`, validationRules[key], true);
        });

        if (isUploading || !validateForm()) return;

        isUploading = true;
        spinner.classList.add('show');
        submitButton.disabled = true;

        try {
            const formData = new FormData();
            uploadedFiles.forEach(file => formData.append("photos", file, file.name));

            formData.append("pet_name", inputs.petName.value);
            formData.append("pet_breed", inputs.petBreed.value);
            formData.append("pet_age", inputs.petAge.value);
            formData.append("pet_color", inputs.petColor.value);
            formData.append("pet_description", inputs.petDescription.value);

            const response = await fetch("/pets/create_with_photos", {
                method: "POST",
                body: formData
            });

            const data = await response.json();

            if (data.status === "error") {
                alert(data.message);
                return;
            }

            if (data.status === "success" && data.redirect_url) {
                alert("Питомец добавлен!");
                window.location.href = data.redirect_url;
                return;
            }

            throw new Error("Неизвестный ответ от сервера");
        } catch (e) {
            console.error("Ошибка:", e);
            alert("Сетевая ошибка: " + e.message);

        } finally {
            isUploading = false;
            spinner.classList.remove('show');
            updateUI();
        }
    }

    submitButton.addEventListener('click', submitForm);
    updateUI();
};