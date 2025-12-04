# app/controllers/main_controller.py

from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta

# Importe o Blueprint que você definiu em app/controllers/__init__.py
from app.controllers import main_bp

# IMPORTANTE: Importe seus modelos e a instância do seu banco de dados aqui!
# Se você usa SQLAlchemy, pode ser algo como:
from app.extensions import db # Se db estiver em app/extensions.py
from app.models import Tarefa, Usuario, Grupo # Ajuste conforme onde seus modelos estão definidos

# Se você também tiver funções de utilidade como secure_filename ou obter_limites_semana
# from werkzeug.utils import secure_filename
# import os
# from flask import current_app
# from app.utils import obter_limites_semana, adicionar_tarefa, TAREFAS_PRE_ESTABELECIDAS


@main_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    today_date_utc = datetime.utcnow().date()
    current_display_date_str = request.args.get('date')

    if current_display_date_str:
        current_display_date = datetime.strptime(current_display_date_str, '%Y-%m-%d').date()
    else:
        current_display_date = today_date_utc

    if request.method == 'POST':
        descricao = request.form.get('descricao')
        imagem_file = request.files.get('imagem')

        if descricao:
            # --- SUA LÓGICA EXISTENTE PARA ADICIONAR TAREFAS AQUI ---
            # Exemplo com SQLAlchemy:
            # nova_tarefa = Tarefa(descricao=descricao, usuario_id=current_user.id,
            #                     grupo_id=current_user.grupo_id, data=current_display_date, concluida=False)
            # if imagem_file and imagem_file.filename != '':
            #     # Lógica para salvar imagem (requer 'current_app' e 'os' importados, e 'UPLOAD_FOLDER' configurado)
            #     # filename = secure_filename(imagem_file.filename)
            #     # upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
            #     # os.makedirs(upload_folder, exist_ok=True)
            #     # filepath = os.path.join(upload_folder, filename)
            #     # imagem_file.save(filepath)
            #     # nova_tarefa.imagem = filename
            #     pass # Remova este 'pass' e adicione sua lógica de imagem
            # db.session.add(nova_tarefa)
            # db.session.commit()
            flash('Tarefa adicionada!', 'success')
            return redirect(url_for('main.index', date=current_display_date.strftime('%Y-%m-%d')))
        else:
            flash('A descrição da tarefa não pode estar vazia.', 'danger')

    # Lógica para display_date_text (Ontem, Hoje, DD/MM/YYYY)
    if current_display_date == today_date_utc:
        display_date_text = "Hoje"
    elif current_display_date == today_date_utc - timedelta(days=1):
        display_date_text = "Ontem"
    else:
        display_date_text = current_display_date.strftime('%d/%m/%Y')

    is_past_date = current_display_date < today_date_utc

    # --- SUA LÓGICA EXISTENTE PARA BUSCAR TAREFAS AQUI ---
    # Exemplo com SQLAlchemy:
    tarefas = [] # Substitua por sua query real
    # if current_user.is_authenticated:
    #     # Busca as próprias tarefas do usuário para a data
    #     minhas_tarefas = Tarefa.query.filter_by(
    #         usuario_id=current_user.id,
    #         data=current_display_date
    #     ).order_by(Tarefa.concluida.asc(), Tarefa.id.desc()).all()
    #
    #     tarefas = minhas_tarefas
    #
    #     # Se o usuário está em um grupo, busca tarefas dos outros membros do grupo
    #     if current_user.grupo_id:
    #         tarefas_grupo = Tarefa.query.filter_by(
    #             grupo_id=current_user.grupo_id,
    #             data=current_display_date
    #         ).filter(Tarefa.usuario_id != current_user.id) \
    #          .order_by(Tarefa.concluida.asc(), Tarefa.id.desc()).all()
    #         tarefas.extend(tarefas_grupo)


    # --- Lógica de Notificações (substitua com sua lógica real) ---
    total_notificacoes = 0
    notificacoes = {'grupo': 0, 'seguidores': 0}
    # Exemplo:
    # if current_user.is_authenticated:
    #     total_notificacoes = SolicitacaoGrupo.query.filter_by(usuario_alvo_id=current_user.id, status='pendente').count() + \
    #                          PedidoSeguir.query.filter_by(usuario_seguido_id=current_user.id, status='pendente').count()
    #     notificacoes['grupo'] = SolicitacaoGrupo.query.filter_by(usuario_alvo_id=current_user.id, status='pendente').count()
    #     notificacoes['seguidores'] = PedidoSeguir.query.filter_by(usuario_seguido_id=current_user.id, status='pendente').count()


    # --- Lógica para o CHAT WIDGET: Buscar Membros do Grupo ---
    grupo_members = []
    if current_user.is_authenticated and current_user.grupo_id:
        # ATENÇÃO: SUBSTITUA ISSO PELA SUA LÓGICA REAL DE BUSCAR MEMBROS DO GRUPO
        # Exemplo com SQLAlchemy:
        grupo_members = Usuario.query.filter_by(grupo_id=current_user.grupo_id).all()
        # Filtra o próprio usuário da lista que será exibida para os "outros membros" no template
        grupo_members = [member for member in grupo_members if member.id != current_user.id]

    return render_template('index.html',
                           current_user=current_user,
                           tarefas=tarefas,
                           current_display_date=current_display_date,
                           today_date_utc=today_date_utc,
                           display_date_text=display_date_text,
                           is_past_date=is_past_date,
                           total_notificacoes=total_notificacoes,
                           notificacoes=notificacoes,
                           grupo_members=grupo_members) # PASSE A LISTA DE MEMBROS AQUI