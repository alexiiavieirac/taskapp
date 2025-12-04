# app/controllers/tarefa_controller.py
from datetime import datetime, date, timedelta, timezone
from flask import abort, current_app, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import Tarefa, Usuario, Grupo, Conexao, SolicitacaoGrupo, PedidoSeguir
from app.controllers import main_bp
import os
from app.utils.date_utils import obter_limites_semana
from app.utils.task_service import adicionar_tarefa
from app.constants import TAREFAS_PRE_ESTABELECIDAS


@main_bp.route('/', methods=["GET", "POST"])
@login_required
def index():
    grupo_id = current_user.grupo_id
    
    date_str = request.args.get('date')
    if date_str:
        current_display_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        current_display_date = datetime.now(timezone.utc).date()
        
    today_date_utc = datetime.now(timezone.utc).date()
    
    # Nova variável: True se a data exibida for anterior a hoje
    is_past_date = current_display_date < today_date_utc

    if current_display_date == today_date_utc:
        display_date_text = "Hoje"
    elif current_display_date == today_date_utc - timedelta(days=1):
        display_date_text = "Ontem"
    else:
        display_date_text = current_display_date.strftime('%d/%m/%Y')


    if request.method == "POST":
        # Se for uma data passada, não permite adicionar nova tarefa
        if is_past_date:
            flash("Não é possível adicionar tarefas para dias passados.", "warning")
            return redirect(url_for("main.index", date=current_display_date.strftime('%Y-%m-%d')))

        descricao = request.form["descricao"].strip()
        imagem = request.files.get("imagem")
        nome_imagem = None

        if descricao in TAREFAS_PRE_ESTABELECIDAS:
            flash("Essa tarefa já faz parte das tarefas diárias e não pode ser adicionada aqui.", "warning")
            return redirect(url_for("main.index", date=current_display_date.strftime('%Y-%m-%d')))

        # A sua lógica de verificação de tarefa existente aqui parece estar um pouco aberta.
        # Se 'ativa=True' é para tarefas existentes, mas o filtro 'data' não está incluído,
        # significa que uma tarefa adicionada hoje com a mesma descrição impedirá uma amanhã.
        # Avalie se você quer que a verificação de tarefa existente seja por dia ou geral.
        # Por enquanto, vou manter como está no seu código original.
        tarefa_existente = Tarefa.query.filter_by(descricao=descricao, grupo_id=grupo_id, ativa=True).first()
        if tarefa_existente:
            flash("Essa tarefa já foi adicionada anteriormente.", "info")
            return redirect(url_for("main.index", date=current_display_date.strftime('%Y-%m-%d')))

        if imagem and imagem.filename != "":
            nome_imagem = secure_filename(imagem.filename)
            imagem.save(os.path.join(current_app.config['UPLOAD_FOLDER'], nome_imagem))

        nova_tarefa = Tarefa(
            descricao=descricao,
            imagem=nome_imagem,
            grupo_id=grupo_id,
            usuario_id=current_user.id,  
            ativa=True,
            concluida=False,
            # Se você quer que a tarefa seja associada à current_display_date,
            # e não apenas à data de criação, você precisaria de um campo 'data_tarefa' no modelo Tarefa
            # Por enquanto, usa data de criação, como no seu código original
            data_criacao=datetime.now(timezone.utc) 
        )

        db.session.add(nova_tarefa)
        db.session.commit()
        flash("Tarefa adicionada com sucesso!", "success")

        return redirect(url_for("main.index", date=current_display_date.strftime('%Y-%m-%d')))


    start_of_day = datetime.combine(current_display_date, datetime.min.time(), tzinfo=timezone.utc)
    end_of_day = datetime.combine(current_display_date, datetime.max.time(), tzinfo=timezone.utc)

    # Lógica para buscar as tarefas
    tarefas = Tarefa.query.filter(
        Tarefa.grupo_id == grupo_id,
        Tarefa.ativa == True,
        # Importante: A sua query filtra as tarefas pela data de CRIAÇÃO.
        # Se você quiser que a 'current_display_date' mostre tarefas agendadas para aquele dia,
        # você precisaria de um campo de data específica no modelo Tarefa para isso.
        # Ex: Tarefa.data_agendada == current_display_date
        # Mantenho o filtro de data de criação como está no seu código original.
        Tarefa.data_criacao >= start_of_day,
        Tarefa.data_criacao <= end_of_day
    ).order_by(Tarefa.data_criacao).all()

    grupo = Grupo.query.get_or_404(grupo_id)
    # Esta variável 'membros' já é a lista de usuários do grupo, perfeita para o chat
    membros = Usuario.query.filter_by(grupo_id=grupo_id).all()

    ranking = db.session.query(
        Usuario.nome,
        func.count(Tarefa.id).label('tarefas_concluidas')
    ).join(Tarefa, Tarefa.usuario_id == Usuario.id) \
    .filter(
        Usuario.grupo_id == grupo_id,
        Tarefa.concluida == True
    ).group_by(Usuario.id, Usuario.nome) \
    .order_by(func.count(Tarefa.id).desc()) \
    .all()

    pedidos_seguir = PedidoSeguir.query.filter_by(destinatario_id=current_user.id, status="pendente").all()
    pedidos_grupo = SolicitacaoGrupo.query.filter_by(grupo_id=current_user.grupo_id, status="pendente").all()
    conexoes = Conexao.query.filter_by(seguido_id=current_user.id).all()  

    pedidos_seguir_count = sum(1 for pedido in pedidos_seguir if not pedido.visto)
    pedidos_grupo_count = sum(1 for pedido in pedidos_grupo if not pedido.visto)
    conexoes_count = sum(1 for conexao in conexoes if not conexao.visto)

    total_notificacoes = pedidos_seguir_count + pedidos_grupo_count + conexoes_count

    return render_template(
        'index.html',
        tarefas=tarefas,
        grupo=grupo,
        membros=membros, # Já estava sendo passado para 'membros'
        grupo_id=grupo_id,
        notificacoes = {
            "grupo": pedidos_grupo_count,
            "seguidores": pedidos_seguir_count,
            "conexoes": conexoes_count
        },
        total_notificacoes=total_notificacoes,
        current_display_date=current_display_date,
        display_date_text=display_date_text,
        is_past_date=is_past_date, # Passa a nova variável para o template
        today_date_utc=today_date_utc,
        timedelta=timedelta,
        grupo_members=membros, # AQUI: Passa a mesma lista 'membros' com o nome 'grupo_members' para o template
        datetime=datetime # Passa o módulo datetime para o template
    )


