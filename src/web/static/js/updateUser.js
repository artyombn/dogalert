window.onload = () => {
    const submitButton = document.getElementById("submitBtn");
    const form = document.getElementById("updateForm");

    const userId = form.dataset.userId;

    const touchedFields = {
        userFirstName: false,
        userLastName: false,
        userPhone: false,
    };

    const inputs = {
        userFirstName: document.getElementById("userFirstName"),
        userLastName: document.getElementById("userLastName"),
        userPhone: document.getElementById("userPhone"),
    };

    const validationRules = {
        userFirstName: { required: true, minLength: 2, maxLength: 20 },
        userLastName: { required: true, minLength: 2, maxLength: 20 },
        userPhone: {
            required: true,
            pattern: /^\+7\d{10}$/,
            errorMsg: 'Введите номер в международном формате (например, +79001234567)'
        },
    };

    function validateField(input, errorElementId, rules, touched) {
        const errorElement = document.getElementById(errorElementId);
        const value = input.value.trim();
        let error = '';

        if (!touched) {
            input.classList.remove('is-invalid');
            errorElement.textContent = '';
            return true;
        }

        if (rules.required && value === '') {
            error = 'Это поле обязательно';
        } else if (rules.pattern && !rules.pattern.test(value)) {
            error = rules.errorMsg || 'Неверный формат';
        } else {
            if (rules.minLength && value.length < rules.minLength) {
                error = `Минимум ${rules.minLength} символа(ов)`;
            } else if (rules.maxLength && value.length > rules.maxLength) {
                error = `Максимум ${rules.maxLength} символа(ов)`;
            }
        }

        if (error) {
            input.classList.add('is-invalid');
            errorElement.textContent = error;
        } else {
            input.classList.remove('is-invalid');
            errorElement.textContent = '';
        }

        return error === '';
    }


    function validateForm() {
        let isValid = true;
        Object.keys(inputs).forEach(key => {
            const input = inputs[key];
            const rules = validationRules[key];
            const errorElementId = `error-${key}`;
            const fieldValid = validateField(input, errorElementId, rules, touchedFields[key]);
            if (!fieldValid) {
                isValid = false;
            }
        });

        submitButton.disabled = !isValid;
        return isValid;
    }

    Object.keys(inputs).forEach(key => {
        const input = inputs[key];

        // Поле считается тронутым при blur (когда убираем фокус)
        input.addEventListener('blur', () => {
            touchedFields[key] = true;
            validateField(input, `error-${key}`, validationRules[key], true);
            validateForm();
        });

        // Также можно считать поле тронутым при вводе
        input.addEventListener('input', () => {
            if (!touchedFields[key]) {
                touchedFields[key] = true;
            }
            validateField(input, `error-${key}`, validationRules[key], touchedFields[key]);
            validateForm();
        });
    });


    form.addEventListener("submit", async (e) => {
        e.preventDefault(); // отменяем обычную отправку формы

        Object.keys(touchedFields).forEach(key => {
            touchedFields[key] = true;
        });

        if (!validateForm()) {
            return;
        }
        try {
            const formData = new FormData();
            formData.append("first_name", inputs.userFirstName.value.trim());
            formData.append("last_name", inputs.userLastName.value.trim());
            formData.append("phone", inputs.userPhone.value.trim());

            const response = await fetch(`/users/update/${encodeURIComponent(userId)}`, {
                method: "PUT",
                body: formData,
            });

            const data = await response.json();

            if (data.status === "error") {
                alert(data.message);
                return;
            }

            if (data.status === "success") {
                alert(data.message);
                return;
            }

            throw new Error("Неизвестный ответ от сервера");
        } catch (e) {
            console.error("Ошибка:", e);
            alert("Сетевая ошибка: " + e.message);
        }
    });
};
