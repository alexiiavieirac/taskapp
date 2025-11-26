from flask import current_app, render_template, request, flash, redirect, url_for
# from flask.cli import main # Removida importação incorreta
from flask_login import login_required, current_user
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import func
from app.extensions import db
from app.models import Grupo, Usuario, SolicitacaoGrupo, ConviteGrupo, Conexao, Tarefa
from app.controllers import main_bp
from app.extensions import mail # Adicionada importação correta para enviar e-mails


@main_bp.route('/grupo')
@login_required
def grupo():
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

    grupo = current_user.grupo

    # Ranking real com todos os membros (mesmo quem não concluiu nada)
    membros = db.session.query(
        Usuario,
        func.count(Tarefa.id).label('tarefas_concluidas')
    ).outerjoin(Tarefa, Tarefa.concluida_por == Usuario.id) \
     .filter(Usuario.grupo_id == grupo.id) \
     .group_by(Usuario.id) \
     .order_by(func.count(Tarefa.id).desc()) \
     .all()

     # Ranking só com nome e pontuação para usar na lista ordenada
    ranking = [
        (membro.nome, pontos)
        for membro, pontos in membros
    ]

    return render_template("grupo.html", grupo=grupo, membros=membros, ranking=ranking)


@main_bp.route('/criar-grupo', methods=['GET', 'POST'])
@login_required
def criar_grupo():
    if current_user.grupo_id:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        nome_grupo = request.form["nome"]
        grupo = Grupo(nome=nome_grupo, proprietario_id=current_user.id)
        db.session.add(grupo)
        db.session.commit()

        current_user.grupo_id = grupo.id
        db.session.commit()

        flash("✅ Grupo criado com sucesso!", "success")
        return redirect(url_for("main.convidar_para_grupo"))

    return render_template("criar_grupo.html")


@main_bp.route("/enviar-convite", methods=["POST"])
@login_required
def enviar_convite():
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

    email_destino = request.form["email"].strip().lower()  # Normaliza o e-mail

    if email_destino == current_user.email:
        flash("⚠️ Você não pode enviar convite para si mesmo.", "warning")
        return redirect(url_for("main.grupo"))

    usuario_convidado = Usuario.query.filter_by(email=email_destino).first()

    if not usuario_convidado:
        flash("❌ Usuário não encontrado.", "danger")
        return redirect(url_for("main.grupo"))

    # Evita duplicação de convites ativos
    convite_existente = ConviteGrupo.query.filter_by(
        email_convidado=email_destino, grupo_id=current_user.grupo_id
    ).first()
    if convite_existente:
        flash("⚠️ Já foi enviado um convite para esse usuário.", "warning")
        return redirect(url_for("main.grupo"))

    # Gera token único
    token = s.dumps({"email": email_destino, "grupo_id": current_user.grupo_id})
    link_aceite = url_for("main.aceitar_convite", token=token, _external=True)

    # Configura o remetente com o nome do usuário logado
    msg = Message(
        subject="📩 Convite para entrar no grupo",
        recipients=[email_destino],
        sender=(f"{current_user.nome} <no-reply@taskapp.com>")  # Remetente com o nome do usuário logado
    )

    # Corpo do e-mail
    msg.html = f"""
        <h3>Você foi convidado para entrar no grupo <strong>{current_user.grupo.nome}</strong>!</h3>
        <p>Para aceitar o convite, clique no link abaixo:</p>
        <p><a href="{link_aceite}">Aceitar convite</a></p>
        <p><em>Este link expira em 1 hora.</em></p>
    """

    try:
        mail.send(msg) # Correção: Usando 'mail.send(msg)'
        # Salva o convite no banco SOMENTE após o envio bem-sucedido do e-mail
        convite = ConviteGrupo(
            email_convidado=email_destino,
            grupo_id=current_user.grupo_id,
            token=token
        )
        db.session.add(convite)
        db.session.commit()
        flash("✅ Convite enviado com sucesso!", "success")
    except Exception as e:
        flash(f"❌ Erro ao enviar o e-mail: {str(e)}", "danger")
    
    return redirect(url_for("main.grupo"))


@main_bp.route("/aceitar-convite/<token>")
def aceitar_convite(token):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

    try:
        # Descriptografa o token com tempo máximo de 1 hora
        data = s.loads(token, max_age=3600)
        email = data["email"]
        grupo_id = data["grupo_id"]

        # Busca o usuário e grupo no banco
        usuario = Usuario.query.filter_by(email=email).first()
        grupo = Grupo.query.get(grupo_id)

        # Valida se os dados existem
        if not usuario or not grupo:
            flash("❌ Usuário ou grupo não encontrados.", "danger")
            return redirect(url_for("main.login"))

        # Verifica se o usuário já está em um grupo
        # Considerar a regra de negócio: se o usuário já está em um grupo, ele pode aceitar outro convite?
        # A lógica atual substitui o grupo, o que está ok se essa for a intenção.
        if usuario.grupo_id and usuario.grupo_id == grupo.id: # Se já está no grupo, apenas flasheia e redireciona
             flash(f"🎉 Você já faz parte do grupo '{grupo.nome}'!", "info")
             return redirect(url_for("main.login"))


        # Atualiza o grupo do usuário
        usuario.grupo_id = grupo.id
        db.session.commit()

        # Exclui o convite após o aceite (opcional)
        convite = ConviteGrupo.query.filter_by(token=token).first()
        if convite:
            db.session.delete(convite)
            db.session.commit()

        flash(f"🎉 Você agora faz parte do grupo '{grupo.nome}'!", "success")
        return redirect(url_for("main.login"))

    except Exception as e:
        print(f"Erro ao aceitar convite: {e}")
        flash("❌ Link inválido, expirado ou já utilizado.", "danger")
        return redirect(url_for("main.login"))
    

