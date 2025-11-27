# models/usuario.py

from datetime import datetime, timezone
from flask_login import UserMixin
from app.extensions import db
from sqlalchemy.orm import foreign # CORRIGIDO: Importar a função foreign de sqlalchemy.orm

from app.models.connection import Conexao # Verifique o caminho correto para Conexao
from app.extensions.serializer import generate_token, confirm_token as confirm_token_ext
# REMOVIDO: from app.models.group import Grupo  <-- Não importamos diretamente aqui para evitar circular import

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuario'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)

    grupo_id = db.Column(db.Integer, nullable=True)
    grupo_original_id = db.Column(db.Integer, nullable=True)

    avatar = db.Column(db.String(200), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    rede_social = db.Column(db.String(255), nullable=True)

    email_verificado = db.Column(db.Boolean, default=False)

    # Relacionamento para grupos que o usuário é proprietário (Usuario -> Grupo)
    # Grupo.proprietario_id é a FK que aponta para Usuario.id
    grupos_proprietario = db.relationship(
        'Grupo',
        back_populates='proprietario',
        # foreign_keys deve apontar para a coluna FK REMOTA (proprietario_id de Grupo)
        foreign_keys=lambda: [db.metadata.tables['grupo'].c.proprietario_id],
        # primaryjoin: explicitamente marca Grupo.proprietario_id como a FK
        primaryjoin=lambda: Usuario.id == foreign(db.metadata.tables['grupo'].c.proprietario_id),
        remote_side=lambda: [db.metadata.tables['grupo'].c.proprietario_id]
    )

    # Relacionamento com o grupo ao qual o usuário pertence (Usuario -> Grupo)
    # Usuario.grupo_id é a FK que aponta para Grupo.id
    grupo = db.relationship(
        'Grupo',
        # foreign_keys deve apontar para a coluna FK LOCAL (grupo_id de Usuario)
        foreign_keys=[grupo_id],
        # primaryjoin: explicitamente marca Usuario.grupo_id como a FK
        primaryjoin=lambda: foreign(Usuario.grupo_id) == db.metadata.tables['grupo'].c.id,
        remote_side=lambda: [db.metadata.tables['grupo'].c.id],
        back_populates='usuarios'
    )

    # Relacionamento com o grupo original ao qual o usuário pertencia (Usuario -> Grupo)
    # Usuario.grupo_original_id é a FK que aponta para Grupo.id
    grupo_original = db.relationship(
        'Grupo',
        # foreign_keys deve apontar para a coluna FK LOCAL (grupo_original_id de Usuario)
        foreign_keys=[grupo_original_id],
        # primaryjoin: explicitamente marca Usuario.grupo_original_id como a FK
        primaryjoin=lambda: foreign(Usuario.grupo_original_id) == db.metadata.tables['grupo'].c.id,
        remote_side=lambda: [db.metadata.tables['grupo'].c.id],
        back_populates='grupo_original_usuarios'
    )

    seguindo_conexoes = db.relationship(
        'Conexao',
        foreign_keys='Conexao.seguidor_id',
        back_populates='seguidor',
        lazy='dynamic'
    )

    seguidores_conexoes = db.relationship(
        'Conexao',
        foreign_keys='Conexao.seguido_id',
        back_populates='seguido',
        lazy='dynamic'
    )

    tarefas_criadas = db.relationship(
        'Tarefa',
        foreign_keys='Tarefa.usuario_id',
        back_populates='criador',
        lazy='dynamic'
    )

    tarefas_concluidas_por = db.relationship(
        'Tarefa',
        foreign_keys='Tarefa.concluida_por',
        back_populates='concluidor',
        lazy='dynamic'
    )

    def is_following(self, usuario):
        return self.seguindo_conexoes.filter(
            Conexao.seguido_id == usuario.id
        ).count() > 0

    def gerar_token_confirmacao(self, expiration=3600):
        return generate_token(self.id, expiration)

    def confirmar_token(token):
        return confirm_token_ext(token)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.senha, password)


class PedidoSeguir(db.Model):
    __tablename__ = 'pedido_seguir'

    id = db.Column(db.Integer, primary_key=True)
    remetente_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False, index=True)
    destinatario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False, index=True)
    status = db.Column(db.String(20), default='pendente', index=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)

    visto = db.Column(db.Boolean, default=False)
    data_visto = db.Column(db.DateTime(), nullable=True)

    remetente = db.relationship('Usuario', foreign_keys=[remetente_id], backref='pedidos_enviados_seguir')
    destinatario = db.relationship('Usuario', foreign_keys=[destinatario_id], backref='pedidos_recebidos_seguir')