// Game state
let gameState = {
    playerScore: 0,
    aiScore: 0,
    gamesPlayed: 0,
    playerWins: 0,
    currentStreak: 0,
    bestStreak: 0,
    isGameActive: false,
    lastGesture: null,
    gestureTimeout: null
};

// DOM elements
const elements = {
    playerScore: document.getElementById('player-score'),
    aiScore: document.getElementById('ai-score'),
    playerGesture: document.getElementById('player-gesture'),
    aiGesture: document.getElementById('ai-gesture'),
    roundResult: document.getElementById('round-result'),
    cameraFeed: document.getElementById('camera-feed'),
    gestureCanvas: document.getElementById('gesture-canvas'),
    cameraOverlay: document.querySelector('.camera-overlay'),
    debugInfo: document.getElementById('debug-info'),
    gamesPlayed: document.getElementById('games-played'),
    winRate: document.getElementById('win-rate'),
    bestStreak: document.getElementById('best-streak')
};

// WebSocket connection
let ws = null;
let cameraStream = null;
let gestureContext = null;

// Initialize game
async function initGame() {
    try {
        // Initialize camera
        cameraStream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 640 },
                height: { ideal: 480 },
                facingMode: 'user'
            }
        });
        
        elements.cameraFeed.srcObject = cameraStream;
        elements.cameraFeed.onloadedmetadata = () => {
            elements.cameraFeed.play();
            elements.cameraOverlay.classList.add('hidden');
        };

        // Initialize canvas
        gestureContext = elements.gestureCanvas.getContext('2d');
        elements.gestureCanvas.width = elements.cameraFeed.videoWidth;
        elements.gestureCanvas.height = elements.cameraFeed.videoHeight;

        // Connect to WebSocket
        ws = new WebSocket(`ws://${window.location.host}/gesture_stream/rps`);
        
        ws.onopen = () => {
            console.log('WebSocket connected');
            startGame();
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleGestureData(data);
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            showError('Connection error. Please refresh the page.');
        };

        ws.onclose = () => {
            console.log('WebSocket closed');
            showError('Connection lost. Please refresh the page.');
        };

    } catch (error) {
        console.error('Error initializing game:', error);
        showError('Failed to access camera. Please ensure camera permissions are granted.');
    }
}

// Start game
function startGame() {
    gameState.isGameActive = true;
    elements.roundResult.textContent = 'Show your gesture to play!';
    updateStats();
}

// Handle gesture data
function handleGestureData(data) {
    if (!gameState.isGameActive) return;

    // Update debug info
    updateDebugInfo(data);

    // Clear previous gesture timeout
    if (gameState.gestureTimeout) {
        clearTimeout(gameState.gestureTimeout);
    }

    // Process gesture from the first hand detected
    if (data.hands && data.hands.length > 0) {
        const hand = data.hands[0];
        if (hand.gesture && hand.gesture !== gameState.lastGesture) {
            gameState.lastGesture = hand.gesture;
            playRound(hand.gesture);
        }
    }

    // Set timeout to clear gesture if no new data received
    gameState.gestureTimeout = setTimeout(() => {
        gameState.lastGesture = null;
        updatePlayerGesture('Waiting...', '✋');
    }, 500);
}

// Detect gesture from hand data
function detectGesture(data) {
    if (!data.hands || data.hands.length === 0) return null;

    const hand = data.hands[0];
    const fingers = countFingers(hand);

    if (fingers === 0) return 'rock';
    if (fingers === 2) return 'scissors';
    if (fingers === 5) return 'paper';
    
    return null;
}

// Count extended fingers
function countFingers(hand) {
    let count = 0;
    const fingerJoints = [
        [8, 7, 6],   // Index finger
        [12, 11, 10], // Middle finger
        [16, 15, 14], // Ring finger
        [20, 19, 18]  // Pinky finger
    ];

    for (const [tip, pip, mcp] of fingerJoints) {
        if (isFingerExtended(hand[tip], hand[pip], hand[mcp])) {
            count++;
        }
    }

    // Count thumb separately
    if (isThumbExtended(hand[4], hand[3], hand[2])) {
        count++;
    }

    return count;
}

// Check if finger is extended
function isFingerExtended(tip, pip, mcp) {
    return tip.y < pip.y && pip.y < mcp.y;
}

// Check if thumb is extended
function isThumbExtended(tip, ip, mcp) {
    return tip.x > ip.x && ip.x > mcp.x;
}

