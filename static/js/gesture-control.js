// Gesture Control Module
class GestureControl {
    constructor() {
        this.videoElement = null;
        this.isEnabled = false;
        this.lastGesture = null;
        this.gestureTimeout = null;
        this.gestureHistory = [];
        this.ws = null;
        this.gameType = null;
    }

    async init(videoElement, gameType) {
        this.videoElement = videoElement;
        this.gameType = gameType;
        this.setupEventListeners();
        await this.startGestureDetection();
    }

    setupEventListeners() {
        document.addEventListener('gestureDetected', (event) => {
            const { gesture, confidence } = event.detail;
            this.handleGesture(gesture, confidence);
        });
    }

    async startGestureDetection() {
        try {
            // Close existing connection if any
            if (this.ws) {
                this.ws.close();
            }

            // Create new WebSocket connection for specific game type
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${wsProtocol}//${window.location.host}/gesture_stream/${this.gameType}`;
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.error) {
                    console.error('Gesture stream error:', data.error);
                    this.handleError(data.error);
                    return;
                }
                
                this.processGameGesture(data);
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket failed:', error);
                this.handleError('Connection to gesture stream failed');
                this.ws.close();
            };

            this.ws.onclose = () => {
                console.log('WebSocket connection closed');
                this.isEnabled = false;
                this.dispatchGestureEvent('connection_closed');
            };

            this.isEnabled = true;
        } catch (error) {
            console.error('Failed to start gesture detection:', error);
            this.handleError('Failed to initialize gesture detection');
        }
    }

    handleError(error) {
        const event = new CustomEvent('gestureError', {
            detail: { error, timestamp: Date.now() }
        });
        document.dispatchEvent(event);
    }

    processGameGesture(data) {
        if (!this.isEnabled) return;

        // Process different types of gesture data based on game type
        switch (this.gameType) {
            case 'rps':
                if (data.gesture) {
                    this.dispatchGestureEvent('rps', data.gesture);
                }
                break;
            case 'piano':
                if (data.finger_positions) {
                    this.dispatchGestureEvent('piano', data.finger_positions);
                }
                break;
            case 'maze':
                if (data.head_pose) {
                    this.dispatchGestureEvent('maze', data.head_pose);
                }
                break;
            case 'pong':
                if (data.hand_position) {
                    this.dispatchGestureEvent('pong', data.hand_position);
                }
                break;
            case 'archery':
                if (data.archery_pose) {
                    this.dispatchGestureEvent('archery', data.archery_pose);
                }
                break;
            case 'dance':
                if (data.dance_pose) {
                    this.dispatchGestureEvent('dance', data.dance_pose);
                }
                break;
            case 'face':
                if (data.expression) {
                    this.dispatchGestureEvent('face', data.expression);
                }
                break;
            case 'math':
                if (data.finger_count !== undefined) {
                    this.dispatchGestureEvent('math', data.finger_count);
                }
                break;
            case 'video':
                if (data.gesture) {
                    this.executeVideoCommand(data.gesture);
                }
                break;
        }
    }

    executeVideoCommand(gesture) {
        if (!this.isEnabled || !this.videoElement) return;

        switch (gesture) {
            case 'palm':
                this.videoElement.paused ? this.videoElement.play() : this.videoElement.pause();
                break;
            case 'point_left':
                this.videoElement.currentTime -= 10;
                break;
            case 'point_right':
                this.videoElement.currentTime += 10;
                break;
            case 'index_up':
                this.videoElement.volume = Math.min(1, this.videoElement.volume + 0.1);
                break;
            case 'fist':
                this.videoElement.volume = Math.max(0, this.videoElement.volume - 0.1);
                break;
        }

        this.dispatchGestureEvent('video', gesture);
    }

    dispatchGestureEvent(type, data) {
        const event = new CustomEvent('gestureExecuted', {
            detail: { 
                type,
                data,
                timestamp: Date.now() 
            }
        });
        document.dispatchEvent(event);
    }

    enable() {
        this.isEnabled = true;
    }

    disable() {
        this.isEnabled = false;
    }

    destroy() {
        if (this.ws) {
            this.ws.close();
        }
        this.videoElement = null;
        this.isEnabled = false;
        this.gameType = null;
    }
}

// Initialize gesture control
window.gestureControl = new GestureControl();

// Automatically start gesture control when page loads
window.addEventListener('load', () => {
    const videoElement = document.querySelector('video');
    if (videoElement) {
        gestureControl.init(videoElement);
        gestureControl.enable();
    }
});