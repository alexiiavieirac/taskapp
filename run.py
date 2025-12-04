# run.py

import os
import sys
import eventlet # Certifique-se de que eventlet está instalado
from app import create_app # Cria o aplicativo Flask
from app.extensions.database import db # Se db estiver em app/extensions/database
from flask_migrate import Migrate
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configura o path para que Flask encontre os módulos do app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

# Importar o objeto socketio de suas extensões
from app.extensions.socketio import socketio

# Importar todos os seus modelos, incluindo o novo ChatMessage
# Se você tem app/models/__init__.py, importe * assim:
from app.models import * # Isso importará Usuario, Tarefa, Grupo, ChatMessage, etc.

# Se você não tem um app/models/__init__.py, importe ChatMessage assim:
# from app.models.chat_message import ChatMessage

# ... outros imports de modelos (se você não usa 'from app.models import *')
# from app.models.usuario import Usuario
# from app.models.task import Tarefa
# from app.models.group import Grupo
# from app.models.connection import Conexao
# from app.models.history import Historico
# from app.models.solicitacao_grupo import SolicitacaoGrupo # Assumindo que você tem isso
# from app.models.pedido_seguir import PedidoSeguir # Assumindo que você tem isso
# from app.models.convite_grupo import ConviteGrupo # Assumindo que você tem isso


app = create_app()

# Inicializa o Flask-Migrate
migrate = Migrate(app, db) # Certifique-se que 'db' vem de app.extensions.database ou similar

# ... (Seu código existente para FLASK_MAIL_CONFIGURATION) ...

# Contexto de shell para Flask-Migrate e outras operações
@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'Usuario': Usuario,
        'Tarefa': Tarefa,
        'Grupo': Grupo,
        'Conexao': Conexao,
        #'Historico': Historico, # Se você tiver este modelo
        'SolicitacaoGrupo': SolicitacaoGrupo,
        'PedidoSeguir': PedidoSeguir,
        'ConviteGrupo': ConviteGrupo,
        'ChatMessage': ChatMessage # --- ADICIONE ESTA LINHA ---
    }

if __name__ == '__main__':
    # --- IMPORTANTE: SUBSTITUA app.run() por socketio.run() ---
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
    # -----------------------------------------------