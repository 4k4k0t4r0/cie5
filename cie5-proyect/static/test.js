// test.js

// Función para mostrar la pregunta actual
function showQuestion(questionId) {
    var questions = document.querySelectorAll('.question');
    for (var i = 0; i < questions.length; i++) {
        questions[i].style.display = 'none';
    }
    document.getElementById(questionId).style.display = 'block';
}

// Función para navegar a la pregunta anterior
function previousQuestion() {
    var currentQuestion = document.querySelector('.question:not([style*="display: none"])');
    if (currentQuestion.previousElementSibling && currentQuestion.previousElementSibling.classList.contains('question')) {
        currentQuestion.style.display = 'none';
        currentQuestion.previousElementSibling.style.display = 'block';
    }
}

// Función para navegar a la siguiente pregunta
function nextQuestion() {
    var currentQuestion = document.querySelector('.question:not([style*="display: none"])');
    if (currentQuestion.nextElementSibling && currentQuestion.nextElementSibling.classList.contains('question')) {
        currentQuestion.style.display = 'none';
        currentQuestion.nextElementSibling.style.display = 'block';
    }
}

// Event listeners para los botones de navegación
document.getElementById('prevBtn').addEventListener('click', function() {
    previousQuestion();
});

document.getElementById('nextBtn').addEventListener('click', function() {
    nextQuestion();
});

// Mostrar la primera pregunta al cargar la página
showQuestion('question1');
