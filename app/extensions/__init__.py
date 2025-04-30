from .database import db
from .login_manager import login_manager
from .mail import mail
from .socketio import socketio
from .serializer import s

__all__ = ['db', 'login_manager', 'mail', 'socketio', 's']