from datetime import datetime, timezone
from flask import abort, app, current_app, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func
from werkzeug.utils import secure_filename
from app import db
from app.models import Tarefa, Usuario, Grupo, Conexao, SolicitacaoGrupo, PedidoSeguir
from app.controllers import main_bp
import os
from app.utils.date_utils import obter_limites_semana
from app.utils.task_service import adicionar_tarefa


@main_bp.route('/', methods=["GET", "POST"])
@login_required
def index():
    grupo_id = current_user.grupo_id
    semana = obter_limites_semana()

    # Tarefas pré-estabelecidas (iguais às de tarefas_diarias)
    tarefas_pre_estabelecidas = [
        "Lavar louça",
        "Varrer a casa",
        "Passar pano nos móveis",
        "Lavar banheiro",
        "Retirar lixos",
        "Recolher roupa",
        "Estender roupa",
        "Colocar roupa para lavar",
        "Arrumar o quarto",
        "Guardar as roupas",
        "Fazer comida",
        "Fazer compras"
    ]

    if request.method == "POST":
        descricao = request.form["descricao"].strip()
        imagem = request.files.get("imagem")
        nome_imagem = None

        # Verifica se é uma tarefa pré-estabelecida
        if descricao in tarefas_pre_estabelecidas:
            flash("Essa tarefa já faz parte das tarefas diárias e não pode ser adicionada aqui.")
            return redirect(url_for("main.index"))

        # Verifica se a tarefa já existe no banco de dados para o mesmo grupo
        tarefa_existente = Tarefa.query.filter_by(descricao=descricao, grupo_id=grupo_id, ativa=True).first()
        if tarefa_existente:
            flash("Essa tarefa já foi adicionada anteriormente.")
            return redirect(url_for("main.index"))

        if imagem and imagem.filename != "":
            nome_imagem = secure_filename(imagem.filename)
            imagem.save(os.path.join(current_app.config['UPLOAD_FOLDER'], nome_imagem))

        nova_tarefa = Tarefa(
            descricao=descricao,
            imagem=nome_imagem,
            grupo_id=grupo_id,
            usuario_id=current_user.id,  
            ativa=True,
            concluida=False
        )

        db.session.add(nova_tarefa)
        db.session.commit()

        return redirect("/")

    tarefas = Tarefa.query.filter_by(grupo_id=grupo_id, ativa=True).order_by(Tarefa.data_criacao).all()
    grupo = Grupo.query.get_or_404(grupo_id)
    membros = Usuario.query.filter_by(grupo_id=grupo_id).all()

    ranking = db.session.query(
        Usuario.nome,
        func.count(Tarefa.id).label('tarefas_concluidas')
    ).join(Tarefa, Tarefa.usuario_id == Usuario.id) \
    .filter(
        Usuario.grupo_id == grupo_id,
        Tarefa.concluida == True,
        Tarefa.ativa == True
    ).group_by(Usuario.id, Usuario.nome) \
    .order_by(func.count(Tarefa.id).desc()) \
    .all()

    # ======================================
    # Notificações (Pedidos pendentes)
    # ======================================
    pedidos_seguir = PedidoSeguir.query.filter_by(destinatario_id=current_user.id, status="pendente").all()
    pedidos_grupo = SolicitacaoGrupo.query.filter_by(grupo_id=current_user.grupo_id, status="pendente").all()
    conexoes = Conexao.query.filter_by(seguido_id=current_user.id).all()  

    # Contar quantas notificações estão pendentes
    pedidos_seguir_count = sum(1 for pedido in pedidos_seguir if not pedido.visto)  # Só conta se não foi visto
    pedidos_grupo_count = sum(1 for pedido in pedidos_grupo if not pedido.visto)
    conexoes_count = sum(1 for conexao in conexoes if not conexao.visto)

    # ======================================
    # Marcar notificações como vistas
    # ====================================== 
    PedidoSeguir.query.filter_by(destinatario_id=current_user.id, status="pendente").update({"visto": True, "data_visto": datetime.now(timezone.utc)})
    SolicitacaoGrupo.query.filter_by(grupo_id=current_user.grupo_id, status="pendente").update({"visto": True, "data_visto": datetime.now(timezone.utc)})
    Conexao.query.filter_by(seguido_id=current_user.id).update({"visto": True, "data_visto": datetime.now(timezone.utc)})

    # Commit para salvar as alterações no banco
    db.session.commit()

    total_notificacoes = pedidos_seguir_count + pedidos_grupo_count + conexoes_count

    return render_template(
        'index.html',
        tarefas=tarefas,
        grupo=grupo,
        membros=membros,
        grupo_id=grupo_id,
        notificacoes = {
            "grupo": pedidos_grupo_count,
            "seguidores": pedidos_seguir_count,
            "conexoes": conexoes_count
        },
        total_notificacoes=total_notificacoes
    )


