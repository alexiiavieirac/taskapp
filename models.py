from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

seguidores = db.Table('seguidores',
    db.Column('seguidor_id', db.Integer, db.ForeignKey('usuario.id')),
    db.Column('seguido_id', db.Integer, db.ForeignKey('usuario.id'))
)

class Grupo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    usuarios = db.relationship('Usuario', backref='grupo', lazy=True)
    tarefas = db.relationship("Tarefa", backref="grupo", lazy=True)

    __table_args__ = (
        db.UniqueConstraint('nome', name='uq_grupo_nome'),
    )


class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'), nullable=False)
    avatar = db.Column(db.String(200), nullable=True)  
    bio = db.Column(db.Text, nullable=True)  

    seguindo = db.relationship(
        'Usuario',
        secondary=seguidores,
        primaryjoin=(seguidores.c.seguidor_id == id),
        secondaryjoin=(seguidores.c.seguido_id == id),
        backref=db.backref('seguidores', lazy='dynamic'),
        lazy='dynamic'
    )


class ConviteGrupo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email_convidado = db.Column(db.String(120), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False)
    status = db.Column(db.String(20), default="pendente")  # pendente, aceito, expirado, etc.
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)

    grupo = db.relationship("Grupo", backref="convites")    


class PedidoGrupo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'), nullable=False)
    status = db.Column(db.String(20), default='pendente')  

    usuario = db.relationship('Usuario', backref='pedidos_grupo')
    grupo = db.relationship('Grupo', backref='pedidos')


class Conexao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seguidor_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    seguido_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)


class SolicitacaoGrupo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    solicitante_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'), nullable=False)
    status = db.Column(db.String(20), default="pendente") 


class HistoricoRanking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'), nullable=False)
    tarefas_concluidas = db.Column(db.Integer, nullable=False)
    semana = db.Column(db.String(10), nullable=False)  # Ex: '2025-W15'
    data_registro = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship('Usuario')
    grupo = db.relationship('Grupo')


class Tarefa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200), nullable=False)
    concluida = db.Column(db.Boolean, default=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    imagem = db.Column(db.String(200), nullable=True)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    pontos = db.Column(db.Integer, default=10)
    ativa = db.Column(db.Boolean, default=True)
    