# Função auxiliar para redirecionar de volta à data correta
def redirect_to_index_with_date():
    redirect_date_str = request.args.get('date')
    if redirect_date_str:
        return redirect(url_for('main.index', date=redirect_date_str))
    return redirect(url_for('main.index')) # Se não houver data na URL, redireciona para hoje


@main_bp.route("/concluir/<int:id>")
@login_required
def concluir(id):
    tarefa = Tarefa.query.get_or_404(id)
    today_date = datetime.now(timezone.utc).date()

    if tarefa.grupo_id != current_user.grupo_id:
        flash("Você não tem permissão para concluir/desmarcar esta tarefa.", "danger")
        abort(403)
    
    # Impede modificação de tarefas de dias passados
    # Sua lógica de data_criacao.date() < today_date pode precisar de ajuste
    # se as tarefas forem "agendadas" para dias diferentes da criação.
    if tarefa.data_criacao.date() < today_date:
        flash("Não é possível modificar tarefas de dias passados.", "warning")
        return redirect_to_index_with_date()

    if tarefa.concluida:
        if tarefa.concluida_por == current_user.id:
            tarefa.concluida = False
            tarefa.concluida_por = None
            tarefa.data_conclusao = None
            flash("Tarefa desmarcada com sucesso!", "info")
        else:
            flash("Apenas quem concluiu a tarefa pode desmarcá-la.", "warning")
            return redirect_to_index_with_date()
    else:
        tarefa.concluida = True
        tarefa.concluida_por = current_user.id
        tarefa.data_conclusao = datetime.now(timezone.utc)
        flash("Tarefa concluída com sucesso!", "success")

    db.session.commit()
    return redirect_to_index_with_date()


@main_bp.route("/deletar/<int:id>")
@login_required
def deletar(id):
    tarefa = Tarefa.query.get_or_404(id)
    today_date = datetime.now(timezone.utc).date()

    if tarefa.usuario_id != current_user.id:
        flash("Você não tem permissão para excluir esta tarefa.", "danger")
        if tarefa.grupo_id != current_user.grupo_id: 
            abort(403)
        return redirect_to_index_with_date()

    # Impede modificação de tarefas de dias passados
    if tarefa.data_criacao.date() < today_date:
        flash("Não é possível modificar tarefas de dias passados.", "warning")
        return redirect_to_index_with_date()

    tarefa.ativa = False
    db.session.commit()
    flash("Tarefa excluída com sucesso.", "success")
    return redirect_to_index_with_date()


@main_bp.route('/editar/<int:id>', methods=["GET", "POST"])
@login_required
def editar(id):
    tarefa = Tarefa.query.get_or_404(id)
    today_date = datetime.now(timezone.utc).date()

    if tarefa.usuario_id != current_user.id:
        flash("Você não tem permissão para editar esta tarefa.", "danger")
        abort(403)

    # Impede modificação de tarefas de dias passados
    if tarefa.data_criacao.date() < today_date:
        flash("Não é possível modificar tarefas de dias passados.", "warning")
        return redirect_to_index_with_date() # Redireciona para o index com a data original
        
    if request.method == "POST":
        descricao = request.form["descricao"].strip()
        nova_imagem = request.files.get("imagem")

        if nova_imagem and nova_imagem.filename != "":
            if tarefa.imagem:
                caminho = os.path.join(current_app.config['UPLOAD_FOLDER'], tarefa.imagem)
                if os.path.exists(caminho):
                    os.remove(caminho)

            nome_imagem = secure_filename(nova_imagem.filename)
            nova_imagem.save(os.path.join(current_app.config['UPLOAD_FOLDER'], nome_imagem))
            tarefa.imagem = nome_imagem
        
        if descricao:
            tarefa.descricao = descricao

        db.session.commit()
        flash("Tarefa editada com sucesso!", "success")
        return redirect_to_index_with_date() # Redireciona para o index com a data original

    return render_template("editar.html", tarefa=tarefa)


