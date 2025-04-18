// Mini-games implementation
class GameManager {
    constructor() {
        this.currentGame = null;
        this.gameContainer = document.getElementById('game-container');
        this.score = 0;
        this.isPlaying = false;
    }

    startGame(gameName) {
        this.score = 0;
        this.isPlaying = true;
        this.currentGame = gameName;
        
        switch(gameName) {
            case 'memory':
                this.initMemoryGame();
                break;
            case 'reaction':
                this.initReactionGame();
                break;
            case 'gesture':
                this.initGestureGame();
                break;
        }
    }

    stopGame() {
        this.isPlaying = false;
        this.gameContainer.innerHTML = '';
        this.currentGame = null;
    }

    updateScore(points) {
        this.score += points;
        const scoreElement = document.getElementById('game-score');
        if (scoreElement) {
            scoreElement.textContent = `Score: ${this.score}`;
        }
    }

    // Memory Card Game
    initMemoryGame() {
        const cards = ['🎥', '🎬', '🎭', '🎪', '🎨', '🎯', '🎲', '🎮'];
        const gameCards = [...cards, ...cards];
        let flippedCards = [];
        let matchedPairs = 0;

        // Shuffle cards
        gameCards.sort(() => Math.random() - 0.5);

        // Create game UI
        this.gameContainer.innerHTML = `
            <div class="game-header">
                <h2>Memory Game</h2>
                <p id="game-score">Score: ${this.score}</p>
            </div>
            <div class="memory-grid"></div>
        `;

        const grid = this.gameContainer.querySelector('.memory-grid');
        
        gameCards.forEach((card, index) => {
            const cardElement = document.createElement('div');
            cardElement.className = 'memory-card';
            cardElement.dataset.cardIndex = index;
            cardElement.innerHTML = `
                <div class="card-inner">
                    <div class="card-front">?</div>
                    <div class="card-back">${card}</div>
                </div>
            `;

            cardElement.addEventListener('click', () => {
                if (!this.isPlaying || flippedCards.length >= 2 || 
                    cardElement.classList.contains('flipped') ||
                    cardElement.classList.contains('matched')) {
                    return;
                }

                cardElement.classList.add('flipped');
                flippedCards.push({ element: cardElement, value: card });

                if (flippedCards.length === 2) {
                    if (flippedCards[0].value === flippedCards[1].value) {
                        flippedCards.forEach(card => card.element.classList.add('matched'));
                        matchedPairs++;
                        this.updateScore(10);
                        
                        if (matchedPairs === cards.length) {
                            setTimeout(() => {
                                alert('Congratulations! You won!');
                                this.stopGame();
                            }, 500);
                        }
                    } else {
                        setTimeout(() => {
                            flippedCards.forEach(card => card.element.classList.remove('flipped'));
                        }, 1000);
                    }
                    flippedCards = [];
                }
            });

            grid.appendChild(cardElement);
        });
    }

    // Reaction Time Game
    initReactionGame() {
        this.gameContainer.innerHTML = `
            <div class="game-header">
                <h2>Reaction Time</h2>
                <p id="game-score">Score: ${this.score}</p>
            </div>
            <div class="reaction-area">
                <div class="target">Click when green!</div>
            </div>
        `;

        const target = this.gameContainer.querySelector('.target');
        let startTime;
        let timeoutId;
        let isWaiting = true;

        const startRound = () => {
            if (!this.isPlaying) return;
            
            target.style.backgroundColor = 'red';
            target.textContent = 'Wait...';
            isWaiting = true;

            const delay = 1000 + Math.random() * 4000;
            timeoutId = setTimeout(() => {
                if (!this.isPlaying) return;
                
                target.style.backgroundColor = 'green';
                target.textContent = 'Click Now!';
                startTime = Date.now();
                isWaiting = false;
            }, delay);
        };

        target.addEventListener('click', () => {
            if (!this.isPlaying) return;

            if (isWaiting) {
                clearTimeout(timeoutId);
                target.style.backgroundColor = '#ff4444';
                target.textContent = 'Too Early! Try again...';
                setTimeout(startRound, 1000);
            } else {
                const reactionTime = Date.now() - startTime;
                const points = Math.max(0, Math.floor((1000 - reactionTime) / 10));
                this.updateScore(points);
                
                target.style.backgroundColor = '#4444ff';
                target.textContent = `${reactionTime}ms! +${points} points`;
                setTimeout(startRound, 1500);
            }
        });

        startRound();
    }

