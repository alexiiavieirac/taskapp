from flask import render_template, request, flash, redirect, url_for, session
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.utils.network_utils import is_safe_url
from app.models import Usuario, Grupo
from app.utils.auth_utils import validar_senha
from app.controllers import main_bp


@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    # Rota para registro de novos usuários
    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email")
        senha = request.form.get("senha")
        grupo_nome = request.form.get("grupo")

        # Valida a senha
        if not validar_senha(senha):
            flash("A senha deve ter entre 8 e 15 caracteres, incluindo uma letra maiúscula, um número e um caractere especial.", "register-danger")
            return redirect(url_for('main.register'))

        # Verifica se o e-mail já está cadastrado
        if Usuario.query.filter_by(email=email).first():
            flash("Este e-mail já está registrado. Faça login ou use outro e-mail.", "register-warning")
            return redirect(url_for('main.register'))

        # Sempre cria um novo grupo, mesmo que o nome já exista
        grupo = Grupo(nome=grupo_nome)
        db.session.add(grupo)
        db.session.commit()

        # Cria novo usuário com senha criptografada
        senha_hash = generate_password_hash(senha)
        novo_usuario = Usuario(nome=nome, email=email, senha=senha_hash, grupo_id=grupo.id, grupo_original_id=grupo.id)
        db.session.add(novo_usuario)
        db.session.commit()

        # Login automático após registro
        login_user(novo_usuario)
        session['grupo_id'] = novo_usuario.grupo_id
        flash("Usuário registrado e logado com sucesso!", "register-success")

        return redirect(url_for('main.index'))

    return render_template("register.html")


@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Rota para login de usuários
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and check_password_hash(usuario.senha, senha):
            login_user(usuario, remember=True)
            session['grupo_id'] = usuario.grupo_id
            flash('Login realizado com sucesso!', 'login-success')

            next_page = request.args.get('next')
            if next_page and is_safe_url(next_page):
                return redirect(next_page)
            return redirect(url_for('main.index'))
        else:
            flash("Email ou senha inválidos", "login-danger")

    return render_template("login.html")


@main_bp.route('/logout')
@login_required
def logout():
    # Rota para logout de usuários
    logout_user()
    session.pop('grupo_id', None)
    flash('Logout realizado com sucesso.', 'info')
    return redirect(url_for('main.login'))