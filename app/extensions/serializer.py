from itsdangerous import URLSafeTimedSerializer

s = None

def init_serializer(app):
    global s
    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])


def generate_token(email):
    return s.dumps(email, salt='email-confirm-salt')


def confirm_token(token, expiration=3600):
    try:
        email = s.loads(token, salt='email-confirm-salt', max_age=expiration)
    except Exception:
        return None
    return email