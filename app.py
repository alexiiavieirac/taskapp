import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from app import create_app
from extensions import socketio

sys.path.insert(0, str(Path(__file__).parent))

load_dotenv()

app = create_app()

if __name__ == "__main__":
    socketio.run(app, debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true', 
                 port=int(os.getenv('FLASK_PORT', 5000)), use_reloader=False)