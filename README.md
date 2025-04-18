# QuantumGaze

QuantumGaze is an innovative web application that enables hands-free video control through gesture recognition. Built with Flask and powered by MediaPipe, it provides an intuitive way to interact with video content using hand gestures.

## Features

- Real-time hand gesture recognition
- Hands-free video control
- Rock Paper Scissors game with gesture detection
- YouTube video integration
- User authentication and profile management
- Responsive and modern UI

## Tech Stack

- **Backend**: Flask, Gunicorn
- **Frontend**: HTML5, CSS3, JavaScript
- **AI/ML**: MediaPipe, OpenCV
- **Database**: MongoDB
- **WebSockets**: Flask-SocketIO
- **Deployment**: Render

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/quantumgaze.git
cd quantumgaze
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your environment variables:
```
YOUTUBE_API_KEY=your_api_key
MONGODB_URI=your_mongodb_uri
```

5. Run the application:
```bash
python app.py
```

## Deployment

The application is configured for deployment on Render. The `render.yaml` file contains the necessary configuration for automatic deployment.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built by Ariful Hussain
- Special thanks to the MediaPipe team for their excellent hand tracking solution 