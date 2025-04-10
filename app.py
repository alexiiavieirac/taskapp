import os
import re
from flask import Flask, abort, render_template, request, redirect, url_for, flash, session
from flask.cli import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import Conexao, HistoricoRanking, PedidoGrupo, SolicitacaoGrupo, TarefaPadrao, db, Usuario, Grupo, Tarefa
from datetime import datetime, timedelta
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import case, func

# Configurações do Flask
load_dotenv()

app = Flask(__name__)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'lekacvieira@gmail.com'
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
app.config['MAIL_DEFAULT_SENDER'] = 'lekacvieira@gmail.com'

app.config['SECRET_KEY'] = 'chave-super-secreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Inicializa db e migrate
db.init_app(app)
mail = Mail(app)
migrate = Migrate(app, db)

# Inicializa o LoginManager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# E-MAIL
@app.route("/enviar-convite", methods=["POST"])
@login_required
def enviar_convite():
    email_destino = request.form["email"]
    usuario_convidado = Usuario.query.filter_by(email=email_destino).first()
    
    if not usuario_convidado:
        flash("❌ Usuário não encontrado.", "danger")
        return redirect(url_for("grupo"))
    
    token = s.dumps({"email": email_destino, "grupo_id": current_user.grupo_id})

    link_aceite = url_for("aceitar_convite", token=token, _external=True)

    msg = Message("Convite para entrar no grupo", recipients=[email_destino])
    msg.body = f"Você foi convidado para entrar no grupo '{current_user.grupo.nome}'. Clique no link abaixo para aceitar:\n{link_aceite}"
    mail.send(msg)

    flash("✅ Convite enviado com sucesso!", "success")
    return redirect(url_for("grupo"))

# LOGIN, REGISTRO E LOGOUT

# Rota de erro para login
@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# Rota de Registro
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email")
        senha = request.form.get("senha")
        grupo_nome = request.form.get("grupo")

        # Valida a senha
        if not validar_senha(senha):
            flash("A senha deve ter entre 8 e 15 caracteres, incluindo uma letra maiúscula, um número e um caractere especial.", "danger")
            return redirect(url_for('register'))

        # Verifica se o e-mail já está cadastrado
        if Usuario.query.filter_by(email=email).first():
            flash("Este e-mail já está registrado. Faça login ou use outro e-mail.", "warning")
            return redirect(url_for('register'))

        # Cria grupo se ainda não existir
        grupo = Grupo.query.filter_by(nome=grupo_nome).first()
        if not grupo:
            grupo = Grupo(nome=grupo_nome)
            db.session.add(grupo)
            db.session.commit()

        # Cria novo usuário com senha criptografada
        senha_hash = generate_password_hash(senha)
        novo_usuario = Usuario(nome=nome, email=email, senha=senha_hash, grupo_id=grupo.id)
        db.session.add(novo_usuario)
        db.session.commit()

        # Login automático após registro
        login_user(novo_usuario)
        session['grupo_id'] = novo_usuario.grupo_id
        flash("Usuário registrado e logado com sucesso!", "success")

        return redirect(url_for('index'))

    return render_template("register.html")

# ROTA PARA SENHA
def validar_senha(senha):
    # Verifica se a senha atende aos requisitos
    if len(senha) < 8 or len(senha) > 15:
        return False
    if not re.search(r"[A-Z]", senha):  # Verifica se tem letra maiúscula
        return False
    if not re.search(r"[0-9]", senha):  # Verifica se tem número
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", senha):  # Verifica se tem caractere especial
        return False
    return True

# Rota de Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]

        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and check_password_hash(usuario.senha, senha):
            login_user(usuario)
            session['grupo_id'] = usuario.grupo_id
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))
        else:
            flash("Email ou senha inválidos", "danger")

    return render_template("login.html")

# Rota de Logout
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('Logout realizado com sucesso.', 'info')
    return redirect(url_for('login'))



# PARTE DA TAREFA E DAS IMAGENS

# Rota de Entrar no Sistema
@app.route('/', methods=["GET", "POST"])
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
            return redirect(url_for("index"))

        if imagem and imagem.filename != "":
            nome_imagem = secure_filename(imagem.filename)
            imagem.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_imagem))

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
        Tarefa.concluida == True
    ).group_by(Usuario.id, Usuario.nome) \
    .order_by(func.count(Tarefa.id).desc()) \
    .all()

    return render_template("index.html", tarefas=tarefas, grupo=grupo, membros=membros, grupo_id=grupo_id)