    // Gesture Control Game
    initGestureGame() {
        this.gameContainer.innerHTML = `
            <div class="game-header">
                <h2>Gesture Control Game</h2>
                <p id="game-score">Score: ${this.score}</p>
            </div>
            <div class="gesture-game">
                <div class="target-gesture">✋</div>
                <div class="gesture-instruction">Match the gesture!</div>
            </div>
        `;

        const gestures = ['✋', '✌️', '👆', '👊'];
        const targetGesture = this.gameContainer.querySelector('.target-gesture');
        const instruction = this.gameContainer.querySelector('.gesture-instruction');
        let currentGesture = 0;

        const updateGesture = () => {
            if (!this.isPlaying) return;
            
            currentGesture = (currentGesture + 1) % gestures.length;
            targetGesture.textContent = gestures[currentGesture];
            instruction.textContent = 'Match the gesture!';
            
            // This would integrate with the gesture recognition system
            // For now, we'll just update automatically
            setTimeout(() => {
                if (this.isPlaying) {
                    this.updateScore(5);
                    instruction.textContent = 'Good job! Next gesture...';
                    setTimeout(updateGesture, 1000);
                }
            }, 2000);
        };

        setTimeout(updateGesture, 2000);
    }
}

// Initialize game manager
const gameManager = new GameManager();

// Event listeners for game buttons
document.addEventListener('DOMContentLoaded', () => {
    const gameButtons = document.querySelectorAll('.game-btn');
    gameButtons.forEach(button => {
        button.addEventListener('click', () => {
            const gameName = button.dataset.game;
            if (gameName) {
                gameManager.startGame(gameName);
            }
        });
    });
});

let gestureEventSource = null;
let isDebugMode = false;
let lastGestureTime = 0;
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;
const baseReconnectDelay = 1000;
let playerChoice = null;
let computerChoice = null;
let gameInProgress = false;

const choices = ['rock', 'paper', 'scissors'];
const gestureMap = {
    'fist': 'rock',
    'five': 'paper',
    'peace': 'scissors'
};

function toggleDebugMode() {
    isDebugMode = !isDebugMode;
    document.getElementById('debug-info').style.display = isDebugMode ? 'block' : 'none';
}

function updateDebugInfo(message) {
    if (isDebugMode) {
        const debugInfo = document.getElementById('debug-info');
        debugInfo.textContent = message;
    }
}

function startGestureStream() {
    if (gestureEventSource) {
        gestureEventSource.close();
    }

    gestureEventSource = new EventSource('/gesture-stream');
    
    gestureEventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        updateDebugInfo(JSON.stringify(data, null, 2));
        
        if (data.gesture && !gameInProgress) {
            const currentTime = Date.now();
            if (currentTime - lastGestureTime > 1000) { // Debounce gestures
                lastGestureTime = currentTime;
                const mappedGesture = gestureMap[data.gesture];
                if (mappedGesture) {
                    handlePlayerChoice(mappedGesture);
                }
            }
        }
    };

    gestureEventSource.onerror = function(error) {
        console.error('EventSource failed:', error);
        updateDebugInfo('Connection error. Attempting to reconnect...');
        
        if (reconnectAttempts < maxReconnectAttempts) {
            const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 10000);
            setTimeout(() => {
                reconnectAttempts++;
                startGestureStream();
            }, delay);
        } else {
            updateDebugInfo('Max reconnection attempts reached. Please refresh the page.');
        }
    };
}

