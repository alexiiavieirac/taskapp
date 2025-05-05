from datetime import datetime, timezone
from flask_login import UserMixin
from app.extensions.database import db
from app.models.connection import Conexao

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuario'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)

    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'), nullable=True)
    grupo_original_id = db.Column(db.Integer, db.ForeignKey('grupo.id'), nullable=True)

    avatar = db.Column(db.String(200), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    rede_social = db.Column(db.String(255), nullable=True)

    email_verificado = db.Column(db.Boolean, default=False)

    # Conexões de quem o usuário segue
    seguindo_conexoes = db.relationship(
        'Conexao',
        foreign_keys='Conexao.seguidor_id',
        back_populates='seguidor',
        lazy='dynamic'
    )

    # Conexões de quem segue o usuário
    seguidores_conexoes = db.relationship(
        'Conexao',
        foreign_keys='Conexao.seguido_id',
        back_populates='seguido',
        lazy='dynamic'
    )

    # Verifica se o usuário já segue outro
    def is_following(self, usuario):
        return self.seguindo_conexoes.filter(
            Conexao.seguido_id == usuario.id
        ).count() > 0
    

class PedidoSeguir(db.Model):
    __tablename__ = 'pedido_seguir'

    id = db.Column(db.Integer, primary_key=True)
    remetente_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False, index=True)
    destinatario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False, index=True)
    status = db.Column(db.String(20), default='pendente', index=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)

    visto = db.Column(db.Boolean, default=False)
    data_visto = db.Column(db.DateTime(), nullable=True)

    remetente = db.relationship('Usuario', foreign_keys=[remetente_id], backref='pedidos_enviados')
    destinatario = db.relationship('Usuario', foreign_keys=[destinatario_id], backref='pedidos_recebidos')