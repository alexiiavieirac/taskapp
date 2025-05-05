import os
import sys
import eventlet

eventlet.monkey_patch()

from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

# Agora sim, pode importar o app
from app import create_app
from app.extensions.socketio import socketio

app = create_app()