function handlePlayerChoice(choice) {
    if (gameInProgress) return;
    
    gameInProgress = true;
    playerChoice = choice;
    updateChoiceDisplay('player-choice', choice);
    
    // Simulate computer thinking
    document.getElementById('computer-choice').classList.add('thinking');
    
    setTimeout(() => {
        playRound();
    }, 1000);
}

function getComputerChoice() {
    return choices[Math.floor(Math.random() * choices.length)];
}

function updateChoiceDisplay(elementId, choice) {
    const element = document.getElementById(elementId);
    element.textContent = choice.charAt(0).toUpperCase() + choice.slice(1);
    element.className = 'choice ' + choice;
}

function determineWinner(player, computer) {
    if (player === computer) return 'tie';
    if ((player === 'rock' && computer === 'scissors') ||
        (player === 'paper' && computer === 'rock') ||
        (player === 'scissors' && computer === 'paper')) {
        return 'win';
    }
    return 'lose';
}

function playRound() {
    computerChoice = getComputerChoice();
    document.getElementById('computer-choice').classList.remove('thinking');
    updateChoiceDisplay('computer-choice', computerChoice);
    
    const result = determineWinner(playerChoice, computerChoice);
    const resultElement = document.getElementById('result');
    
    switch (result) {
        case 'win':
            resultElement.textContent = 'You win!';
            resultElement.className = 'win';
            break;
        case 'lose':
            resultElement.textContent = 'Computer wins!';
            resultElement.className = 'lose';
            break;
        case 'tie':
            resultElement.textContent = "It's a tie!";
            resultElement.className = 'tie';
            break;
    }
    
    setTimeout(() => {
        gameInProgress = false;
        document.getElementById('result').className = '';
    }, 2000);
}

// Initialize the game when the page loads
document.addEventListener('DOMContentLoaded', function() {
    startGestureStream();
    
    // Add click handlers for manual controls
    document.querySelectorAll('.control-btn').forEach(button => {
        button.addEventListener('click', () => {
            handlePlayerChoice(button.dataset.choice);
        });
    });
    
    // Add handler for debug mode toggle
    document.getElementById('debug-toggle').addEventListener('click', toggleDebugMode);
});

// Game state
let isPlaying = false;
let playerScore = 0;
let aiScore = 0;
let gamesPlayed = 0;
let currentStreak = 0;
let bestStreak = 0;

// DOM Elements
const startBtn = document.getElementById('start-game');
const debugBtn = document.getElementById('toggle-debug');
const debugInfo = document.getElementById('debug-info');
const playerGesture = document.getElementById('player-gesture');
const aiGesture = document.getElementById('ai-gesture');
const roundResult = document.getElementById('round-result');
const playerScoreDisplay = document.getElementById('player-score');
const aiScoreDisplay = document.getElementById('ai-score');
const gamesPlayedDisplay = document.getElementById('games-played');
const winRateDisplay = document.getElementById('win-rate');
const bestStreakDisplay = document.getElementById('best-streak');
const videoPreview = document.getElementById('camera-feed');

// Game configuration
const GESTURES = ['rock', 'paper', 'scissors'];
const GESTURE_ICONS = {
    'rock': '✊',
    'paper': '✋',
    'scissors': '✌️',
    'waiting': '❓'
};

// Initialize game
function initGame() {
    setupControls();
    
    // Initialize gesture control with game type
    window.gestureControl.init(videoPreview, 'rps');
    
    // Listen for gesture events
    document.addEventListener('gestureExecuted', handleGestureEvent);
    document.addEventListener('gestureError', handleGestureError);
}

// Set up control buttons
function setupControls() {
    startBtn.addEventListener('click', toggleGame);
    debugBtn.addEventListener('click', toggleDebug);
}

// Handle gesture events
function handleGestureEvent(event) {
    const { type, data } = event.detail;
    
    if (type === 'rps' && isPlaying) {
        const playerChoice = data;
        playRound(playerChoice);
        
        if (isDebugMode) {
            updateDebugInfo({ gesture: playerChoice });
        }
    }
}

