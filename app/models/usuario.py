from datetime import datetime, timezone
from flask_login import UserMixin
# from app.extensions import serializer # REMOVIDO: Funções de serializer são chamadas diretamente do módulo
from app.extensions import db # Simplificado import para consistência
from app.models.connection import Conexao
# from app.extensions.serializer import s as serializer # Importa 's' se realmente precisar acessar o objeto Serializer diretamente,
                                                       # mas as funções generate_token e confirm_token já estão em escopo global no auth_controller.

# Se as funções de serialização forem usadas fora do auth_controller (ex: em outros modelos ou utilitários)
# e você quiser manter a sintaxe Usuario.gerar_token_confirmacao(), então
# seria mais apropriado ter um módulo utilitário para isso, ou reimportar as funções.
# Para manter a centralização da lógica de token no módulo serializer, vamos remover as duplicadas aqui.
from app.extensions.serializer import generate_token, confirm_token as confirm_token_ext # Renomeado para evitar conflito com método

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

    # Relacionamento para grupos que o usuário é proprietário
    grupos_proprietario = db.relationship(
        'Grupo', 
        foreign_keys='Grupo.proprietario_id', 
        back_populates='proprietario', 
        lazy=True
    )

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

    # Relacionamento para tarefas criadas pelo usuário
    tarefas_criadas = db.relationship(
        'Tarefa',
        foreign_keys='Tarefa.usuario_id',
        back_populates='criador',
        lazy='dynamic'
    )

    # Relacionamento para tarefas concluídas pelo usuário
    tarefas_concluidas_por = db.relationship(
        'Tarefa',
        foreign_keys='Tarefa.concluida_por',
        back_populates='concluidor',
        lazy='dynamic'
    )

    # Verifica se o usuário já segue outro
    def is_following(self, usuario):
        return self.seguindo_conexoes.filter(
            Conexao.seguido_id == usuario.id
        ).count() > 0
    
    # 🔑 Gerar token de verificação de e-mail - REMOVIDO: Usar app.extensions.serializer.generate_token
    # def gerar_token_confirmacao(self):
    #     return serializer.dumps(self.email, salt='confirm-email')

    # ✅ Confirmar token e retornar e-mail, ou None se inválido/expirado - REMOVIDO: Usar app.extensions.serializer.confirm_token
    # @staticmethod
    # def confirmar_token(token, expiracao=3600):
    #     try:
    #         email = serializer.loads(token, salt='confirm-email', max_age=expiracao)
    #     except Exception:
    #         return None
    #     return email


class PedidoSeguir(db.Model):
    __tablename__ = 'pedido_seguir'

    id = db.Column(db.Integer, primary_key=True)
    remetente_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False, index=True)
    destinatario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False, index=True)
    status = db.Column(db.String(20), default='pendente', index=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)

    visto = db.Column(db.Boolean, default=False)
    data_visto = db.Column(db.DateTime(), nullable=True)

    remetente = db.relationship('Usuario', foreign_keys=[remetente_id], backref='pedidos_enviados_seguir') # backref mais específico
    destinatario = db.relationship('Usuario', foreign_keys=[destinatario_id], backref='pedidos_recebidos_seguir') # backref mais específico