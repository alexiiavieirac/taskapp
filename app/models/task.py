from datetime import datetime
from app.extensions import db

# Removido o modelo TarefaPadrao, pois sua funcionalidade foi substituída
# por uma lista de constantes em app/constants.py, conforme análises anteriores.
# Se houver uma necessidade futura de persistir tarefas padrão no banco de dados,
# este modelo pode ser reintegrado.
# class TarefaPadrao(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     descricao = db.Column(db.String(200), nullable=False)
#     imagem = db.Column(db.String(200))


class Tarefa(db.Model):
    __tablename__ = 'tarefa' # Adicionado __tablename__ para consistência

    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(120), nullable=False)
    imagem = db.Column(db.String(120), nullable=True)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'))

    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id')) 
    concluida_por = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True) 

    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_conclusao = db.Column(db.DateTime, nullable=True)
    concluida = db.Column(db.Boolean, default=False)
    ativa = db.Column(db.Boolean, default=True)

    criador = db.relationship('Usuario', foreign_keys=[usuario_id], back_populates='tarefas_criadas')
    concluidor = db.relationship('Usuario', foreign_keys=[concluida_por], back_populates='tarefas_concluidas_por')