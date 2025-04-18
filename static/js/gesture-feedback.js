class GestureFeedback {
    constructor() {
        this.feedbackElement = null;
        this.gestureHistory = [];
        this.maxHistoryItems = 5;
        this.createFeedbackUI();
        this.setupEventListeners();
    }

    createFeedbackUI() {
        // Create feedback container
        this.feedbackElement = document.createElement('div');
        this.feedbackElement.className = 'gesture-feedback';
        this.feedbackElement.innerHTML = `
            <div class="gesture-status">
                <div class="status-indicator"></div>
                <span class="status-text">Gesture Control Ready</span>
            </div>
            <div class="gesture-history"></div>
            <div class="gesture-controls">
                <button class="toggle-gesture" onclick="gestureFeedback.toggleGestureControl()">
                    <span class="icon">👋</span>
                    <span class="text">Enable Gestures</span>
                </button>
            </div>
        `;

        // Add styles
        const styles = document.createElement('style');
        styles.textContent = `
            .gesture-feedback {
                position: fixed;
                top: 20px;
                right: 20px;
                background: rgba(15, 23, 42, 0.9);
                border-radius: 12px;
                padding: 16px;
                color: white;
                font-family: 'Inter', sans-serif;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(148, 163, 184, 0.1);
                z-index: 1000;
                min-width: 240px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
            }

            .gesture-status {
                display: flex;
                align-items: center;
                margin-bottom: 12px;
            }

            .status-indicator {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #22c55e;
                margin-right: 8px;
            }

            .status-indicator.disabled {
                background: #94a3b8;
            }

            .gesture-history {
                margin: 12px 0;
                font-size: 0.9rem;
                color: #94a3b8;
            }

            .gesture-history-item {
                padding: 4px 0;
                display: flex;
                justify-content: space-between;
                animation: fadeIn 0.3s ease;
            }

            .toggle-gesture {
                background: linear-gradient(135deg, #22d3ee, #0ea5e9);
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                color: white;
                cursor: pointer;
                display: flex;
                align-items: center;
                width: 100%;
                justify-content: center;
                font-size: 0.9rem;
                transition: all 0.3s ease;
            }

            .toggle-gesture:hover {
                opacity: 0.9;
                transform: translateY(-1px);
            }

            .toggle-gesture .icon {
                margin-right: 8px;
            }

            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(5px); }
                to { opacity: 1; transform: translateY(0); }
            }
        `;

        document.head.appendChild(styles);
        document.body.appendChild(this.feedbackElement);
    }

    setupEventListeners() {
        document.addEventListener('gestureExecuted', (event) => {
            const { gesture, timestamp } = event.detail;
            this.updateGestureHistory(gesture, timestamp);
        });
    }

    updateGestureHistory(gesture, timestamp) {
        const time = new Date(timestamp).toLocaleTimeString();
        this.gestureHistory.unshift({ gesture, time });
        
        if (this.gestureHistory.length > this.maxHistoryItems) {
            this.gestureHistory.pop();
        }

        this.renderGestureHistory();
    }

    renderGestureHistory() {
        const historyElement = this.feedbackElement.querySelector('.gesture-history');
        historyElement.innerHTML = this.gestureHistory
            .map(item => `
                <div class="gesture-history-item">
                    <span>${item.gesture}</span>
                    <span>${item.time}</span>
                </div>
            `)
            .join('');
    }

    toggleGestureControl() {
        const isEnabled = window.gestureControl.isEnabled;
        const newState = !isEnabled;
        
        window.gestureControl.isEnabled = newState;
        
        const indicator = this.feedbackElement.querySelector('.status-indicator');
        const statusText = this.feedbackElement.querySelector('.status-text');
        const toggleButton = this.feedbackElement.querySelector('.toggle-gesture .text');
        
        if (newState) {
            indicator.classList.remove('disabled');
            statusText.textContent = 'Gesture Control Active';
            toggleButton.textContent = 'Disable Gestures';
        } else {
            indicator.classList.add('disabled');
            statusText.textContent = 'Gesture Control Disabled';
            toggleButton.textContent = 'Enable Gestures';
        }
    }
}

// Initialize gesture feedback
const gestureFeedback = new GestureFeedback();
window.gestureFeedback = gestureFeedback; // Make it globally accessible