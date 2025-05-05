from itsdangerous import URLSafeTimedSerializer

serializer = None

def init_serializer(app):
    global serializer
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])


def generate_token(email):
    return serializer.dumps(email, salt='email-confirm-salt')


def confirm_token(token, expiration=3600):
    try:
        email = serializer.loads(token, salt='email-confirm-salt', max_age=expiration)
    except Exception:
        return None
    return email