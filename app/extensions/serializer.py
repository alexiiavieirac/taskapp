from itsdangerous import Serializer, URLSafeTimedSerializer
import app

s = None

def init_serializer(app):
    global s
    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])


def generate_token(email, expiratation=3600):
    s = Serializer(app.config['SECRET_KEY'], expires_in=expiratation)
    return s.dumps({'email': email}).decode('utf-8')


def confirm_token(token, expiration=3600):
    s = Serializer(app.config['SECRET_KEY'])
    try:
        email = s.loads(token)['email']
    except Exception:
        return None
    return email