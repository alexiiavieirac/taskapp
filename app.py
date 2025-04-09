import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import Conexao, PedidoGrupo, SolicitacaoGrupo, db, Usuario, Grupo, Tarefa
from datetime import datetime
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import func

# Configurações do Flask
app = Flask(__name__)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'lekacvieira@gmail.com'
app.config['MAIL_PASSWORD'] = 'hwhg tixs wjvz wzfb'
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
    
    if request.method == "POST":
        descricao = request.form["descricao"]
        imagem = request.files.get("imagem")
        nome_imagem = None

        if imagem and imagem.filename != "":
            nome_imagem = secure_filename(imagem.filename)
            imagem.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_imagem))

        nova_tarefa = Tarefa(
            descricao=descricao,
            imagem=nome_imagem,
            grupo_id=grupo_id
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

    # Lista de membros do grupo atual
    membros = Usuario.query.filter_by(grupo_id=grupo.id).all()

    # Consulta para obter o ranking por número de tarefas concluídas
    ranking = db.session.query(
        Usuario.nome,
        db.func.count(Tarefa.id).label('tarefas_concluidas')
    ).join(Tarefa, Tarefa.usuario_id == Usuario.id) \
     .filter(
         Usuario.grupo_id == grupo.id,
         Tarefa.concluida == True
     ).group_by(Usuario.id, Usuario.nome) \
     .order_by(db.desc('tarefas_concluidas')) \
     .all()

    return render_template("grupo.html", grupo=grupo, membros=membros, ranking=ranking)

# Rota de Ranking - Mostrar o ranking de tarefas concluídas por grupo, ordenado do maior para o menor número de tarefas concluídas.
@app.route("/ranking")
def ranking():
    grupo_id = current_user.grupo_id

    ranking = db.session.query(
        Usuario.nome,
        db.func.count(Tarefa.id).label('tarefas_concluidas')
    ).join(Tarefa, Tarefa.usuario_id == Usuario.id) \
    .filter(
        Usuario.grupo_id == grupo_id,
        Tarefa.concluida == True,
        Tarefa.ativa == True
    ).group_by(Usuario.id, Usuario.nome) \
    .order_by(db.desc('tarefas_concluidas')) \
    .all()

    return render_template("ranking.html", ranking=ranking)

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
@app.route("/concluir/<int:id>")
def concluir(id):
    tarefa = Tarefa.query.get_or_404(id)

    # Impede qualquer tentativa de desmarcar a tarefa, mesmo pelo próprio usuário
    if tarefa.concluida:
        flash("Tarefa já foi concluída e não pode ser desmarcada.")
        return redirect("/")

    # Impede que o usuário conclua uma tarefa já atribuída a outro usuário
    if tarefa.usuario_id and tarefa.usuario_id != current_user.id:
        flash("Essa tarefa já está atribuída a outro usuário.")
        return redirect("/")

    # Marca como concluída e associa o usuário atual
    tarefa.concluida = True
    tarefa.usuario_id = current_user.id

    db.session.commit()
    flash("Tarefa concluída com sucesso!")
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
def editar(id):
    tarefa = Tarefa.query.get_or_404(id)

    if request.method == "POST":
        tarefa.descricao = request.form["descricao"]
        nova_imagem = request.files.get("imagem")

        if nova_imagem and nova_imagem.filename != "":
            if tarefa.imagem:
                caminho = os.path.join(app.config['UPLOAD_FOLDER'], tarefa.imagem)
                if os.path.exists(caminho):
                    os.remove(caminho)

            nome_imagem = secure_filename(nova_imagem.filename)
            nova_imagem.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_imagem))
            tarefa.imagem = nome_imagem  
        db.session.commit()
        return redirect("/")

    return render_template("editar.html", tarefa=tarefa)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  
    app.run(debug=True)
