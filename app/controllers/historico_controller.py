from flask import render_template, request
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from app.models import Tarefa, Usuario
from app.controllers import main_bp
from datetime import datetime, timedelta, timezone


@main_bp.route("/historico")
@login_required
def historico():
    grupo_id = current_user.grupo_id

    # Fuso horário local
    fuso = timezone(timedelta(hours=-3))

    # Usa data fornecida ou data atual no fuso local
    data_str = request.args.get("data")
    if data_str:
        data = datetime.strptime(data_str, "%Y-%m-%d").replace(tzinfo=fuso)
    else:
        data = datetime.now(fuso)

    # Define início e fim do dia com precisão
    inicio_dia = datetime(data.year, data.month, data.day, 0, 0, 0, tzinfo=fuso)
    fim_dia = datetime(data.year, data.month, data.day, 23, 59, 59, 999999, tzinfo=fuso)

    tarefas_por_usuario = db.session.query(
        Usuario.nome,
        func.count(Tarefa.id).label("tarefas_concluidas")
    ).join(Tarefa, Tarefa.concluida_por == Usuario.id) \
    .filter(
        Usuario.grupo_id == grupo_id,
        Tarefa.concluida == True,
        Tarefa.data_criacao >= inicio_dia,
        Tarefa.data_criacao <= fim_dia
    ).group_by(Usuario.id).order_by(func.count(Tarefa.id).desc()).all()

    vencedor = tarefas_por_usuario[0].nome if tarefas_por_usuario else None

    dia_anterior = (data - timedelta(days=1)).strftime("%Y-%m-%d")
    proximo_dia = (data + timedelta(days=1)).strftime("%Y-%m-%d")

    return render_template(
        "historico.html",
        historico=tarefas_por_usuario,
        vencedor=vencedor,
        data=data.strftime("%d/%m/%Y"),
        dia_anterior=dia_anterior,
        proximo_dia=proximo_dia
    )