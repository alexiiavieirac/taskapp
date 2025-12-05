# app/utils/task_service.py
from app.models import Tarefa
from app.extensions import db
from datetime import datetime, timezone, date # Importe 'date' para comparação de datas
from sqlalchemy import func # Importe 'func' para usar funções SQL como DATE()

def adicionar_tarefa(descricao, grupo_id, usuario_id):
    # Obtém a data atual em UTC (apenas a parte da data)
    today_utc = datetime.now(timezone.utc).date()

    # Verifica se a tarefa já existe HOJE para este grupo e está ativa
    existe = Tarefa.query.filter(
        Tarefa.descricao == descricao,
        Tarefa.grupo_id == grupo_id,
        Tarefa.ativa == True,
        # Filtra a data de criação para ser EXATAMENTE a data de hoje
        func.date(Tarefa.data_criacao) == today_utc
    ).first()
    
    if not existe:
        nova = Tarefa(
            descricao=descricao,
            usuario_id=usuario_id,
            grupo_id=grupo_id,
            ativa=True,
            concluida=False,
            data_criacao=datetime.now(timezone.utc) # A data de criação será a de agora (hoje)
        )
        db.session.add(nova)
        # db.session.commit() # Não fazer commit aqui, deixar o caller da função fazer
    # else:
        # Se desejar adicionar logs ou feedback quando a tarefa já existe para HOJE:
        # print(f"DEBUG: Tarefa '{descricao}' já existe HOJE para o grupo {grupo_id} e está ativa. Não será adicionada novamente.")