// Play a round
function playRound(playerGesture) {
    const aiGesture = getAIGesture();
    const result = determineWinner(playerGesture, aiGesture);

    // Update UI
    updatePlayerGesture(getGestureLabel(playerGesture), getGestureEmoji(playerGesture));
    updateAIGesture(getGestureLabel(aiGesture), getGestureEmoji(aiGesture));
    updateRoundResult(result, playerGesture, aiGesture);

    // Update scores and stats
    if (result === 'win') {
        gameState.playerScore++;
        gameState.playerWins++;
        gameState.currentStreak++;
        if (gameState.currentStreak > gameState.bestStreak) {
            gameState.bestStreak = gameState.currentStreak;
        }
    } else if (result === 'lose') {
        gameState.aiScore++;
        gameState.currentStreak = 0;
    }

    gameState.gamesPlayed++;
    updateStats();
}

// Get AI gesture
function getAIGesture() {
    const gestures = ['rock', 'paper', 'scissors'];
    return gestures[Math.floor(Math.random() * gestures.length)];
}

// Determine winner
function determineWinner(player, ai) {
    if (player === ai) return 'draw';
    if (
        (player === 'rock' && ai === 'scissors') ||
        (player === 'paper' && ai === 'rock') ||
        (player === 'scissors' && ai === 'paper')
    ) {
        return 'win';
    }
    return 'lose';
}

// Update player gesture display
function updatePlayerGesture(label, emoji) {
    elements.playerGesture.querySelector('.gesture-label').textContent = label;
    elements.playerGesture.querySelector('.gesture-icon').textContent = emoji;
}

// Update AI gesture display
function updateAIGesture(label, emoji) {
    elements.aiGesture.querySelector('.gesture-label').textContent = label;
    elements.aiGesture.querySelector('.gesture-icon').textContent = emoji;
}

// Update round result
function updateRoundResult(result, player, ai) {
    let message = '';
    if (result === 'win') {
        message = `You win! ${getGestureLabel(player)} beats ${getGestureLabel(ai)}`;
    } else if (result === 'lose') {
        message = `You lose! ${getGestureLabel(ai)} beats ${getGestureLabel(player)}`;
    } else {
        message = `It's a draw! Both chose ${getGestureLabel(player)}`;
    }
    elements.roundResult.textContent = message;
}

// Update game stats
function updateStats() {
    elements.playerScore.textContent = gameState.playerScore;
    elements.aiScore.textContent = gameState.aiScore;
    elements.gamesPlayed.textContent = gameState.gamesPlayed;
    elements.winRate.textContent = gameState.gamesPlayed > 0 
        ? `${Math.round((gameState.playerWins / gameState.gamesPlayed) * 100)}%` 
        : '0%';
    elements.bestStreak.textContent = gameState.bestStreak;
}

// Update debug information
function updateDebugInfo(data) {
    if (!data.hands || data.hands.length === 0) {
        elements.debugInfo.querySelector('.debug-hand').textContent = 'Hand: Not detected';
        elements.debugInfo.querySelector('.debug-fingers').textContent = 'Fingers: 0';
        elements.debugInfo.querySelector('.debug-gesture').textContent = 'Gesture: None';
        return;
    }

    const hand = data.hands[0];
    elements.debugInfo.querySelector('.debug-hand').textContent = 'Hand: Detected';
    elements.debugInfo.querySelector('.debug-fingers').textContent = `Fingers: ${hand.finger_count}`;
    elements.debugInfo.querySelector('.debug-gesture').textContent = `Gesture: ${hand.gesture || 'None'}`;
}

// Get gesture label
function getGestureLabel(gesture) {
    const labels = {
        rock: 'Rock',
        paper: 'Paper',
        scissors: 'Scissors'
    };
    return labels[gesture] || 'Unknown';
}

// Get gesture emoji
function getGestureEmoji(gesture) {
    const emojis = {
        rock: '✊',
        paper: '✋',
        scissors: '✌️'
    };
    return emojis[gesture] || '❓';
}

// Show error message
function showError(message) {
    elements.cameraOverlay.classList.remove('hidden');
    elements.cameraOverlay.querySelector('.camera-status').innerHTML = `
        <i class="fas fa-exclamation-circle"></i>
        <span>${message}</span>
    `;
}

// Initialize game when page loads
document.addEventListener('DOMContentLoaded', initGame); 