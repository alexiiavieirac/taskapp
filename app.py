import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from app import create_app
from app.extensions.socketio import socketio

sys.path.insert(0, str(Path(__file__).parent))

load_dotenv()

app = create_app()

if __name__ == "__main__":
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    port = int(os.getenv('FLASK_PORT', 5000))

    socketio.run(app, debug=debug_mode, port=port)
