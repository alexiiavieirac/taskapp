from datetime import timezone, datetime, timedelta
from sqlalchemy import func
from app.extensions import db
from app.models import Tarefa, HistoricoRanking, Usuario

def obter_limites_semana():
    # Retorna o início e fim da semana atual (domingo a sábado) 
    hoje = datetime.now(timezone.utc)
    # weekday() retorna 0 (segunda) até 6 (domingo)
    dias_desde_domingo = (hoje.weekday() + 1) % 7  # transforma segunda=1 ... domingo=0
    inicio_semana = hoje - timedelta(days=dias_desde_domingo)
    inicio_semana = inicio_semana.replace(hour=0, minute=0, second=0, microsecond=0)
    fim_semana = inicio_semana + timedelta(days=6, hours=23, minutes=59, seconds=59)
    return inicio_semana, fim_semana


def salvar_historico_semanal():
    hoje = datetime.now(timezone.utc)
    # Pega a semana passada (domingo a sábado)
    inicio_semana = hoje - timedelta(days=hoje.weekday() + 8)
    inicio_semana = inicio_semana.replace(hour=0, minute=0, second=0, microsecond=0)
    fim_semana = inicio_semana + timedelta(days=6, hours=23, minutes=59, seconds=59)

    semana_label = inicio_semana.strftime("%Y-W%U")

    ranking = db.session.query(
        Usuario.id.label("usuario_id"),
        Usuario.grupo_id,
        func.count(Tarefa.id).label("tarefas_concluidas")
    ).join(Tarefa, Tarefa.usuario_id == Usuario.id)\
     .filter(
        Tarefa.concluida == True,
        Tarefa.data_conclusao >= inicio_semana,
        Tarefa.data_conclusao <= fim_semana
     ).group_by(Usuario.id, Usuario.grupo_id)\
     .all()

    for registro in ranking:
        historico = HistoricoRanking(
            usuario_id=registro.usuario_id,
            grupo_id=registro.grupo_id,
            tarefas_concluidas=registro.tarefas_concluidas,
            semana=semana_label
        )
        db.session.add(historico)

    db.session.commit()