@main_bp.route("/concluir/<int:id>")
@login_required
def concluir(id):
    tarefa = Tarefa.query.get_or_404(id)

    # Verifica se o usuário pertence ao mesmo grupo
    if tarefa.grupo_id != current_user.grupo_id:
        abort(403)

    if not tarefa.ativa:
        flash("Esta tarefa está desativada.")
        return redirect("/")

    # Se já está concluída
    if tarefa.concluida:
        # Só quem concluiu pode desmarcar
        if tarefa.concluida_por == current_user.id:
            tarefa.concluida = False
            tarefa.concluida_por = None
            tarefa.data_conclusao = None  # limpa a data
            flash("Tarefa desmarcada com sucesso!")
        else:
            flash("Apenas quem concluiu a tarefa pode desmarcá-la.")
    else:
        # Marca como concluída por quem clicou
        tarefa.concluida = True
        tarefa.concluida_por = current_user.id
        tarefa.data_conclusao = datetime.now(timezone.utc)  # registra o momento
        flash("Tarefa concluída com sucesso!")

    db.session.commit()
    return redirect("/")


@main_bp.route("/deletar/<int:id>")
@login_required
def deletar(id):
    tarefa = Tarefa.query.get_or_404(id)

    # Verifica se o usuário pertence ao mesmo grupo
    if tarefa.grupo_id != current_user.grupo_id:
        flash("Você não pode excluir esta tarefa.")
        return redirect("/")

    # Marca como inativa, não deleta
    tarefa.ativa = False
    db.session.commit()
    #flash("Tarefa excluída com sucesso.")
    return redirect("/")


@main_bp.route('/editar/<int:id>', methods=["GET", "POST"])
@login_required
def editar(id):
    tarefa = Tarefa.query.get_or_404(id)

    # Verifica se o usuário atual é o criador da tarefa
    if tarefa.usuario_id != current_user.id:
        abort(403)  # Proibido

    if not tarefa.ativa:
        flash("Tarefa desativada não pode ser editada.")
        return redirect("/")

    if request.method == "POST":
        nova_desc = request.form["descricao"].strip()
        nova_imagem = request.files.get("imagem")

        if nova_desc:
            tarefa.descricao = nova_desc

        if nova_imagem and nova_imagem.filename != "":
            # Se já existe uma imagem antiga, remove ela
            if tarefa.imagem:
                caminho = os.path.join(current_app.config['UPLOAD_FOLDER'], tarefa.imagem)
                if os.path.exists(caminho):
                    os.remove(caminho)

            nome_imagem = secure_filename(nova_imagem.filename)
            nova_imagem.save(os.path.join(current_app.config['UPLOAD_FOLDER'], nome_imagem))
            tarefa.imagem = nome_imagem

        db.session.commit()
        flash("Tarefa editada com sucesso!")
        return redirect("/")

    return render_template("editar.html", tarefa=tarefa)

