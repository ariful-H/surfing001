// Initialize game elements
const canvas = document.getElementById('pianoCanvas');
const ctx = canvas.getContext('2d');
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const debugInfo = document.getElementById('debugInfo');
const videoPreview = document.getElementById('videoPreview');

let isPlaying = false;
let isDebugMode = false;

// Piano configuration
const keys = {
    white: ['C', 'D', 'E', 'F', 'G', 'A', 'B'],
    black: ['C#', 'D#', 'F#', 'G#', 'A#']
};

// Audio context and sounds
let audioContext;
let oscillator;

// Initialize game
function initGame() {
    setupCanvas();
    setupAudio();
    setupControls();
    
    // Initialize gesture control with game type
    window.gestureControl.init(videoPreview, 'piano');
    
    // Listen for gesture events
    document.addEventListener('gestureExecuted', handleGestureEvent);
    document.addEventListener('gestureError', handleGestureError);
}

// Set up canvas and drawing
function setupCanvas() {
    canvas.width = window.innerWidth * 0.8;
    canvas.height = window.innerHeight * 0.3;
    drawPiano();
}

// Set up Web Audio
function setupAudio() {
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
}

// Set up control buttons
function setupControls() {
    startBtn.addEventListener('click', startGame);
    stopBtn.addEventListener('click', stopGame);
    document.getElementById('debugToggle').addEventListener('click', toggleDebug);
}

// Handle gesture events
function handleGestureEvent(event) {
    const { type, data } = event.detail;
    
    if (type === 'piano') {
        const fingerPositions = data;
        playNoteFromGesture(fingerPositions);
        
        if (isDebugMode) {
            updateDebugInfo({ fingerPositions });
        }
    }
}

// Handle gesture errors
function handleGestureError(event) {
    const { error } = event.detail;
    console.error('Gesture Error:', error);
    updateDebugInfo({ error });
}

// Play note based on finger position
function playNoteFromGesture(fingerPositions) {
    if (!isPlaying) return;
    
    // Calculate which key was "pressed" based on finger position
    const keyIndex = Math.floor(fingerPositions.x * keys.white.length);
    const note = keys.white[keyIndex];
    
    if (note) {
        playNote(note);
        highlightKey(keyIndex);
    }
}

// Play a musical note
function playNote(note) {
    if (oscillator) {
        oscillator.stop();
    }
    
    oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    // Convert note to frequency
    const frequency = getNoteFrequency(note);
    oscillator.frequency.setValueAtTime(frequency, audioContext.currentTime);
    
    // Add envelope
    gainNode.gain.setValueAtTime(0, audioContext.currentTime);
    gainNode.gain.linearRampToValueAtTime(0.5, audioContext.currentTime + 0.1);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 1.5);
    
    oscillator.start();
    oscillator.stop(audioContext.currentTime + 1.5);
}

// Convert note name to frequency
function getNoteFrequency(note) {
    const noteMap = {
        'C': 261.63, // C4
        'C#': 277.18,
        'D': 293.66,
        'D#': 311.13,
        'E': 329.63,
        'F': 349.23,
        'F#': 369.99,
        'G': 392.00,
        'G#': 415.30,
        'A': 440.00, // A4
        'A#': 466.16,
        'B': 493.88
    };
    return noteMap[note] || 440;
}

// Draw piano keys
function drawPiano() {
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw white keys
    const whiteKeyWidth = canvas.width / keys.white.length;
    keys.white.forEach((note, i) => {
        ctx.beginPath();
        ctx.rect(i * whiteKeyWidth, 0, whiteKeyWidth, canvas.height);
        ctx.strokeStyle = '#000';
        ctx.stroke();
        ctx.fillStyle = '#fff';
        ctx.fill();
        
        // Add note label
        ctx.fillStyle = '#000';
        ctx.font = '20px Arial';
        ctx.fillText(note, (i * whiteKeyWidth) + (whiteKeyWidth / 3), canvas.height - 20);
    });
    
    // Draw black keys
    const blackKeyWidth = whiteKeyWidth * 0.6;
    const blackKeyHeight = canvas.height * 0.6;
    keys.black.forEach((note, i) => {
        const x = (whiteKeyWidth * [1, 2, 4, 5, 6][i]) - (blackKeyWidth / 2);
        ctx.beginPath();
        ctx.rect(x, 0, blackKeyWidth, blackKeyHeight);
        ctx.fillStyle = '#000';
        ctx.fill();
        
        // Add note label
        ctx.fillStyle = '#fff';
        ctx.font = '16px Arial';
        ctx.fillText(note, x + (blackKeyWidth / 4), blackKeyHeight - 20);
    });
}

// Highlight a key when played
function highlightKey(keyIndex) {
    const whiteKeyWidth = canvas.width / keys.white.length;
    
    // Clear previous highlight
    drawPiano();
    
    // Draw highlight
    ctx.beginPath();
    ctx.rect(keyIndex * whiteKeyWidth, 0, whiteKeyWidth, canvas.height);
    ctx.fillStyle = 'rgba(0, 255, 255, 0.3)';
    ctx.fill();
    
    // Reset after animation
    setTimeout(drawPiano, 200);
}

// Start the game
function startGame() {
    if (!isPlaying) {
        isPlaying = true;
        startBtn.disabled = true;
        stopBtn.disabled = false;
        window.gestureControl.enable();
    }
}

// Stop the game
function stopGame() {
    if (isPlaying) {
        isPlaying = false;
        startBtn.disabled = false;
        stopBtn.disabled = true;
        window.gestureControl.disable();
    }
}

// Toggle debug mode
function toggleDebug() {
    isDebugMode = !isDebugMode;
    debugInfo.style.display = isDebugMode ? 'block' : 'none';
}

// Update debug information
function updateDebugInfo(data) {
    if (!isDebugMode) return;
    debugInfo.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
}

// Handle window resize
window.addEventListener('resize', () => {
    setupCanvas();
});

// Initialize the game when the page loads
document.addEventListener('DOMContentLoaded', initGame); 