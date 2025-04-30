from datetime import datetime
from app.extensions import db

class Grupo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)

    usuarios = db.relationship(
        'Usuario', 
        backref='grupo', 
        lazy=True,
        foreign_keys='Usuario.grupo_id'

    )

    grupo_original_usuarios = db.relationship( 
        'Usuario',
        backref='grupo_original',
        lazy=True,
        foreign_keys='Usuario.grupo_original_id'
    )

    tarefas = db.relationship('Tarefa', backref='grupo', lazy=True)
    convites = db.relationship('ConviteGrupo', backref='grupo', lazy=True)
    pedidos = db.relationship('SolicitacaoGrupo', backref='grupo', lazy=True)

    __table_args__ = (
        db.UniqueConstraint('nome', name='uq_grupo_nome'),
    )


class ConviteGrupo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email_convidado = db.Column(db.String(120), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False)
    status = db.Column(db.String(20), default='pendente')
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)
class SolicitacaoGrupo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    solicitante_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'), nullable=False)
    status = db.Column(db.String(20), default='pendente')

    visto = db.Column(db.Boolean, default=False)
    data_visto = db.Column(db.DateTime(), nullable=True)

    usuario = db.relationship('Usuario', backref='pedidos_grupo')