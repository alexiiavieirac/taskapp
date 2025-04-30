from flask import Blueprint

main_bp = Blueprint('main', __name__)

from app.controllers import (
    auth_controller,
    grupo_controller,
    tarefa_controller,
    ranking_controller,
    conexao_controller,
    historico_controller,
    configuracao_controller
)