@main_bp.route("/tarefas_diarias", methods=["GET", "POST"])
@login_required
def tarefas_diarias():
    if request.method == "POST":
        tarefas_selecionadas = request.form.getlist("tarefas")
        nova_tarefa = request.form.get("nova_tarefa", "").strip()

        for descricao in tarefas_selecionadas:
            adicionar_tarefa(descricao, current_user.grupo_id, current_user.id)

        if nova_tarefa and nova_tarefa not in TAREFAS_PRE_ESTABELECIDAS:
            existe_personalizada = Tarefa.query.filter_by(
                descricao=nova_tarefa,
                grupo_id=current_user.grupo_id,
                ativa=True
            ).first()
            if not existe_personalizada:
                adicionar_tarefa(nova_tarefa, current_user.grupo_id, current_user.id)

        db.session.commit()
        flash("Tarefas adicionadas com sucesso!", "success")
        return redirect(url_for("main.tarefas_diarias"))

    return render_template("tarefas_diarias.html", tarefas=TAREFAS_PRE_ESTABELECIDAS)


@main_bp.route("/imagem/<int:id>", methods=["POST"])
@login_required
def enviar_imagem(id):
    tarefa = Tarefa.query.get_or_404(id)
    today_date = datetime.now(timezone.utc).date()

    if tarefa.grupo_id != current_user.grupo_id:
        flash("Você não tem permissão para adicionar/alterar a imagem desta tarefa.", "danger")
        abort(403)

    # Impede modificação de tarefas de dias passados
    if tarefa.data_criacao.date() < today_date:
        flash("Não é possível modificar tarefas de dias passados.", "warning")
        return redirect_to_index_with_date()

    imagem = request.files.get("imagem")

    if imagem and imagem.filename != "":
        if tarefa.imagem:
            caminho_antigo = os.path.join(current_app.config['UPLOAD_FOLDER'], tarefa.imagem)
            if os.path.exists(caminho_antigo):
                os.remove(caminho_antigo)

        nome_imagem = secure_filename(imagem.filename)
        imagem.save(os.path.join(current_app.config['UPLOAD_FOLDER'], nome_imagem))
        tarefa.imagem = nome_imagem
        db.session.commit()
        flash("Imagem enviada/atualizada com sucesso!", "success")

    return redirect_to_index_with_date()


@main_bp.route('/remover-imagem/<int:id>', methods=["POST"])
@login_required
def remover_imagem(id):
    tarefa = Tarefa.query.get_or_404(id)
    today_date = datetime.now(timezone.utc).date()

    if tarefa.grupo_id != current_user.grupo_id:
        flash("Você não tem permissão para remover a imagem desta tarefa.", "danger")
        abort(403)

    # Impede modificação de tarefas de dias passados
    if tarefa.data_criacao.date() < today_date:
        flash("Não é possível modificar tarefas de dias passados.", "warning")
        return redirect_to_index_with_date()

    if tarefa.imagem:
        caminho_imagem = os.path.join(current_app.config['UPLOAD_FOLDER'], tarefa.imagem)
        if os.path.exists(caminho_imagem):
            os.remove(caminho_imagem)
        tarefa.imagem = None
        db.session.commit()
        flash("Imagem removida com sucesso!", "success")

    return redirect_to_index_with_date()


@main_bp.route("/excluir_tarefa/<int:id>", methods=["POST"])
@login_required
def excluir_tarefa(id):
    tarefa = Tarefa.query.get_or_404(id)
    today_date = datetime.now(timezone.utc).date()

    if tarefa.grupo_id != current_user.grupo_id:
        flash("Você não tem permissão para excluir esta tarefa.", "danger")
        abort(403)

    if tarefa.usuario_id is None:
        flash("Essa tarefa padrão não pode ser excluída por aqui.", "warning")
        return redirect_to_index_with_date()

    if tarefa.usuario_id != current_user.id:
        flash("Você não tem permissão para excluir esta tarefa.", "danger")
        return redirect_to_index_with_date()

    # Impede modificação de tarefas de dias passados
    if tarefa.data_criacao.date() < today_date:
        flash("Não é possível modificar tarefas de dias passados.", "warning")
        return redirect_to_index_with_date()

    tarefa.ativa = False
    db.session.commit()
    flash("Tarefa excluída com sucesso.", "success")
    return redirect_to_index_with_date()
