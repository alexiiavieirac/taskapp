import os
from flask import Flask
from dotenv import load_dotenv

# Importando as funções de inicialização das extensões
from app.extensions.database import init_db
from app.extensions.login_manager import init_login_manager
from app.extensions.mail import init_mail
from app.extensions.serializer import init_serializer
from app.extensions.uploads import configure_uploads
from app.extensions.socketio import socketio

# Importando utilitários
from app.utils.response_utils import setup_response_handlers

# Importando blueprints
from app.controllers.auth_controller import main_bp


def create_app():
    # 1. Carregar variáveis de ambiente o mais cedo possível
    load_dotenv()

    app = Flask( __name__,
        template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
        static_folder=os.path.join(os.path.dirname(__file__), 'static')
    )

    # 2. Configurar a aplicação com variáveis de ambiente
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY', 'uma_chave_secreta_padrao'),
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,

        # === ADICIONE AS CONFIGURAÇÕES DE E-MAIL AQUI ===
        MAIL_SERVER=os.getenv('MAIL_SERVER'),
        MAIL_PORT=int(os.getenv('MAIL_PORT', 587)), # Converte para int
        MAIL_USE_TLS=os.getenv('MAIL_USE_TLS', 'False').lower() in ('true', '1'), # Converte string para booleano
        MAIL_USERNAME=os.getenv('MAIL_USERNAME'),
        MAIL_PASSWORD=os.getenv('MAIL_PASSWORD'),
        MAIL_DEFAULT_SENDER=os.getenv('MAIL_DEFAULT_SENDER') # Se você tiver um DEFAULT_SENDER no .env
        # =================================================
    )

    print(f"\n--- DEBUG FLASK-MAIL CONFIGURATION ---")
    print(f"MAIL_SERVER: {app.config.get('MAIL_SERVER')}")
    print(f"MAIL_PORT: {app.config.get('MAIL_PORT')}")
    print(f"MAIL_USE_TLS: {app.config.get('MAIL_USE_TLS')}")
    print(f"MAIL_USERNAME: {app.config.get('MAIL_USERNAME')}")
    # ATENÇÃO: Nunca imprima senhas em um ambiente de produção.
    # Estamos fazendo isso APENAS para depuração local.
    print(f"MAIL_PASSWORD (primeiros 4 chars): {str(app.config.get('MAIL_PASSWORD'))[:4]}****")
    print(f"MAIL_DEFAULT_SENDER: {app.config.get('MAIL_DEFAULT_SENDER')}")
    print(f"--- FIM DO DEBUG ---\n")

    # 3. Inicializar extensões
    init_mail(app)

    configure_uploads(app)
    setup_response_handlers(app)

    init_db(app)

    init_login_manager(app)

    socketio.init_app(app)

    init_serializer(app)

    # 4. Registrar blueprints
    app.register_blueprint(main_bp)

    return app