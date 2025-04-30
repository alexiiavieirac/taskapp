from functools import wraps
from flask import redirect, url_for
from flask_login import current_user

def grupo_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.grupo_id is None:
            return redirect(url_for('criar_grupo'))
        return f(*args, **kwargs)
    return decorated_function