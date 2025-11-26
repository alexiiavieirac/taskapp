import os
from flask_mail import Mail
# from dotenv import load_dotenv # REMOVIDO: load_dotenv() deve ser chamado apenas uma vez em app/__init__.py

# load_dotenv() # REMOVIDO: load_dotenv() deve ser chamado apenas uma vez em app/__init__.py
mail = Mail()

def init_mail(app):
    mail.init_app(app)
    # Adicionado: MAIL_SERVER agora é configurável via variável de ambiente
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com') # Default para gmail
    
    mail_port = os.getenv("MAIL_PORT", "587")  # Usar 587 como valor padrão
    app.config['MAIL_PORT'] = int(mail_port)    
    
    # Correção: Converter string de variável de ambiente para booleano
    # os.getenv retorna string, que é sempre True em contexto booleano.
    # Devemos comparar com "True" explicitamente.
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
    
    app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
    app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MAIL_DEFAULT_SENDER")
