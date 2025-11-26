from app.extensions import db

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