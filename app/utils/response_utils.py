from flask import session # A importação de 'session' não é usada aqui, pode ser removida se não for necessária em outro lugar
from datetime import datetime

def setup_response_handlers(app):
    @app.after_request
    def modify_response(response):
        # Desabilitar cache para páginas que podem conter dados sensíveis ou em constante mudança
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0' # Adicionado max-age=0
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0' # Para compatibilidade com HTTP/1.0
        # Definir a data de expiração para o passado
        response.headers['Last-Modified'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT') # Para indicar que o conteúdo é "fresco"

        return response