from datetime import datetime
from app.models import Tarefa
from app.extensions import db

def adicionar_tarefa(descricao, grupo_id, usuario_id, data_planejada=None):
    if data_planejada is None:
        data_planejada = datetime.today()

    existe = Tarefa.query.filter_by(
        descricao=descricao,
        grupo_id=grupo_id,
        data_planejada=data_planejada,
        ativa=True
    ).first()
 
    if not existe:
        nova = Tarefa(
            descricao=descricao,
            usuario_id=usuario_id,
            grupo_id=grupo_id,
            data_planejada=data_planejada,
            ativa=True,
            concluida=False
        )
        db.session.add(nova)
        db.session.commit()