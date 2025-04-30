from app.models import Tarefa
from app.extensions import db

def adicionar_tarefa(descricao, grupo_id, usuario_id):
    existe = Tarefa.query.filter_by(
        descricao=descricao,
        grupo_id=grupo_id,
        ativa=True
    ).first()
    if not existe:
        nova = Tarefa(
            descricao=descricao,
            usuario_id=usuario_id,
            grupo_id=grupo_id,
            ativa=True,
            concluida=False
        )
        db.session.add(nova)