import os

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def configure_uploads(app):
    # Caminho absoluto para a pasta de uploads dentro de static
    upload_folder = os.path.join(app.root_path, 'static', 'uploads')
    app.config['UPLOAD_FOLDER'] = upload_folder
    app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS
    # Cria a pasta de uploads se ela não existir
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    # Verifica se o arquivo tem um ponto e se a extensão está na lista permitida
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS