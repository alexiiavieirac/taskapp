import re
from flask import app, current_app, render_template, request, flash, redirect, url_for
from werkzeug.security import generate_password_hash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.controllers import main_bp
import os

from app.extensions.uploads import allowed_file


@main_bp.route('/configuracoes', methods=["GET", "POST"])
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
            if allowed_file(avatar_file.filename):
                filename = secure_filename(avatar_file.filename)
                path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                avatar_file.save(path)
                current_user.avatar = filename
            else:
                flash("Formato de imagem não permitido. Use JPG, PNG ou GIF.", "danger")
                return redirect(url_for('main.configuracoes'))

        db.session.commit()
        flash("Configurações atualizadas com sucesso!", "success")
        return redirect(url_for('main.configuracoes'))

    return render_template("configuracoes.html")


@main_bp.route('/change_password', methods=["GET", "POST"])
@login_required
def mudar_senha():
    if request.method == "POST":
        nova_senha = request.form['nova_senha']
        confirmar_senha = request.form['confirmar_senha']

        if nova_senha != confirmar_senha:
            flash("❌ As senhas não coincidem.", "danger")
            return redirect(url_for('main.mudar_senha'))

        # Validação de senha
        senha_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,15}$'
        if not re.match(senha_regex, nova_senha):
            flash("❌ A senha deve ter entre 8 e 15 caracteres, com letras maiúsculas, minúsculas e caracteres especiais.", "danger")
            return redirect(url_for('main.mudar_senha'))

        # Atualiza a senha
        current_user.senha = generate_password_hash(nova_senha)
        db.session.commit()
        flash("Senha alterada com sucesso!", "success")
        return redirect(url_for('main.configuracoes'))

    return render_template("mudar_senha.html")
