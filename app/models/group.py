from datetime import datetime
from app.extensions import db

class Grupo(db.Model):
    __tablename__ = 'grupo' # Adicionado __tablename__ para consistência

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    proprietario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True) # Adicionado proprietario_id

    # Relacionamento com o usuário proprietário do grupo
    proprietario = db.relationship('Usuario', foreign_keys=[proprietario_id], back_populates='grupos_proprietario')


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


class ConviteGrupo(db.Model):
    __tablename__ = 'convite_grupo' # Adicionado __tablename__ para consistência

    id = db.Column(db.Integer, primary_key=True)
    email_convidado = db.Column(db.String(120), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False) # Aumentado o tamanho para tokens itsdangerous
    status = db.Column(db.String(20), default='pendente')
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)

    
class SolicitacaoGrupo(db.Model):
    __tablename__ = 'solicitacao_grupo' # Adicionado __tablename__ para consistência

    id = db.Column(db.Integer, primary_key=True)
    solicitante_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'), nullable=False)
    status = db.Column(db.String(20), default='pendente')

    visto = db.Column(db.Boolean, default=False)
    data_visto = db.Column(db.DateTime(), nullable=True)

    # Corrigido o relacionamento 'usuario' para apontar para 'solicitante_id'
    solicitante = db.relationship('Usuario', foreign_keys=[solicitante_id], backref='pedidos_grupo_enviados')
    # O backref original 'pedidos_grupo' em Usuario pode ser usado por este relacionamento
    # ou se for para pedidos recebidos. Vamos renomear para evitar ambiguidades.