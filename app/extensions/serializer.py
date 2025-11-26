from itsdangerous import URLSafeTimedSerializer

s = None

def init_serializer(app):
    global s
    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])


def generate_token(email):
    # Usando uma salt específica para o token de e-mail para evitar colisões
    return s.dumps(email, salt='email-confirm-salt')


def confirm_token(token, expiration=3600):
    try:
        # Usando a mesma salt e tempo de expiração
        email = s.loads(token, salt='email-confirm-salt', max_age=expiration)
    except Exception:
        # É uma boa prática logar o erro, embora retorne None para o chamador
        # current_app.logger.debug(f"Falha na confirmação do token: {token}")
        return None
    return email