// Handle gesture errors
function handleGestureError(event) {
    const { error } = event.detail;
    console.error('Gesture Error:', error);
    updateDebugInfo({ error });
}

// Play a round
function playRound(playerChoice) {
    // Update player's gesture display
    updateGestureDisplay(playerGesture, playerChoice);
    
    // Generate AI's choice
    const aiChoice = generateAIChoice();
    updateGestureDisplay(aiGesture, aiChoice);
    
    // Determine winner
    const result = determineWinner(playerChoice, aiChoice);
    updateScore(result);
    
    // Update round result display
    displayRoundResult(result, playerChoice, aiChoice);
}

// Generate AI's choice
function generateAIChoice() {
    return GESTURES[Math.floor(Math.random() * GESTURES.length)];
}

// Determine the winner
function determineWinner(playerChoice, aiChoice) {
    if (playerChoice === aiChoice) return 'tie';
    
    const winConditions = {
        'rock': 'scissors',
        'paper': 'rock',
        'scissors': 'paper'
    };
    
    return winConditions[playerChoice] === aiChoice ? 'win' : 'lose';
}

// Update the score
function updateScore(result) {
    if (result === 'win') {
        playerScore++;
        currentStreak++;
        bestStreak = Math.max(bestStreak, currentStreak);
    } else if (result === 'lose') {
        aiScore++;
        currentStreak = 0;
    }
    
    gamesPlayed++;
    
    // Update displays
    playerScoreDisplay.textContent = playerScore;
    aiScoreDisplay.textContent = aiScore;
    gamesPlayedDisplay.textContent = gamesPlayed;
    winRateDisplay.textContent = `${Math.round((playerScore / gamesPlayed) * 100)}%`;
    bestStreakDisplay.textContent = bestStreak;
}

// Update gesture display
function updateGestureDisplay(element, gesture) {
    const iconElement = element.querySelector('.gesture-icon');
    const labelElement = element.querySelector('.gesture-label');
    
    iconElement.textContent = GESTURE_ICONS[gesture] || GESTURE_ICONS.waiting;
    labelElement.textContent = gesture.charAt(0).toUpperCase() + gesture.slice(1);
}

// Display round result
function displayRoundResult(result, playerChoice, aiChoice) {
    let message = '';
    let color = '';
    
    switch (result) {
        case 'win':
            message = `You win! ${GESTURE_ICONS[playerChoice]} beats ${GESTURE_ICONS[aiChoice]}`;
            color = 'var(--success)';
            break;
        case 'lose':
            message = `AI wins! ${GESTURE_ICONS[aiChoice]} beats ${GESTURE_ICONS[playerChoice]}`;
            color = 'var(--error)';
            break;
        case 'tie':
            message = `It's a tie! Both chose ${GESTURE_ICONS[playerChoice]}`;
            color = 'var(--warning)';
            break;
    }
    
    roundResult.textContent = message;
    roundResult.style.color = color;
}

// Toggle game state
function toggleGame() {
    isPlaying = !isPlaying;
    
    if (isPlaying) {
        startBtn.innerHTML = '<i class="fas fa-stop"></i> Stop Game';
        roundResult.textContent = 'Show your gesture to play!';
        window.gestureControl.enable();
    } else {
        startBtn.innerHTML = '<i class="fas fa-play"></i> Start Game';
        roundResult.textContent = 'Game paused';
        window.gestureControl.disable();
    }
}

// Toggle debug mode
function toggleDebug() {
    isDebugMode = !isDebugMode;
    debugInfo.style.display = isDebugMode ? 'block' : 'none';
    debugBtn.innerHTML = isDebugMode ? 
        '<i class="fas fa-bug"></i> Hide Debug' : 
        '<i class="fas fa-bug"></i> Show Debug';
}

// Update debug information
function updateDebugInfo(data) {
    if (!isDebugMode) return;
    debugInfo.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
}

// Initialize the game when the page loads
document.addEventListener('DOMContentLoaded', initGame);
