from flask import session

def setup_response_handlers(app):
    @app.after_request
    def modify_response(response):
        # Evita cache
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

        # Limpa os flashes
        session.pop('_flashes', None)

        return response