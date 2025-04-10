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


class Conexao(db.Model):
    seguidor_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), primary_key=True)
    seguido_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), primary_key=True)
    
    seguidor = db.relationship('Usuario', foreign_keys=[seguidor_id], back_populates='seguindo_conexoes')
    seguido = db.relationship('Usuario', foreign_keys=[seguido_id], back_populates='seguindo_conexoes')


class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuario'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'), nullable=False)
    avatar = db.Column(db.String(200), nullable=True)
    bio = db.Column(db.Text, nullable=True)  
    rede_social = db.Column(db.String(255), nullable=True)

    # Relacionamento com a tabela de seguidores (Conexões)
    seguindo_conexoes = db.relationship(
        'Conexao',
        foreign_keys=[Conexao.seguidor_id],
        back_populates='seguidor',
        lazy='dynamic'
    )

    # Relacionamento com os seguidores (Conexões onde o usuario é o "seguido")
    seguidores_conexoes = db.relationship(
        'Conexao',
        foreign_keys=[Conexao.seguido_id],
        back_populates='seguido',
        lazy='dynamic'
    )

    def is_following(self, usuario):
        return self.seguindo_conexoes.filter(Conexao.seguido_id == usuario.id).count() > 0


class PedidoSeguir(db.Model):
    __tablename__ = 'pedido_seguir'

    id = db.Column(db.Integer, primary_key=True)
    remetente_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    destinatario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    status = db.Column(db.String(20), default="pendente")

    remetente = db.relationship("Usuario", foreign_keys=[remetente_id], backref="pedidos_enviados")
    destinatario = db.relationship("Usuario", foreign_keys=[destinatario_id], backref="pedidos_recebidos")


class ConviteGrupo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email_convidado = db.Column(db.String(120), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False)
    status = db.Column(db.String(20), default="pendente")
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)

    grupo = db.relationship("Grupo", backref="convites")   


class PedidoGrupo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'), nullable=False)
    status = db.Column(db.String(20), default='pendente')  

    usuario = db.relationship('Usuario', backref='pedidos_grupo')
    grupo = db.relationship('Grupo', backref='pedidos')


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


class TarefaPadrao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200), nullable=False)
    imagem = db.Column(db.String(200))


class Tarefa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(120))
    imagem = db.Column(db.String(120), nullable=True)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'))

    data_conclusao = db.Column(db.DateTime, nullable=True)

    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))  # quem criou
    concluida_por = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)  # quem concluiu

    criador = db.relationship("Usuario", foreign_keys=[usuario_id])
    concluidor = db.relationship("Usuario", foreign_keys=[concluida_por])

    concluida = db.Column(db.Boolean, default=False)
    ativa = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)