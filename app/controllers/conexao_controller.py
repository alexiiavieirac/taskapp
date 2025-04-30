from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from flask import Blueprint, abort, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import Conexao, PedidoSeguir, Usuario
from app.controllers import main_bp


# conexao_bp = Blueprint('conexao', __name__)

# @conexao_bp.route('/test-db')
# def test_db():
#     try:
#         db.session.execute(text('SELECT 1'))
#         return 'Conexão com o MySQL funcionando!'
#     except Exception as e:
#         return f'Erro na conexão com o MySQL: {str(e)}'

@main_bp.route("/conexoes")
@login_required
def conexoes():
    seguindo = Conexao.query.filter_by(seguidor_id=current_user.id).all()
    seguidores = Conexao.query.filter_by(seguido_id=current_user.id).all()

    # Criar um conjunto para evitar IDs duplicados
    ids_bloqueados = {c.seguido_id for c in seguindo}
    ids_bloqueados.add(current_user.id)

    # Considerar somente pedidos pendentes
    pedidos_enviados = PedidoSeguir.query.filter_by(
        remetente_id=current_user.id,
        status='pendente'
    ).all()
    ids_bloqueados.update(p.destinatario_id for p in pedidos_enviados)

    # Lista final de usuários disponíveis para seguir
    usuarios_disponiveis = Usuario.query.filter(~Usuario.id.in_(ids_bloqueados)).all()

    return render_template(
        "conexoes.html",
        seguindo=seguindo,
        seguidores=seguidores,
        usuarios=usuarios_disponiveis,
        pedidos_enviados=pedidos_enviados
    )

# Rota de Pedidos de Seguir - Enviar um pedido de seguimento para outro usuário.
@main_bp.route("/seguir/<int:usuario_id>")
@login_required
def seguir(usuario_id):
    destinatario = Usuario.query.get_or_404(usuario_id)

    if destinatario.id == current_user.id:
        flash("Você não pode seguir a si mesmo.")
        return redirect(url_for("main.conexoes"))

    # Verifica se já há um pedido pendente
    pedido_existente = PedidoSeguir.query.filter_by(
        remetente_id=current_user.id,
        destinatario_id=destinatario.id,
        status='pendente'
    ).first()

    if pedido_existente:
        flash("Você já enviou um pedido para esse usuário.")
        return redirect(url_for("main.conexoes"))

    # Cria novo pedido
    novo_pedido = PedidoSeguir(
        remetente_id=current_user.id,
        destinatario_id=usuario_id,
        status="pendente"
    )
    db.session.add(novo_pedido)
    db.session.commit()

    flash("Solicitação enviada!")
    return redirect(url_for("main.conexoes"))

# Rota para aceitar o pedido de seguimento
@main_bp.route("/aceitar_seguir/<int:pedido_id>")
@login_required
def aceitar_seguir(pedido_id):
    pedido = PedidoSeguir.query.get_or_404(pedido_id)

    if pedido.destinatario_id != current_user.id:
        abort(403)

    # Verifica se a conexão já existe
    conexao_existente = Conexao.query.filter_by(
        seguidor_id=pedido.remetente_id,
        seguido_id=pedido.destinatario_id
    ).first()

    if not conexao_existente:
        # Cria a conexão se ainda não existir
        conexao = Conexao(
            seguidor_id=pedido.remetente_id,
            seguido_id=pedido.destinatario_id
        )
        db.session.add(conexao)

    # Atualiza status do pedido
    pedido.status = "aceito"
    db.session.commit()

    flash("Pedido aceito!", "success")
    return redirect(url_for("main.pedidos_seguir"))

# Rota para rejeitar o pedido de seguimento
@main_bp.route("/rejeitar_seguir/<int:pedido_id>")
@login_required
def rejeitar_seguir(pedido_id):
    pedido = PedidoSeguir.query.get_or_404(pedido_id)

    if pedido.destinatario_id != current_user.id:
        flash("Você não pode rejeitar este pedido.", "danger")
        return redirect(url_for("main.conexoes"))

    # Define se vamos excluir ou apenas mudar o status
    apenas_atualizar_status = True  # Mude para False se quiser deletar de vez

    if apenas_atualizar_status:
        pedido.status = "rejeitado"
        db.session.commit()
        flash("Pedido rejeitado.", "info")
    else:
        db.session.delete(pedido)
        db.session.commit()
        flash("Pedido de seguimento rejeitado e removido.", "info")

    return redirect(url_for('main.pedidos_seguir'))

@main_bp.route('/parar_de_seguir/<int:usuario_id>', methods=['POST'])
@login_required
def parar_de_seguir(usuario_id):
    usuario_alvo = Usuario.query.get_or_404(usuario_id)

    # Verifica se a conexão de seguimento existe
    conexao = Conexao.query.filter_by(
        seguidor_id=current_user.id,
        seguido_id=usuario_id
    ).first()

    if conexao:
        # Remove a conexão de seguimento
        db.session.delete(conexao)

        # Se o usuário atual está no grupo do usuário alvo, retorna ao seu grupo original
        if current_user.grupo_id == usuario_alvo.grupo_id:
            if current_user.grupo_original_id:
                # Caso o usuário tenha um grupo original configurado, retorna a ele
                current_user.grupo_id = current_user.grupo_original_id
                flash('Você saiu do grupo e voltou para seu grupo original.', 'info')
            else:
                # Caso não tenha grupo original, remove a associação de grupo
                current_user.grupo_id = None
                flash('Você saiu do grupo.', 'info')

        # Commit para salvar as mudanças
        db.session.commit()
    else:
        flash('Você não segue essa pessoa.', 'warning')

    return redirect(url_for('main.conexoes'))

# Pedidos para seguir o usuário
@main_bp.route('/pedidos_seguir')
@login_required
def pedidos_seguir():
    # Marcar como vistos todos os pedidos pendentes ainda não vistos
    pedidos_nao_vistos = PedidoSeguir.query.filter_by(destinatario_id=current_user.id, status="pendente", visto=False).all()

    for pedido in pedidos_nao_vistos:
        pedido.visto = True
        pedido.data_visto = datetime.now(timezone.utc)

    db.session.commit()

    pedidos_recebidos = PedidoSeguir.query.filter_by(destinatario_id=current_user.id, status="pendente").all()
    return render_template("pedidos_seguir.html", pedidos_recebidos=pedidos_recebidos)

# Para limpar pedidos expirados
@main_bp.route("/limpar_pedidos_expirados")
@login_required
def limpar_pedidos_expirados():
    limite = datetime.now(timezone.utc) - timedelta(days=7)

    pedidos_expirados = PedidoSeguir.query.filter(
        PedidoSeguir.created_at < limite,
        PedidoSeguir.status == 'pendente'
    ).all()

    for pedido in pedidos_expirados:
        db.session.delete(pedido)

    db.session.commit()

    flash(f"{len(pedidos_expirados)} pedidos expirados foram removidos.")
    return redirect(url_for("main.conexoes"))