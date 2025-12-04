# app/controllers/socket_events.py

from flask import request
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room
from datetime import datetime, timezone # Importar timezone para datetime.utcnow()

from app.extensions.socketio import socketio # Importa o objeto socketio
from app.extensions.database import db # Importa a instância do seu SQLAlchemy
from app.models.chat_message import ChatMessage # Seu novo modelo ChatMessage
from app.models.usuario import Usuario # Para obter o nome do usuário
from app.models.group import Grupo # Para obter o nome do grupo

# Evento de conexão
@socketio.on('connect')
def handle_connect():
    # Nota: current_user funciona em contexto de requisição HTTP. Para SocketIO,
    # pode ser necessário configurar a extensão Flask-Login-SocketIO ou passar
    # explicitamente dados do usuário na conexão ou eventos.
    # Assumimos por enquanto que current_user está disponível aqui.
    print(f'Cliente conectado: {request.sid}')

# Evento de desconexão
@socketio.on('disconnect')
def handle_disconnect():
    print(f'Cliente desconectado: {request.sid}')

# Evento para o usuário entrar em uma sala de chat (baseada no grupo_id)
@socketio.on('join')
def handle_join(data):
    group_id = data.get('group_id')
    
    # Adicionando uma verificação robusta para current_user
    if not current_user.is_authenticated:
        print(f"Usuário não autenticado tentando entrar na sala.")
        emit('error', {'message': 'Você precisa estar logado para entrar no chat.'}, room=request.sid)
        return
    
    # current_user.grupo_id pode ser None se o usuário não tiver um grupo
    if not current_user.grupo_id:
        print(f"Usuário {current_user.id} não possui um grupo atribuído.")
        emit('error', {'message': 'Você não faz parte de nenhum grupo de chat.'}, room=request.sid)
        return

    if not group_id or current_user.grupo_id != group_id:
        print(f"Erro ao tentar entrar na sala: user {current_user.id} tentou grupo {group_id}, mas está no grupo {current_user.grupo_id}")
        emit('error', {'message': 'ID de grupo inválido ou você não pertence a este grupo.'}, room=request.sid)
        return

    room = str(group_id) # Salas são identificadas por strings
    join_room(room)
    print(f'Usuário {current_user.nome} ({current_user.id}) entrou na sala {room}')

    # Carregar histórico de mensagens
    # Busque as últimas N mensagens do grupo (ex: 50 últimas)
    messages_history = ChatMessage.query \
        .filter_by(grupo_id=group_id) \
        .order_by(ChatMessage.timestamp.asc()) \
        .limit(50) \
        .all()
    
    # Formatar as mensagens para enviar ao cliente
    formatted_messages = []
    for msg in messages_history:
        sender = Usuario.query.get(msg.usuario_id)
        formatted_messages.append({
            'username': sender.nome if sender else 'Desconhecido',
            'message': msg.message,
            'user_id': msg.usuario_id, # <--- ENVIANDO user_id
            'timestamp': msg.timestamp.isoformat()
        })
    
    # Envia o histórico APENAS para o cliente que se conectou
    emit('history', formatted_messages, room=request.sid) 

    # Notificar outros membros do grupo que um usuário se juntou (opcional)
    # emit('message', {'username': 'Sistema', 'message': f'{current_user.nome} entrou no chat.', 'timestamp': datetime.now(timezone.utc).isoformat(), 'user_id': -1}, room=room) # Use -1 para user_id de sistema

# Evento para o usuário sair da sala (opcional, SocketIO lida com isso em disconnect)
@socketio.on('leave')
def handle_leave(data):
    group_id = data.get('group_id')
    if not group_id:
        return
    room = str(group_id)
    leave_room(room)
    print(f'Usuário {current_user.nome} ({current_user.id}) saiu da sala {room}')

# Evento para receber e retransmitir mensagens
@socketio.on('send_message')
def handle_send_message(data):
    group_id = data.get('group_id')
    message_content = data.get('message')

    # Verificações de segurança e autenticação
    if not current_user.is_authenticated:
        emit('error', {'message': 'Você precisa estar logado para enviar mensagens.'}, room=request.sid)
        return
    if not current_user.grupo_id or current_user.grupo_id != group_id:
        emit('error', {'message': 'Você não faz parte deste grupo de chat.'}, room=request.sid)
        return
    if not group_id or not message_content:
        emit('error', {'message': 'Mensagem ou ID de grupo inválido.'}, room=request.sid)
        return

    # Salvar a mensagem no banco de dados
    new_message = ChatMessage(
        grupo_id=group_id,
        usuario_id=current_user.id,
        message=message_content,
        timestamp=datetime.now(timezone.utc) # Use datetime.now(timezone.utc) para consistência
    )
    db.session.add(new_message)
    db.session.commit()

    # Emitir a mensagem para todos os clientes na mesma sala,
    # incluindo o remetente. O cliente decidirá se é 'self' ou 'other'.
    room = str(group_id)
    emit('message', {
        'username': current_user.nome,
        'message': message_content,
        'timestamp': new_message.timestamp.isoformat(),
        'user_id': current_user.id # <--- AGORA ENVIAMOS O ID DO REMETENTE
    }, room=room) # Emite para TODOS na sala, incluindo o remetente.
    # O cliente (JavaScript no base.html) usará 'user_id' para determinar 'is_self'.
