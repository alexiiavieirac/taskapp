from flask import current_app, render_template, request, flash, redirect, url_for, session
from flask_login import login_user, logout_user, login_required
from flask_mail import Message
from werkzeug.security import generate_password_hash, check_password_hash
# CORREÇÃO: Importar 'db' diretamente de app.extensions
from app.extensions import db # <--- AQUI ESTÁ A MUDANÇA
from app.extensions import mail
from app.extensions.serializer import generate_token, confirm_token
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
        novo_usuario = Usuario(nome=nome, email=email, senha=senha_hash, grupo_id=grupo.id, grupo_original_id=grupo.id, email_verificado=False)
        db.session.add(novo_usuario)
        db.session.commit()

        # Gera token de confirmação
        token = generate_token(novo_usuario.email)
        confirm_url = url_for('main.confirmar_email', token=token, _external=True)

        # Envia o e-mail de confirmação
        msg = Message("Confirme seu cadastro", recipients=[novo_usuario.email])  # E-mail do usuário
        msg.body = f"Olá {novo_usuario.nome}, clique no link para confirmar seu e-mail: {confirm_url}"
        msg.html = render_template("email/confirm_email.html", confirm_url=confirm_url, nome=novo_usuario.nome)
        
        try:
            mail.send(msg)
            flash("Um e-mail de confirmação foi enviado. Verifique sua caixa de entrada.", "register-info")
        except Exception as e:
            current_app.logger.error(f"Erro ao enviar e-mail: {e}")
            flash("Erro ao enviar o e-mail de confirmação. Tente novamente.", "register-danger")
            return redirect(url_for('main.register'))

        return redirect(url_for('main.aguardando_confirmacao'))

    return render_template("register.html")


@main_bp.route('/aguardando-confirmacao')
def aguardando_confirmacao():
    # Página que avisa para o usuário verificar o e-mail
    return render_template("aguardando_confirmacao.html")


@main_bp.route('/confirmar/<token>')
def confirmar_email(token):
    email = confirm_token(token)

    if not email:
        flash("O link de confirmação é inválido ou expirou.", "confirm-danger")
        return redirect(url_for('main.login'))

    usuario = Usuario.query.filter_by(email=email).first_or_404()

    if usuario.email_verificado:
        flash("Conta já confirmada. Faça login.", "confirm-info")
        return redirect(url_for('main.login'))

    usuario.email_verificado = True
    db.session.commit()
    flash("E-mail confirmado com sucesso! Agora você pode fazer login.", "confirm-success")
    return redirect(url_for('main.login'))


@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Rota para login de usuários
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and check_password_hash(usuario.senha, senha):
            if not usuario.email_verificado:
                flash("Você precisa verificar seu e-mail antes de fazer login.", "login-warning")
                return redirect(url_for('main.login'))

            login_user(usuario, remember=True)
            session['grupo_id'] = usuario.grupo_id
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
    return redirect(url_for('main.login'))


@main_bp.route('/esqueci-senha', methods=['GET', 'POST'])
def esqueci_senha():
    if request.method == "POST":
        email = request.form.get("email")

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario:
            # Gerar token de recuperação de senha
            token = generate_token(email)
            reset_url = url_for('main.resetar_senha', token=token, _external=True)

            # Enviar e-mail com link de recuperação
            msg = Message("Recuperação de Senha", recipients=[email])
            msg.body = f"Olá, clique no link para redefinir sua senha: {reset_url}"
            msg.html = render_template("email/reset_email.html", reset_url=reset_url)

            try:
                mail.send(msg)
                flash("E-mail de recuperação enviado. Verifique sua caixa de entrada.", "info")
            except Exception as e:
                current_app.logger.error(f"Erro ao enviar e-mail: {e}")
                flash("Erro ao enviar o e-mail de recuperação. Tente novamente.", "danger")
                return redirect(url_for('main.esqueci_senha'))

            return redirect(url_for('main.aguardando_email'))
        else:
            flash("E-mail não encontrado.", "danger")

    return render_template("esqueci_senha.html")


@main_bp.route('/resetar-senha/<token>', methods=['GET', 'POST'])
def resetar_senha(token):
    email = confirm_token(token)

    if not email:
        flash("O link de recuperação é inválido ou expirou.", "danger")
        return redirect(url_for('main.login'))

    usuario = Usuario.query.filter_by(email=email).first_or_404()

    if request.method == "POST":
        nova_senha = request.form.get("senha")
        confirmacao_senha = request.form.get("confirmar_senha")

        if nova_senha != confirmacao_senha:
            flash("As senhas não coincidem.", "danger")
            return redirect(url_for('main.resetar_senha', token=token))

        # Verificar se a nova senha é diferente da antiga
        if check_password_hash(usuario.senha, nova_senha):
            flash("A nova senha não pode ser igual à anterior.", "danger")
            return redirect(url_for('main.resetar_senha', token=token))

        # Valida a nova senha com a função padronizada
        if not validar_senha(nova_senha):
            flash("A nova senha deve ter entre 8 e 15 caracteres, incluindo uma letra maiúscula, um número e um caractere especial.", "danger")
            return redirect(url_for('main.resetar_senha', token=token))

        # Atualizar senha
        senha_hash = generate_password_hash(nova_senha)
        usuario.senha = senha_hash
        db.session.commit()

        flash("Senha alterada com sucesso. Faça login.", "success")
        return redirect(url_for('main.login'))

    return render_template("resetar_senha.html")


@main_bp.route('/aguardando-email')
def aguardando_email():
    return render_template("aguardando_email.html")