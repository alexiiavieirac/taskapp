# models/group.py

from datetime import datetime
from app.extensions import db
from sqlalchemy.orm import foreign # CORRIGIDO: Importar a função foreign de sqlalchemy.orm

# REMOVIDO: from app.models.usuario import Usuario  <-- Não importamos diretamente aqui para evitar circular import

class Grupo(db.Model):
    __tablename__ = 'grupo'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    proprietario_id = db.Column(db.Integer, nullable=True) # Apenas um INTEGER, sem db.ForeignKey aqui

    __table_args__ = (
        #db.UniqueConstraint('nome', name='uq_grupo_nome'),
    )

    # Relacionamento com o usuário proprietário do grupo (Grupo -> Usuario)
    # Grupo.proprietario_id é a FK que aponta para Usuario.id
    proprietario = db.relationship(
        'Usuario',
        # foreign_keys deve apontar para a coluna FK LOCAL (proprietario_id de Grupo)
        foreign_keys=[proprietario_id],
        # primaryjoin: explicitamente marca proprietario_id como a FK
        primaryjoin=lambda: foreign(Grupo.proprietario_id) == db.metadata.tables['usuario'].c.id,
        remote_side=lambda: [db.metadata.tables['usuario'].c.id],
        back_populates='grupos_proprietario'
    )

    # Relacionamento com usuários que pertencem a este grupo (Grupo -> Usuario)
    # Usuario.grupo_id é a FK que aponta para Grupo.id
    usuarios = db.relationship(
        'Usuario',
        # foreign_keys deve apontar para a coluna FK REMOTA (grupo_id de Usuario)
        foreign_keys=lambda: [db.metadata.tables['usuario'].c.grupo_id],
        # primaryjoin: explicitamente marca Usuario.grupo_id como a FK
        primaryjoin=lambda: Grupo.id == foreign(db.metadata.tables['usuario'].c.grupo_id),
        remote_side=lambda: [db.metadata.tables['usuario'].c.grupo_id],
        back_populates='grupo',
        lazy=True
    )

    # Relacionamento com usuários que pertenciam originalmente a este grupo (Grupo -> Usuario)
    # Usuario.grupo_original_id é a FK que aponta para Grupo.id
    grupo_original_usuarios = db.relationship(
        'Usuario',
        # foreign_keys deve apontar para a coluna FK REMOTA (grupo_original_id de Usuario)
        foreign_keys=lambda: [db.metadata.tables['usuario'].c.grupo_original_id],
        # primaryjoin: explicitamente marca Usuario.grupo_original_id como a FK
        primaryjoin=lambda: Grupo.id == foreign(db.metadata.tables['usuario'].c.grupo_original_id),
        remote_side=lambda: [db.metadata.tables['usuario'].c.grupo_original_id],
        back_populates='grupo_original',
        lazy=True
    )

    tarefas = db.relationship('Tarefa', backref='grupo', lazy=True)
    convites = db.relationship('ConviteGrupo', backref='grupo', lazy=True)
    pedidos = db.relationship('SolicitacaoGrupo', backref='grupo', lazy=True)


class ConviteGrupo(db.Model):
    __tablename__ = 'convite_grupo'

    id = db.Column(db.Integer, primary_key=True)
    email_convidado = db.Column(db.String(120), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)
    status = db.Column(db.String(20), default='pendente')
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)

    
class SolicitacaoGrupo(db.Model):
    __tablename__ = 'solicitacao_grupo'

    id = db.Column(db.Integer, primary_key=True)
    solicitante_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'), nullable=False)
    status = db.Column(db.String(20), default='pendente')

    visto = db.Column(db.Boolean, default=False)
    data_visto = db.Column(db.DateTime(), nullable=True)

    solicitante = db.relationship('Usuario', foreign_keys=[solicitante_id], backref='pedidos_grupo_enviados')
