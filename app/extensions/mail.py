import os
from flask_mail import Mail
from dotenv import load_dotenv

load_dotenv()
mail = Mail()

def init_mail(app):
    mail.init_app(app)
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = int(os.getenv("MAIL_PORT"))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', True) 
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', False) 
    app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
    app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MAIL_DEFAULT_SENDER")
