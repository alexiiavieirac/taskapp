from flask_socketio import SocketIO

socketio = SocketIO(async_mode="eventlet")

def init_socketio(app):
    socketio.init_app(app)