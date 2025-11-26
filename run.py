# run.py
import os
import sys
import eventlet

# eventlet.monkey_patch() deve ser chamado antes de qualquer importação de módulos que ele precisa corrigir
eventlet.monkey_patch()

from pathlib import Path
# from dotenv import load_dotenv # REMOVIDO: load_dotenv() agora é chamado dentro de create_app() em app/__init__.py
from app import create_app
from app.extensions.socketio import socketio # socketio é importado aqui para que o servidor possa usá-lo

sys.path.insert(0, str(Path(__file__).parent))

# load_dotenv() # REMOVIDO: load_dotenv() agora é chamado dentro de create_app() em app/__init__.py

# --- LINHAS DE DEPURACAO REMOVIDAS ---
# Estas linhas de depuração são úteis, mas devem ser removidas em um ambiente de produção
# e geralmente não são necessárias aqui, pois create_app() já garante que o ambiente seja carregado.
# print(f"DEBUG: SQLALCHEMY_DATABASE_URI carregado do .env: {os.getenv('SQLALCHEMY_DATABASE_URI')}")
# print(f"DEBUG: Caminho atual: {os.getcwd()}")
# --- FIM DAS LINHAS DE DEPURACAO REMOVIDAS ---

# A instância da aplicação Flask é criada chamando create_app().
# create_app() já lida com o carregamento das variáveis de ambiente e inicialização das extensões.
app = create_app()

if __name__ == "__main__":
    # Para usar o Flask-SocketIO com eventlet, você deve usar o servidor do SocketIO
    # em vez do servidor de desenvolvimento padrão do Flask.
    # O debug=True ainda funciona, e o allow_unsafe_werkzeug=True é necessário
    # quando você não está em ambiente de produção para depuração.
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True, host='0.0.0.0', port=5000)
