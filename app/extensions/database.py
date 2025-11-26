from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def init_db(app):
    db.init_app(app) # <--- ADICIONADA ESTA LINHA CRÍTICA
    migrate.init_app(app, db)

    # Recomendação: db.create_all() geralmente é executado uma única vez para criar o esquema inicial
    # ou para fins de teste. Em ambientes de produção, as migrações (flask db upgrade)
    # são usadas para gerenciar as mudanças no esquema do banco de dados.
    # Se você está usando Flask-Migrate, a criação de tabelas deve ser feita via 'flask db upgrade'.
    # Removendo a chamada automática para evitar sobrescrita ou comportamentos inesperados em produção.
    # with app.app_context():
    #    db.create_all()