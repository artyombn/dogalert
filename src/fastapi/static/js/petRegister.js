const questions = [
  { key: "name",        label: "Как зовут питомца?" },
  { key: "breed",       label: "Какая порода?" },
  { key: "age",         label: "Сколько ему лет?" },
  { key: "color",       label: "Какого цвета?" },
  { key: "description", label: "Особенности питомца (характер, питание и т.д.)" },
];

let current = 0;
const answers = {};

function showQuestion() {
  if (current < questions.length) {
    const q = questions[current];
    document.getElementById("question-text").innerText = q.label;
    document.getElementById("answer-input").value = "";
  } else {
    sendAnswers();
  }
}

function nextQuestion() {
  const input = document.getElementById("answer-input");
  const value = input.value.trim();

  const key = questions[current].key;
  if (key === "age") {
    answers[key] = parseInt(value);
  } else {
    answers[key] = value;
  }

  current++;
  showQuestion();
}

function sendAnswers() {
  fetch("/registration/submit_pet_register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(answers)
  }).then((response) => {
    document.getElementById("question-container").innerHTML = "<p>Питомец добавлен!</p>";

    if (response.redirected) {
      setTimeout(() => {
        window.location.href = response.url;
      }, 1500);
    }
  });
}