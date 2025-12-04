# app/models/chat_message.py

from datetime import datetime
from app.extensions import db # Importe a instância do seu SQLAlchemy

class ChatMessage(db.Model):
    __tablename__ = 'chat_message' # Explicitamente defina o nome da tabela

    id = db.Column(db.Integer, primary_key=True)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relacionamentos
    # Não precisa do backref aqui se já está definido nos outros modelos ou será acessado por query
    # grupo = db.relationship('Grupo', backref=db.backref('chat_messages', lazy=True))
    # usuario = db.relationship('Usuario', backref=db.backref('sent_messages', lazy=True))

    # É mais comum definir os relacionamentos no modelo "pai" se ele precisar acessar os "filhos"
    # No seu caso, você provavelmente já tem algo como:
    # No Usuario.py: chat_messages = db.relationship('ChatMessage', backref='usuario', lazy=True)
    # No Group.py: chat_messages = db.relationship('ChatMessage', backref='grupo', lazy=True)
    # Se você já tem isso, pode remover as linhas comentadas acima (grupo = db.relationship...)

    def __repr__(self):
        # Para evitar erros de carregamento recursivo durante o __repr__,
        # especialmente se os relacionamentos não estiverem carregados,
        # é melhor acessar apenas as IDs aqui.
        return f'<ChatMessage {self.id}: {self.message[:20]} from user {self.usuario_id} in group {self.grupo_id}>'
