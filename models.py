from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timezone

db = SQLAlchemy()

# Tabela de associação para seguidores
seguidores = db.Table(
    'seguidores',
    db.Column('seguidor_id', db.Integer, db.ForeignKey('usuario.id')),
    db.Column('seguido_id', db.Integer, db.ForeignKey('usuario.id'))
)

# =============================================
# MODELO: Grupo
# =============================================
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


# =============================================
# MODELO: Usuário
# =============================================
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


# =============================================
# MODELO: Conexão entre usuários (seguidores/seguidos)
# =============================================
class Conexao(db.Model):
    __tablename__ = 'conexao'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    seguidor_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    seguido_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)

    seguidor = db.relationship('Usuario', foreign_keys=[seguidor_id], back_populates='seguindo_conexoes')
    seguido = db.relationship('Usuario', foreign_keys=[seguido_id], back_populates='seguidores_conexoes')

    visto = db.Column(db.Boolean, default=False)
    data_visto = db.Column(db.DateTime(), nullable=True)

    __table_args__ = (
        db.Index('idx_seguidor_seguido', 'seguidor_id', 'seguido_id'),
        db.UniqueConstraint('seguidor_id', 'seguido_id', name='uq_seguidor_seguido')
    )


# =============================================
# MODELO: Pedido de seguir outro usuário
# =============================================
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


# =============================================
# MODELO: Convite de grupo enviado por e-mail
# =============================================
class ConviteGrupo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email_convidado = db.Column(db.String(120), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False)
    status = db.Column(db.String(20), default='pendente')
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)


# =============================================
# MODELO: Solicitação genérica para grupo
# =============================================
class SolicitacaoGrupo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    solicitante_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'), nullable=False)
    status = db.Column(db.String(20), default='pendente')

    visto = db.Column(db.Boolean, default=False)
    data_visto = db.Column(db.DateTime(), nullable=True)

    usuario = db.relationship('Usuario', backref='pedidos_grupo')

# =============================================
# MODELO: Histórico de ranking semanal do grupo
# =============================================
class HistoricoRanking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'), nullable=False)
    tarefas_concluidas = db.Column(db.Integer, nullable=False)
    semana = db.Column(db.String(10), nullable=False)  # Ex: '2025-W15'
    data_registro = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship('Usuario')
    grupo = db.relationship('Grupo')


# =============================================
# MODELO: Tarefa Padrão (modelo reutilizável)
# =============================================
class TarefaPadrao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200), nullable=False)
    imagem = db.Column(db.String(200))


# =============================================
# MODELO: Tarefa (criada por um usuário para o grupo)
# =============================================
class Tarefa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(120), nullable=False)
    imagem = db.Column(db.String(120), nullable=True)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'))

    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))  # Criador
    concluida_por = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)  # Concluidor

    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_conclusao = db.Column(db.DateTime, nullable=True)
    concluida = db.Column(db.Boolean, default=False)
    ativa = db.Column(db.Boolean, default=True)

    criador = db.relationship('Usuario', foreign_keys=[usuario_id])
    concluidor = db.relationship('Usuario', foreign_keys=[concluida_por])