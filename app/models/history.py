from datetime import datetime
from app.extensions import db

class HistoricoRanking(db.Model):
    __tablename__ = 'historico_ranking' # Adicionado __tablename__ para consistência

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'), nullable=False)
    tarefas_concluidas = db.Column(db.Integer, nullable=False)
    semana = db.Column(db.String(10), nullable=False)  # Ex: '2025-W15'
    data_registro = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship('Usuario')
    grupo = db.relationship('Grupo')