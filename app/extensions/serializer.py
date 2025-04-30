from itsdangerous import URLSafeTimedSerializer

s = None

def init_serializer(app):
    app.config['serializer'] = URLSafeTimedSerializer(app.config['SECRET_KEY'])


def get_serializer(app):
    return app.config.get('serializer', None)