from flask_login import LoginManager
from app.models.usuario import Usuario
from app.extensions import db

login_manager = LoginManager()

def init_login_manager(app):
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(Usuario, int(user_id))
        except (ValueError, TypeError):
            # É uma boa prática logar este erro para depuração
            app.logger.warning(f"Tentativa de carregar usuário com ID inválido: {user_id}")
            return None