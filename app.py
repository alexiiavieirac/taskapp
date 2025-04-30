import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from app import create_app

sys.path.insert(0, str(Path(__file__).parent))

load_dotenv()

app = create_app()

if __name__ == "__main__":
    socketio = app.extensions.get('socketio')
    if socketio:
        socketio.run(app, debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true', port=int(os.getenv('FLASK_PORT', 5000)))
    else:
        app.run(debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true', port=int(os.getenv('FLASK_PORT', 5000)))