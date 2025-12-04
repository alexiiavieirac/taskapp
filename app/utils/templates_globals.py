# app/utils/template_globals.py

from flask import current_app
from flask_login import current_user
from datetime import datetime, timedelta, timezone

# Importar modelos *dentro* da função para evitar circular imports se os modelos
# precisarem do app_context (como db.init_app(app)) durante a importação.
# Se os modelos são definidos de forma que 'db' já está inicializado quando eles são importados,
# você pode importá-los globalmente no topo. Para segurança, mantenho a importação local.

def inject_global_data():
    global_data = {}

    # Variáveis relacionadas a datas e horas
    global_data['datetime'] = datetime
    global_data['timedelta'] = timedelta
    global_data['timezone'] = timezone
    global_data['today_date_utc'] = datetime.now(timezone.utc).date()

    # Variáveis relacionadas ao usuário logado e grupo
    if current_user.is_authenticated and current_user.grupo_id:
        # Importa 'db' aqui, já que 'init_db' já terá sido chamado em create_app
        from app.extensions.database import db
        from app.models.usuario import Usuario
        from app.models.group import Grupo

        grupo_members = Usuario.query.filter_by(grupo_id=current_user.grupo_id).all()
        global_data['grupo_members'] = grupo_members
        
        # Obter o nome do grupo para o chat
        grupo_obj = Grupo.query.get(current_user.grupo_id)
        global_data['current_user_group_name'] = grupo_obj.nome if grupo_obj else "Meu Grupo"

        # Calcular notificações globais
        # Se estas consultas são intensivas, considere cacheá-las ou passá-las apenas
        # onde são estritamente necessárias (como na view que renderiza o menu).
        # Para um exemplo global, as incluímos aqui.
        from app.models.group import SolicitacaoGrupo
        from app.models.usuario import PedidoSeguir
        from app.models.connection import Conexao

        pedidos_seguir = PedidoSeguir.query.filter_by(destinatario_id=current_user.id, status="pendente").all()
        pedidos_grupo = SolicitacaoGrupo.query.filter_by(grupo_id=current_user.grupo_id, status="pendente").all()
        conexoes = Conexao.query.filter_by(seguido_id=current_user.id).all()  # Verifique se 'conexoes' faz sentido aqui para badge

        pedidos_seguir_count = sum(1 for pedido in pedidos_seguir if not pedido.visto)
        pedidos_grupo_count = sum(1 for pedido in pedidos_grupo if not pedido.visto)
        conexoes_count = sum(1 for conexao in conexoes if not conexao.visto) # Depende da lógica de visto

        global_data['notificacoes'] = {
            "grupo": pedidos_grupo_count,
            "seguidores": pedidos_seguir_count,
            "conexoes": conexoes_count
        }
        global_data['total_notificacoes'] = pedidos_seguir_count + pedidos_grupo_count + conexoes_count
    else:
        global_data['grupo_members'] = []
        global_data['current_user_group_name'] = "Nenhum Grupo"
        global_data['notificacoes'] = {"grupo": 0, "seguidores": 0, "conexoes": 0}
        global_data['total_notificacoes'] = 0

    return global_data