# ENVIO DE IMAGENS
@app.route("/imagem/<int:id>", methods=["POST"])
def enviar_imagem(id):
    tarefa = Tarefa.query.get_or_404(id)
    imagem = request.files.get("imagem")

    if imagem and imagem.filename != "":
        # Se já existe uma imagem antiga, deleta
        if tarefa.imagem:
            caminho_antigo = os.path.join(app.config['UPLOAD_FOLDER'], tarefa.imagem)
            if os.path.exists(caminho_antigo):
                os.remove(caminho_antigo)

        nome_imagem = secure_filename(imagem.filename)
        imagem.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_imagem))
        tarefa.imagem = nome_imagem
        db.session.commit()

    return redirect("/")



# GRUPO, CONEXÕES E RANKING

# Rota de Grupo - Mostrar os dados do grupo atual do usuário logado, incluindo: nome do grupo, lista de membros e ranking. 
@app.route("/grupo")
@login_required
def grupo():
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

# Rota de Ranking - Mostrar o ranking de tarefas concluídas por grupo, ordenado do maior para o menor número de tarefas concluídas.
@app.route("/ranking")
@login_required
def ranking():
    grupo_id = current_user.grupo_id
    inicio_semana, fim_semana = obter_limites_semana()
    agora = datetime.utcnow()

    # Ranking da semana atual (baseado em quem concluiu)
    ranking = db.session.query(
        Usuario.nome,
        func.count(Tarefa.id).label('tarefas_concluidas')
    ).outerjoin(Tarefa, Tarefa.concluida_por == Usuario.id) \
    .filter(
        Usuario.grupo_id == grupo_id,
        Tarefa.concluida == True,
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
                    semana=semana_label
                )
                db.session.add(novo_registro)
            db.session.commit()

    tempo_restante = fim_semana - agora

    return render_template("ranking.html", ranking=ranking, tempo_restante=tempo_restante)