# Pedidos para entrar no grupo
@main_bp.route("/pedidos_grupo")
@login_required
def pedidos_grupo():
    grupo = current_user.grupo

    if not current_user.grupo_id:
        flash("Você não está em um grupo.", "info") # Adicionada categoria
        return redirect(url_for("main.index"))

    pedidos = SolicitacaoGrupo.query.filter_by(grupo_id=current_user.grupo_id, status="pendente").all()
    return render_template('pedidos_grupo.html', pedidos=pedidos)


@main_bp.route('/solicitar_entrada_grupo/<int:usuario_id>', methods=['POST'])
@login_required
def solicitar_entrada_grupo(usuario_id):
    usuario_alvo = Usuario.query.get_or_404(usuario_id)

    # Verifica se o usuário atual segue o usuário alvo
    conexao = Conexao.query.filter_by(
        seguidor_id=current_user.id,
        seguido_id=usuario_alvo.id
    ).first()

    if not conexao:
        flash("Você precisa seguir esse usuário antes de solicitar entrada no grupo.", "warning")
        return redirect(url_for("main.conexoes"))

    # Verifica se o usuário alvo tem um grupo
    if not usuario_alvo.grupo_id:
        flash("Este usuário não faz parte de um grupo.", "danger")
        return redirect(url_for("main.conexoes"))

    # Verifica se já existe uma solicitação pendente
    ja_existe = SolicitacaoGrupo.query.filter_by(
        solicitante_id=current_user.id,
        grupo_id=usuario_alvo.grupo_id,
        status="pendente"
    ).first()

    if ja_existe:
        flash("Você já solicitou entrada neste grupo.", "info")
        return redirect(url_for("main.conexoes"))

    nova_solicitacao = SolicitacaoGrupo(
        solicitante_id=current_user.id,
        grupo_id=usuario_alvo.grupo_id
    )
    db.session.add(nova_solicitacao)
    db.session.commit()

    flash("Solicitação enviada com sucesso!", "success")
    return redirect(url_for("main.conexoes"))


@main_bp.route('/aceitar_pedido_grupo/<int:pedido_id>', methods=['POST'])
@login_required
def aceitar_pedido_grupo(pedido_id):
    pedido = SolicitacaoGrupo.query.get_or_404(pedido_id)
    grupo = current_user.grupo

    # Verifica se o grupo é o mesmo
    if not grupo or pedido.grupo_id != grupo.id:
        flash("Você não pode aceitar esse pedido.", "danger")
        return redirect(url_for('main.pedidos_grupo'))

    # Atualiza status e atribui grupo ao solicitante
    pedido.status = 'aceito'
    solicitante = Usuario.query.get(pedido.solicitante_id)

    # Verifica se o solicitante já está no grupo ou tem grupo_original_id preenchido
    if solicitante.grupo_id != grupo.id: # Apenas atualiza se o usuário não está no grupo alvo
        if not solicitante.grupo_original_id:
            solicitante.grupo_original_id = solicitante.grupo_id # Salva o grupo atual como original
        solicitante.grupo_id = grupo.id # Atribui o novo grupo

    db.session.commit()
    flash("Pedido aceito! Usuário agora faz parte do grupo.", "success")
    return redirect(url_for('main.pedidos_grupo'))


@main_bp.route('/recusar_pedido_grupo/<int:pedido_id>', methods=['POST'])
@login_required
def recusar_pedido_grupo(pedido_id):
    pedido = SolicitacaoGrupo.query.get_or_404(pedido_id)
    grupo = current_user.grupo

    if not grupo or pedido.grupo_id != grupo.id:
        flash("Você não pode recusar esse pedido.", "danger")
        return redirect(url_for('main.pedidos_grupo'))

    pedido.status = 'recusado'
    db.session.commit()
    flash("Pedido recusado com sucesso.", "warning")
    return redirect(url_for('main.pedidos_grupo'))


@main_bp.route("/adicionar-membro", methods=["POST"])
@login_required
def adicionar_membro():
    email = request.form["email"]
    membro = Usuario.query.filter_by(email=email).first()
    if membro:
        membro.grupo = current_user.grupo
        db.session.commit()
        flash("✅ Membro adicionado ao grupo com sucesso!", "success")
    else:
        flash("❌ Usuário não encontrado.", "danger")
    return redirect(url_for("main.dashboard"))


@main_bp.route("/entrar_grupo/<int:grupo_id>")
@login_required
def entrar_grupo(grupo_id):
    ja_enviado = SolicitacaoGrupo.query.filter_by(solicitante_id=current_user.id, grupo_id=grupo_id, status="pendente").first()
    if not ja_enviado:
        pedido = SolicitacaoGrupo(solicitante_id=current_user.id, grupo_id=grupo_id)
        db.session.add(pedido)
        db.session.commit()
    flash("Pedido enviado com sucesso.", "info") # Adicionada categoria
    return redirect(url_for("main.conexoes"))