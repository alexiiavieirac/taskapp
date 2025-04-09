import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import Conexao, PedidoGrupo, SolicitacaoGrupo, db, Usuario, Grupo, Tarefa
from datetime import datetime
from werkzeug.utils import secure_filename

# Configurações do Flask
app = Flask(__name__)

app.config['SECRET_KEY'] = 'chave-super-secreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Inicializa db e migrate
db.init_app(app)
migrate = Migrate(app, db)

# Inicializa o LoginManager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

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
    if request.method == "POST":
        descricao = request.form["descricao"]
        imagem = request.files.get("imagem")
        nome_imagem = None

        if imagem and imagem.filename != "":
            nome_imagem = secure_filename(imagem.filename)
            imagem.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_imagem))

        grupo_id = session.get('grupo_id')

        if not grupo_id:
            flash("Você precisa estar logado para criar uma tarefa.")
            return redirect("/login")

        nova_tarefa = Tarefa(descricao=descricao, imagem=nome_imagem, grupo_id=grupo_id)

        db.session.add(nova_tarefa)
        db.session.commit()
        return redirect("/")

    grupo_id = session.get('grupo_id')

    if not grupo_id:
        flash("Login necessário.")
        return redirect("/login")

    tarefas = Tarefa.query.filter_by(grupo_id=grupo_id).order_by(Tarefa.data_criacao).all()
    
    return render_template("index.html", tarefas=tarefas, grupo_id=grupo_id)

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
    membros = Usuario.query.filter_by(grupo_id=grupo.id).all()
    
    ranking = db.session.query(
        Usuario,
        db.func.count(Tarefa.id).label('tarefas_concluidas')
    ).join(Tarefa, Tarefa.usuario_id == Usuario.id) \
     .filter(
         Usuario.grupo_id == grupo.id,
         Tarefa.concluida == True
     ).group_by(Usuario.id).order_by(db.desc('tarefas_concluidas')).all()
    
    return render_template('grupo.html', grupo=grupo, membros=membros, ranking=ranking)

# Rota de Ranking - Mostrar o ranking de tarefas concluídas por grupo, ordenado do maior para o menor número de tarefas concluídas.
@app.route("/ranking")
def ranking():
    ranking = db.session.query(
        Usuario,
        db.func.count(Tarefa.id).label('tarefas_concluidas')
    ).join(Tarefa, Tarefa.usuario_id == Usuario.id) \
     .filter(Tarefa.concluida == True) \
     .group_by(Usuario.id).order_by(db.desc('tarefas_concluidas')).all()
    return render_template('ranking.html', ranking=ranking)

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
    tarefa.concluida = not tarefa.concluida
    db.session.commit()
    return redirect("/")

@app.route("/deletar/<int:id>")
def deletar(id):
    tarefa = Tarefa.query.get_or_404(id)

    if tarefa.imagem:
        caminho = os.path.join(app.config['UPLOAD_FOLDER'], tarefa.imagem)
        try:
            if os.path.exists(caminho):
                os.remove(caminho)
        except Exception as e:
            print(f"Erro ao deletar imagem: {e}")

    db.session.delete(tarefa)
    db.session.commit()
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