@app.route("/historico")
@login_required
def historico():
    grupo_id = current_user.grupo_id

    data_str = request.args.get("data")
    if data_str:
        data = datetime.strptime(data_str, "%Y-%m-%d")
    else:
        data = datetime.utcnow()  # ou datetime.now() se usar horário local

    inicio_dia = datetime(data.year, data.month, data.day)
    fim_dia = inicio_dia + timedelta(days=1)

    tarefas_por_usuario = db.session.query(
        Usuario.nome,
        func.count(Tarefa.id).label("tarefas_concluidas")
    ).join(Tarefa, Tarefa.concluida_por == Usuario.id) \
    .filter(
        Usuario.grupo_id == grupo_id,
        Tarefa.concluida == True,
        Tarefa.data_criacao >= inicio_dia,
        Tarefa.data_criacao < fim_dia
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

# Rota de Adicionar-membro - Permitir que o usuário adicione um membro ao seu grupo informando o e-mail do usuário.
@app.route("/adicionar-membro", methods=["POST"])
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
    return redirect(url_for("dashboard"))

@app.route("/aceitar-convite/<token>")
def aceitar_convite(token):
    try:
        data = s.loads(token, max_age=3600)  # Token expira em 1 hora
        email = data["email"]
        grupo_id = data["grupo_id"]

        usuario = Usuario.query.filter_by(email=email).first()
        grupo = Grupo.query.get(grupo_id)

        if not usuario or not grupo:
            flash("❌ Usuário ou grupo não encontrados.", "danger")
            return redirect(url_for("login"))

        usuario.grupo_id = grupo.id
        db.session.commit()

        flash(f"🎉 Você agora faz parte do grupo '{grupo.nome}'!", "success")
        return redirect(url_for("login"))

    except Exception as e:
        print(e)
        flash("❌ Link inválido ou expirado.", "danger")
        return redirect(url_for("login"))

# Rota de Conexões - Mostra tela com: nome do usuário que segue, pessoas que seguem o usuário, lista de usuários para seguir.
@app.route("/conexoes")
@login_required
def conexoes():
    seguindo = current_user.seguindo.all()
    seguidores = current_user.seguidores.all()
    usuarios = Usuario.query.filter(Usuario.id != current_user.id).all()
    return render_template('conexoes.html', seguindo=seguindo, seguidores=seguidores, usuarios=usuarios)

# Rotas de Seguir - Permitir que o usuário logado siga outro usuário.
@app.route("/seguir/<int:usuario_id>")
@login_required
def seguir(usuario_id):
    conexao_existente = Conexao.query.filter_by(seguidor_id=current_user.id, seguido_id=usuario_id).first()
    if not conexao_existente:
        nova_conexao = Conexao(seguidor_id=current_user.id, seguido_id=usuario_id)
        db.session.add(nova_conexao)
        db.session.commit()
    flash("Agora você está seguindo essa pessoa!")
    return redirect(url_for('conexoes'))

# Rota de Entrar no Grupo - Enviar um pedido de entrada em um grupo específico.
@app.route("/entrar_grupo/<int:grupo_id>")
@login_required
def entrar_grupo(grupo_id):
    ja_enviado = SolicitacaoGrupo.query.filter_by(solicitante_id=current_user.id, grupo_id=grupo_id, status="pendente").first()
    if not ja_enviado:
        pedido = SolicitacaoGrupo(solicitante_id=current_user.id, grupo_id=grupo_id)
        db.session.add(pedido)
        db.session.commit()
    flash("Pedido enviado com sucesso.")
    return redirect(url_for("conexoes"))    

# Rota de Pedidos - Aceitar uma solicitação de entrada no grupo feita por outro usuário.
@app.route("/aceitar_pedido/<int:pedido_id>")
@login_required
def aceitar_pedido(pedido_id):
    pedido = SolicitacaoGrupo.query.get_or_404(pedido_id)
    if pedido.grupo_id == current_user.grupo_id:
        pedido.status = "aceito"
        usuario = Usuario.query.get(pedido.solicitante_id)
        usuario.grupo_id = pedido.grupo_id
        db.session.commit()
        flash("Pedido aceito!")
    return redirect(url_for("ver_pedidos"))

@app.route("/rejeitar_pedido/<int:pedido_id>")
@login_required
def rejeitar_pedido(pedido_id):
    pedido = SolicitacaoGrupo.query.get(pedido_id)
    
    if pedido and pedido.grupo_id == current_user.grupo_id:
        db.session.delete(pedido)
        db.session.commit()
    
    return redirect(url_for("pedidos"))

# Rota de Rejeitar Pedido - Listar todos os pedidos de entrada pendentes no grupo do usuário logado.
@app.route("/pedidos")
@login_required
def ver_pedidos():
    pedidos = SolicitacaoGrupo.query.filter_by(grupo_id=current_user.grupo_id, status="pendente").all()
    return render_template('pedidos.html', pedidos=pedidos)



# CONCLUIR, DELETAR E EDITAR TAREFAS
from datetime import datetime

@app.route("/concluir/<int:id>")
@login_required
def concluir(id):
    tarefa = Tarefa.query.get_or_404(id)

    # Verifica se o usuário pertence ao mesmo grupo
    if tarefa.grupo_id != current_user.grupo_id:
        abort(403)

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
            return redirect("/")
    else:
        # Marca como concluída por quem clicou
        tarefa.concluida = True
        tarefa.concluida_por = current_user.id
        tarefa.data_conclusao = datetime.utcnow()  # registra o momento
        flash("Tarefa concluída com sucesso!")

    db.session.commit()
    return redirect("/")

@app.route("/deletar/<int:id>")
def deletar(id):
    tarefa = Tarefa.query.get_or_404(id)

    # Verifica se o usuário pertence ao mesmo grupo
    if tarefa.grupo_id != current_user.grupo_id:
        flash("Você não pode excluir esta tarefa.")
        return redirect("/")

    # Marca como inativa, não deleta
    tarefa.ativa = False
    db.session.commit()
    flash("Tarefa excluída com sucesso.")
    return redirect("/")

@app.route('/editar/<int:id>', methods=["GET", "POST"])
@login_required
def editar(id):
    tarefa = Tarefa.query.get_or_404(id)

    # Verifica se o usuário atual é o criador da tarefa
    if tarefa.usuario_id != current_user.id:
        abort(403)  # Proibido

    if request.method == "POST":
        tarefa.descricao = request.form["descricao"].strip()
        nova_imagem = request.files.get("imagem")

        if nova_imagem and nova_imagem.filename != "":
            # Se já existe uma imagem antiga, remove ela
            if tarefa.imagem:
                caminho = os.path.join(app.config['UPLOAD_FOLDER'], tarefa.imagem)
                if os.path.exists(caminho):
                    os.remove(caminho)

            nome_imagem = secure_filename(nova_imagem.filename)
            nova_imagem.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_imagem))
            tarefa.imagem = nome_imagem

        db.session.commit()
        flash("Tarefa editada com sucesso!")
        return redirect("/")

    return render_template("editar.html", tarefa=tarefa)

