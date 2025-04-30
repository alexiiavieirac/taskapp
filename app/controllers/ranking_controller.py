from unittest import case
from flask import render_template
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from app.models import Tarefa, Usuario, HistoricoRanking
from app.controllers import main_bp
from datetime import datetime, timedelta, timezone
from app.utils.date_utils import obter_limites_semana


@main_bp.route("/ranking")
@login_required
def ranking():
    grupo_id = current_user.grupo_id
    inicio_semana, fim_semana = obter_limites_semana()
    agora = datetime.now(timezone.utc)

    # Ranking da semana atual (baseado em quem concluiu corretamente)
    ranking = db.session.query(
        Usuario.nome,
        func.count(Tarefa.id).label('tarefas_concluidas')
    ).outerjoin(Tarefa, Tarefa.concluida_por == Usuario.id) \
    .filter(
        Usuario.grupo_id == grupo_id,
        Tarefa.concluida == True,
        Tarefa.data_conclusao != None,  # Garante que tem data válida
        Tarefa.data_conclusao >= inicio_semana,
        Tarefa.data_conclusao <= fim_semana
    ) \
    .group_by(Usuario.id, Usuario.nome) \
    .order_by(func.count(Tarefa.id).desc()) \
    .all()

    # Cálculo da semana anterior
    semana_anterior_inicio = inicio_semana - timedelta(days=7)
    semana_anterior_fim = fim_semana - timedelta(days=7)
    semana_label = semana_anterior_inicio.strftime("%Y-W%U")

    # Verifica se já passou da semana atual para salvar o histórico da semana passada
    if agora > fim_semana:
        ja_salvo = HistoricoRanking.query.filter_by(grupo_id=grupo_id, semana=semana_label).first()

        if not ja_salvo:
            ranking_anterior = db.session.query(
                Usuario.id.label("usuario_id"),
                func.count(
                    case((Tarefa.concluida == True, 1))
                ).label('tarefas_concluidas')
            ).join(Tarefa, Tarefa.concluida_por == Usuario.id) \
            .filter(
                Usuario.grupo_id == grupo_id,
                Tarefa.concluida == True,
                Tarefa.data_conclusao != None,  # Também exige data válida
                Tarefa.data_conclusao >= semana_anterior_inicio,
                Tarefa.data_conclusao <= semana_anterior_fim
            ) \
            .group_by(Usuario.id) \
            .all()

            for r in ranking_anterior:
                novo_registro = HistoricoRanking(
                    usuario_id=r.usuario_id,
                    grupo_id=grupo_id,
                    tarefas_concluidas=r.tarefas_concluidas,
                    semana=semana_label,
                )
                db.session.add(novo_registro)

            db.session.commit()

    tempo_restante = fim_semana - agora

    return render_template("ranking.html", ranking=ranking, tempo_restante=tempo_restante)