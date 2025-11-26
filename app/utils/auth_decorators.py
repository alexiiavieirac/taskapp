from functools import wraps
from flask import redirect, url_for, flash # Adicionado 'flash'
from flask_login import current_user

def grupo_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.grupo_id is None:
            flash("Você precisa estar em um grupo para acessar esta página.", "warning") # Adicionado feedback ao usuário
            return redirect(url_for('main.criar_grupo')) # Alterado para main.criar_grupo, conforme o blueprint
        return f(*args, **kwargs)
    return decorated_function