# TAREFAS PADROES
@main_bp.route("/tarefas_diarias", methods=["GET", "POST"])
@login_required
def tarefas_diarias():
    tarefas_pre_estabelecidas = [
        "Lavar louça",
        "Varrer a casa",
        "Passar pano nos móveis",
        "Lavar banheiro",
        "Retirar lixos",
        "Recolher roupa",
        "Estender roupa",
        "Colocar roupa para lavar",
        "Arrumar o quarto",
        "Guardar as roupas",
        "Fazer comida",
        "Fazer compras"
    ]

    if request.method == "POST":
        # Tarefas selecionadas (pré-estabelecidas)
        tarefas_selecionadas = request.form.getlist("tarefas")

        # Nova tarefa personalizada (input de texto)
        nova_tarefa = request.form.get("nova_tarefa", "").strip()

        # Adiciona as tarefas selecionadas (pré-estabelecidas), se ainda não existirem
        for descricao in tarefas_selecionadas:
            adicionar_tarefa(descricao, current_user.grupo_id, current_user.id)

        # Adiciona a nova tarefa personalizada, se não estiver nas pré-estabelecidas nem já no banco
        if nova_tarefa and nova_tarefa not in tarefas_pre_estabelecidas:
            # Verifica se a tarefa personalizada já existe no banco antes de adicionar
            existe_personalizada = Tarefa.query.filter_by(
                descricao=nova_tarefa,
                grupo_id=current_user.grupo_id,
                ativa=True
            ).first()
            if not existe_personalizada:
                adicionar_tarefa(nova_tarefa, current_user.grupo_id, current_user.id)

        # Commit das mudanças no banco de dados
        db.session.commit()
        #flash("Tarefas adicionadas com sucesso!")
        return redirect(url_for("main.tarefas_diarias"))

    return render_template("tarefas_diarias.html", tarefas=tarefas_pre_estabelecidas)


@main_bp.route("/imagem/<int:id>", methods=["POST"])
def enviar_imagem(id):
    tarefa = Tarefa.query.get_or_404(id)
    imagem = request.files.get("imagem")

    if imagem and imagem.filename != "":
        # Se já existe uma imagem antiga, deleta
        if tarefa.imagem:
            caminho_antigo = os.path.join(current_app.config['UPLOAD_FOLDER'], tarefa.imagem)
            if os.path.exists(caminho_antigo):
                os.remove(caminho_antigo)

        nome_imagem = secure_filename(imagem.filename)
        imagem.save(os.path.join(current_app.config['UPLOAD_FOLDER'], nome_imagem))
        tarefa.imagem = nome_imagem
        db.session.commit()

    return redirect("/")


@main_bp.route('/remover-imagem/<int:id>', methods=["POST"])
@login_required
def remover_imagem(id):
    tarefa = Tarefa.query.get_or_404(id)

    if tarefa.usuario_id != current_user.id:
        abort(403)  # Não autorizado

    if tarefa.imagem:
        caminho_imagem = os.path.join(current_app.config['UPLOAD_FOLDER'], tarefa.imagem)
        if os.path.exists(caminho_imagem):
            os.remove(caminho_imagem)
        tarefa.imagem = None
        db.session.commit()

    return redirect(url_for('main.index'))


@main_bp.route("/excluir_tarefa/<int:id>", methods=["POST"])
@login_required
def excluir_tarefa(id):
    tarefa = Tarefa.query.get_or_404(id)

    # Verifica se a tarefa pertence ao grupo do usuário logado
    if tarefa.grupo_id != current_user.grupo_id:
        abort(403)

    # Impede a exclusão se a tarefa não tiver um dono definido
    if tarefa.usuario_id is None:
        #flash("Essa tarefa padrão não pode ser excluída.")
        return redirect(url_for("main.index"))

    # Impede se o usuário atual não for o dono da tarefa (mesmo que tenha sido adicionada do tarefas_diarias)
    if tarefa.usuario_id != current_user.id:
        flash("Você não tem permissão para excluir esta tarefa.")
        return redirect(url_for("main.index"))

    # Marca como inativa ao invés de deletar
    tarefa.ativa = False
    db.session.commit()
    flash("Tarefa excluída com sucesso.")
    return redirect(url_for("main.index"))
