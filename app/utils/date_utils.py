from datetime import timezone, datetime, timedelta
from sqlalchemy import func
from app.extensions import db
from app.models import Tarefa, HistoricoRanking, Usuario

# Definindo o fuso horário padrão para UTC-3 (Brasília)
FUSO_HORARIO_BRASILIA = timezone(timedelta(hours=-3))

def obter_limites_semana():
    # Retorna o início e fim da semana atual (domingo a sábado) em UTC-3
    hoje = datetime.now(FUSO_HORARIO_BRASILIA) # Usando o fuso horário definido
    
    # weekday() retorna 0 (segunda) até 6 (domingo)
    # Precisamos ajustar para que o domingo seja o dia 0 da semana
    # (hoje.weekday() + 1) % 7: segunda=1, terça=2, ..., sábado=6, domingo=0
    dias_desde_domingo = (hoje.weekday() + 1) % 7 
    
    inicio_semana = hoje - timedelta(days=dias_desde_domingo)
    inicio_semana = inicio_semana.replace(hour=0, minute=0, second=0, microsecond=0)
    
    fim_semana = inicio_semana + timedelta(days=6, hours=23, minutes=59, seconds=59, microseconds=999999) # Adicionado microsegundos
    
    return inicio_semana, fim_semana


def salvar_historico_semanal():
    # Esta função é muito similar à lógica de salvamento em ranking_controller.py
    # Pode haver uma duplicação se o ranking_controller também salva.
    # Se esta função for usada por um script agendado (ex: cron job), ok.
    # Caso contrário, pode ser redundante com a lógica do ranking_controller.

    hoje = datetime.now(timezone.utc) # Aqui você usa UTC, inconsistente com FUSO_HORARIO_BRASILIA
    # Recomenda-se usar sempre o mesmo fuso horário ao manipular datas ou converter para UTC antes de salvar no DB
    # Para consistência com obter_limites_semana, vamos usar FUSO_HORARIO_BRASILIA para calcular a semana anterior
    
    # Calcula a semana anterior (domingo a sábado)
    # Pega a data atual no fuso horário local
    agora_local = datetime.now(FUSO_HORARIO_BRASILIA)
    
    # Dias desde domingo para a data atual
    dias_desde_domingo_agora = (agora_local.weekday() + 1) % 7
    
    # Início da semana atual (domingo 00:00:00)
    inicio_semana_atual = agora_local - timedelta(days=dias_desde_domingo_agora)
    inicio_semana_atual = inicio_semana_atual.replace(hour=0, minute=0, second=0, microsecond=0)

    # Início da semana anterior (7 dias antes do início da semana atual)
    inicio_semana_anterior = inicio_semana_atual - timedelta(days=7)
    fim_semana_anterior = inicio_semana_anterior + timedelta(days=6, hours=23, minutes=59, seconds=59, microseconds=999999)

    semana_label = inicio_semana_anterior.strftime("%Y-W%U")

    # Verifica se o histórico para esta semana já foi salvo para evitar duplicatas
    ja_salvo_para_qualquer_grupo = HistoricoRanking.query.filter_by(semana=semana_label).first()
    if ja_salvo_para_qualquer_grupo:
        # Já foi salvo por um grupo ou por esta função, não fazer nada ou logar.
        print(f"DEBUG: Histórico semanal para {semana_label} já foi salvo, ignorando.")
        return # Sai da função para evitar re-processamento

    # Para cada grupo que tem usuários, calcule o ranking e salve.
    # Melhor pegar os usuários e seus grupos e depois iterar por grupo
    grupos_ids = db.session.query(Usuario.grupo_id).filter(Usuario.grupo_id != None).distinct().all()
    
    for (grupo_id,) in grupos_ids:
        ranking_grupo = db.session.query(
            Usuario.id.label("usuario_id"),
            func.count(Tarefa.id).label("tarefas_concluidas")
        ).join(Tarefa, Tarefa.concluida_por == Usuario.id) \
         .filter(
            Usuario.grupo_id == grupo_id, # Filtra por grupo
            Tarefa.concluida == True,
            Tarefa.data_conclusao >= inicio_semana_anterior, # Usa o período da semana anterior
            Tarefa.data_conclusao <= fim_semana_anterior
         ).group_by(Usuario.id)\
         .all()

        for registro in ranking_grupo:
            historico = HistoricoRanking(
                usuario_id=registro.usuario_id,
                grupo_id=grupo_id, # Usa o grupo_id correto da iteração
                tarefas_concluidas=registro.tarefas_concluidas,
                semana=semana_label
            )
            db.session.add(historico)

    db.session.commit()
    print(f"DEBUG: Histórico semanal para {semana_label} salvo com sucesso para {len(grupos_ids)} grupos.")