# RANKING SEMANAL
def obter_limites_semana():
    hoje = datetime.utcnow()
    # weekday() retorna 0 (segunda) até 6 (domingo)
    dias_desde_domingo = (hoje.weekday() + 1) % 7  # transforma segunda=1 ... domingo=0
    inicio_semana = hoje - timedelta(days=dias_desde_domingo)
    inicio_semana = inicio_semana.replace(hour=0, minute=0, second=0, microsecond=0)
    fim_semana = inicio_semana + timedelta(days=6, hours=23, minutes=59, seconds=59)
    return inicio_semana, fim_semana

# SALVAR HISTORICO POR SEMANA
def salvar_historico_semanal():
    hoje = datetime.utcnow()
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

# TAREFAS PADROES
@app.route("/tarefas_diarias", methods=["GET", "POST"])
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

        # Adiciona tarefas selecionadas, se ainda não existirem
        for descricao in tarefas_selecionadas:
            existe = Tarefa.query.filter_by(
                descricao=descricao,
                grupo_id=current_user.grupo_id,
                ativa=True
            ).first()
            if not existe:
                nova = Tarefa(
                    descricao=descricao,
                    usuario_id=current_user.id,
                    grupo_id=current_user.grupo_id,
                    ativa=True,
                    concluida=False
                )
                db.session.add(nova)

        # Adiciona a nova tarefa personalizada, se não estiver nas pré-estabelecidas nem já no banco
        if nova_tarefa and nova_tarefa not in tarefas_pre_estabelecidas:
            existe_personalizada = Tarefa.query.filter_by(
                descricao=nova_tarefa,
                grupo_id=current_user.grupo_id,
                ativa=True
            ).first()
            if not existe_personalizada:
                nova = Tarefa(
                    descricao=nova_tarefa,
                    usuario_id=current_user.id,
                    grupo_id=current_user.grupo_id,
                    ativa=True,
                    concluida=False
                )
                db.session.add(nova)

        db.session.commit()
        flash("Tarefas adicionadas com sucesso!")
        return redirect(url_for("tarefas_diarias"))

    return render_template("tarefas_diarias.html", tarefas=tarefas_pre_estabelecidas)

# EXCLUIR TAREFA
@app.route("/excluir_tarefa/<int:id>", methods=["POST"])
@login_required
def excluir_tarefa(id):
    tarefa = Tarefa.query.get_or_404(id)

    # Verifica se a tarefa pertence ao grupo do usuário logado
    if tarefa.grupo_id != current_user.grupo_id:
        abort(403)

    # Impede a exclusão se a tarefa não tiver um dono definido
    if tarefa.usuario_id is None:
        flash("Essa tarefa padrão não pode ser excluída.")
        return redirect(url_for("index"))

    # Impede se o usuário atual não for o dono da tarefa (mesmo que tenha sido adicionada do tarefas_diarias)
    if tarefa.usuario_id != current_user.id:
        flash("Você não tem permissão para excluir esta tarefa.")
        return redirect(url_for("index"))

    # Marca como inativa ao invés de deletar
    tarefa.ativa = False
    db.session.commit()
    flash("Tarefa excluída com sucesso.")
    return redirect(url_for("index"))

# CONFIGURACOES
@app.route('/configuracoes', methods=["GET", "POST"])
@login_required
def configuracoes():
    if request.method == "POST":
        current_user.nome = request.form['nome']
        current_user.email = request.form['email']
        current_user.bio = request.form.get('bio')
        current_user.rede_social = request.form.get('rede_social')

        # Upload da foto
        avatar_file = request.files.get('avatar_file')
        if avatar_file and avatar_file.filename != "":
            filename = secure_filename(avatar_file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            avatar_file.save(path)
            current_user.avatar = filename  # Apenas o nome do arquivo

        db.session.commit()
        flash("Configurações atualizadas com sucesso!", "success")
        return redirect(url_for('configuracoes'))

    return render_template("configuracoes.html")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  
    app.run(debug=True)
