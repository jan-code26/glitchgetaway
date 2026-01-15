// GlitchGetaway Demo Script

// Demo puzzle data
const demoPuzzle = {
    question: "What is the correct closing tag for an HTML paragraph?",
    answer: "</p>",
    hint: "All HTML tags use angled brackets. A closing tag starts with a slash.",
    description: "Welcome to your first glitch! You need to fix broken HTML."
};

// Command history
let commandHistory = [];
let historyIndex = 0;

// Initialize the demo
window.addEventListener('DOMContentLoaded', () => {
    initializeTheme();
    initializeTerminal();
    initializeThemeSwitcher();
});

// Theme Management
function initializeTheme() {
    const body = document.querySelector('body');
    let theme = localStorage.getItem('glitchgetaway-theme');
    
    if (!theme) {
        const currentHour = new Date().getHours();
        theme = (currentHour >= 7 && currentHour <= 19) ? 'light' : 'dark';
        localStorage.setItem('glitchgetaway-theme', theme);
    }
    
    applyTheme(theme);
}

function applyTheme(theme) {
    const body = document.querySelector('body');
    const themeButton = document.getElementById('theme-switcher');
    
    if (theme === 'light') {
        body.classList.add('light-theme');
        if (themeButton) themeButton.textContent = '🌙';
    } else {
        body.classList.remove('light-theme');
        if (themeButton) themeButton.textContent = '☀️';
    }
}

function initializeThemeSwitcher() {
    const themeButton = document.getElementById('theme-switcher');
    
    themeButton.addEventListener('click', () => {
        const body = document.querySelector('body');
        const isLight = body.classList.contains('light-theme');
        const newTheme = isLight ? 'dark' : 'light';
        
        localStorage.setItem('glitchgetaway-theme', newTheme);
        applyTheme(newTheme);
    });
}

// Terminal Functionality
function initializeTerminal() {
    const terminalInput = document.getElementById('terminal-input');
    const errorMessage = document.getElementById('error-message');
    const successMessage = document.getElementById('success-message');
    
    // Focus input on load
    terminalInput.focus();
    
    // Re-focus input when clicking anywhere on the terminal
    document.querySelector('.terminal-screen').addEventListener('click', () => {
        terminalInput.focus();
    });
    
    // Handle keyboard input
    terminalInput.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowUp') {
            e.preventDefault();
            if (historyIndex > 0) {
                historyIndex--;
                terminalInput.value = commandHistory[historyIndex];
            }
        }
        
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            if (historyIndex < commandHistory.length - 1) {
                historyIndex++;
                terminalInput.value = commandHistory[historyIndex];
            } else {
                historyIndex = commandHistory.length;
                terminalInput.value = '';
            }
        }
        
        if (e.key === 'Enter') {
            e.preventDefault();
            const input = terminalInput.value.trim();
            
            if (input !== '') {
                commandHistory.push(input);
                historyIndex = commandHistory.length;
                handleCommand(input.toLowerCase());
            }
            
            terminalInput.value = '';
        }
    });
}

function handleCommand(command) {
    const errorMessage = document.getElementById('error-message');
    const successMessage = document.getElementById('success-message');
    
    // Hide previous messages
    errorMessage.style.display = 'none';
    successMessage.style.display = 'none';
    
    // Handle special commands
    if (command === 'hint') {
        showError(`[[ SYSTEM HINT ]] ${demoPuzzle.hint}`);
        return;
    }
    
    if (command === 'help') {
        showError('[[ COMMANDS ]] Available commands: help, hint, clear');
        return;
    }
    
    if (command === 'clear') {
        errorMessage.style.display = 'none';
        successMessage.style.display = 'none';
        return;
    }
    
    // Check answer
    if (command === demoPuzzle.answer.toLowerCase()) {
        showSuccess('🎉 Correct! You escaped the first glitch!\n\n[[ SYSTEM ]] This is just a taste of GlitchGetaway.\nPlay the full game to solve more puzzles!');
        
        // Add confetti effect
        setTimeout(() => {
            createConfetti();
        }, 500);
    } else {
        showError('[[ SYSTEM ]] Incorrect. Try again or type "hint" for a clue.');
    }
}

function showError(message) {
    const errorMessage = document.getElementById('error-message');
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
}

function showSuccess(message) {
    const successMessage = document.getElementById('success-message');
    successMessage.textContent = message;
    successMessage.style.display = 'block';
}

// Confetti Effect
function createConfetti() {
    const colors = ['#00FF00', '#00FFFF', '#FFFF00', '#FF00FF', '#00FF7F'];
    const confettiCount = 50;
    
    for (let i = 0; i < confettiCount; i++) {
        setTimeout(() => {
            const confetti = document.createElement('div');
            confetti.style.position = 'fixed';
            confetti.style.width = '10px';
            confetti.style.height = '10px';
            confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
            confetti.style.left = Math.random() * window.innerWidth + 'px';
            confetti.style.top = '-10px';
            confetti.style.opacity = '1';
            confetti.style.borderRadius = '50%';
            confetti.style.pointerEvents = 'none';
            confetti.style.zIndex = '9999';
            
            document.body.appendChild(confetti);
            
            const duration = 2000 + Math.random() * 1000;
            const drift = (Math.random() - 0.5) * 200;
            
            confetti.animate([
                { 
                    transform: 'translateY(0px) translateX(0px) rotate(0deg)',
                    opacity: 1
                },
                { 
                    transform: `translateY(${window.innerHeight + 10}px) translateX(${drift}px) rotate(${Math.random() * 360}deg)`,
                    opacity: 0
                }
            ], {
                duration: duration,
                easing: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)'
            });
            
            setTimeout(() => {
                confetti.remove();
            }, duration);
        }, i * 30);
    }
}

// Easter egg: Konami code
let konamiCode = [];
const konamiSequence = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'b', 'a'];

document.addEventListener('keydown', (e) => {
    konamiCode.push(e.key);
    konamiCode = konamiCode.slice(-konamiSequence.length);
    
    if (konamiCode.join(',') === konamiSequence.join(',')) {
        showSuccess('🎮 KONAMI CODE ACTIVATED! You found the easter egg!\n\nYou\'re a true gamer! ⭐');
        createConfetti();
        konamiCode = [];
    }
});
