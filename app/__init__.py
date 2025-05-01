import os
from flask import Flask
from app.extensions.serializer import init_serializer
from app.extensions.uploads import configure_uploads
from app.utils.response_utils import setup_response_handlers
from .extensions import db, login_manager, mail, socketio
from app.extensions.database import init_db
from app.extensions.login_manager import init_login_manager
from app.controllers.auth_controller import main_bp

def create_app():
    app = Flask( __name__,
        template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
        static_folder=os.path.join(os.path.dirname(__file__), 'static')
    )
    
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY'),
        SQLALCHEMY_DATABASE_URI=os.getenv('MYSQL_URL'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    #app.register_blueprint(conexao_bp)
    #app.register_blueprint(auth_bp)

    configure_uploads(app)

    setup_response_handlers(app)
    
    db.init_app(app)
    login_manager.init_app(app)
    init_login_manager(app)
    mail.init_app(app)
    socketio.init_app(app)

    app.extensions['socketio'] = socketio

    init_db(app)
    init_serializer(app)

    with app.app_context():
        app.register_blueprint(main_bp)
    
    return app