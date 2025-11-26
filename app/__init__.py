import os
from flask import Flask
from dotenv import load_dotenv # Importado para carregar variáveis de ambiente

# Importando as funções de inicialização das extensões
from app.extensions.database import init_db # Importa a função init_db que inicializa db e migrate
from app.extensions.login_manager import init_login_manager # Importa a função init_login_manager
from app.extensions.mail import init_mail # Importa a função init_mail
from app.extensions.serializer import init_serializer # Importa a função init_serializer
from app.extensions.uploads import configure_uploads # Importa a função configure_uploads
from app.extensions.socketio import socketio # Importa a instância de socketio (e a função init_socketio se fosse usada)

# Importando utilitários
from app.utils.response_utils import setup_response_handlers

# Importando blueprints
from app.controllers.auth_controller import main_bp # Assumindo que main_bp é o único blueprint principal por enquanto

# Não precisamos mais importar 'db', 'login_manager', 'mail', 'socketio' como instâncias diretamente
# de '.extensions' se estamos usando as funções init_x(app).
# Também não precisamos de 'flask_migrate' aqui, pois init_db já cuida disso internamente.


def create_app():
    # 1. Carregar variáveis de ambiente o mais cedo possível
    load_dotenv() 

    app = Flask( __name__,
        template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
        static_folder=os.path.join(os.path.dirname(__file__), 'static')
    )
    
    # 2. Configurar a aplicação com variáveis de ambiente
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY', 'uma_chave_secreta_padrao'), # Sempre bom ter um fallback
        # Corrigido para usar SQLALCHEMY_DATABASE_URI como nome da variável de ambiente
        # para consistência com o que discutimos no .env (sqlite:///instance/site.db)
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI'), 
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    # 3. Inicializar extensões
    # A função init_mail(app) já configura e inicializa a extensão mail.
    # Não é necessário chamar 'mail.init_app(app)' novamente.
    init_mail(app) 
    
    configure_uploads(app)
    setup_response_handlers(app)
    
    # init_db(app) cuida da inicialização do db e do Flask-Migrate
    init_db(app) 
    
    # init_login_manager(app) cuida da inicialização do login_manager
    init_login_manager(app) 
    
    # SocketIO é inicializado e anexado ao app
    socketio.init_app(app) 
    # Não é necessário app.extensions['socketio'] = socketio; a instância global já é acessível.

    init_serializer(app) # Inicializa o serializador itsdangerous

    # 4. Registrar blueprints
    # Blueprints devem ser registrados fora do app_context() para que sejam globais.
    app.register_blueprint(main_bp) # O main_bp já está importado de auth_controller

    # Se você tiver outros blueprints (ex: 'conexao_bp' ou 'admin_bp'), registre-os aqui:
    # from app.controllers.conexao_controller import conexao_bp # Exemplo
    # app.register_blueprint(conexao_bp) # Exemplo
    
    return app