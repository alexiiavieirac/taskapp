from app.models import Tarefa
from app.extensions import db
from datetime import datetime, timezone # Adicionado import para datetime e timezone

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
            concluida=False,
            data_criacao=datetime.now(timezone.utc) # Adicionado data_criacao explícita
        )
        db.session.add(nova)
        # db.session.commit() # Não fazer commit aqui, deixar o caller da função fazer
    # else:
        # print(f"DEBUG: Tarefa '{descricao}' já existe para o grupo {grupo_id}, não adicionada novamente.")