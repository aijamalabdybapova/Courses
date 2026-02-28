// Система смены темы
document.addEventListener('DOMContentLoaded', function() {
    // Проверяем сохраненную тему
    const currentTheme = localStorage.getItem('theme') || 'light';
    setTheme(currentTheme);
    
    // Кнопка переключения темы
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
        updateThemeIcon(currentTheme);
    }
    
    // Анимация при загрузке
    const cards = document.querySelectorAll('.card, .stat-card, .feature-card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('fade-in');
    });
});

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    updateThemeIcon(theme);
    updateProgressCircles();
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
}

function updateThemeIcon(theme) {
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        if (theme === 'dark') {
            themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
            themeToggle.title = 'Переключить на светлую тему';
        } else {
            themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
            themeToggle.title = 'Переключить на темную тему';
        }
    }
}

function updateProgressCircles() {
    const circles = document.querySelectorAll('.progress-circle-fill');
    circles.forEach(circle => {
        const percentage = circle.getAttribute('data-percentage');
        if (percentage) {
            const offset = 314 - (percentage * 314 / 100);
            circle.style.strokeDashoffset = offset;
        }
    });
}

// Инициализация прогресс кругов
document.addEventListener('DOMContentLoaded', updateProgressCircles);