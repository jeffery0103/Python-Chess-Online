from flask import Flask
from flask_socketio import SocketIO, emit, join_room, leave_room, send
from flask import request # NEW! We need to import 'request' to get the session ID

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a_super_secret_key_that_no_one_will_guess'
socketio = SocketIO(app, cors_allowed_origins="*")

rooms = {}
sid_to_room = {}

# UPDATED! This function now correctly accepts the connection arguments but we don't need them.
@socketio.on('connect')
def handle_connect(auth):
    print(f'一個客戶端連線了！ SID: {request.sid}')

# UPDATED! This function now correctly accepts disconnect arguments.
@socketio.on('disconnect')
def handle_disconnect():
    print(f'一個客戶端斷線了！ SID: {request.sid}')
    room_id = sid_to_room.get(request.sid)
    if room_id and room_id in rooms:
        emit('opponent_disconnected', room=room_id, include_self=False)
        # Clean up room info
        if room_id in rooms:
             del rooms[room_id]
    if request.sid in sid_to_room:
        del sid_to_room[request.sid]

@socketio.on('join_game')
def handle_join_game(data):
    username = data.get('username', '匿名玩家')
    
    available_room = None
    for room_id, players in rooms.items():
        if len(players) == 1:
            available_room = room_id
            break
            
    if available_room:
        # UPDATED! Use request.sid to track the new player
        join_room(available_room)
        rooms[available_room].append(request.sid)
        sid_to_room[request.sid] = available_room
        print(f"玩家 {username} ({request.sid}) 加入了房間 {available_room}")
        emit('game_start', {'room': available_room, 'white': rooms[available_room][0], 'black': rooms[available_room][1]}, room=available_room)
    else:
        # UPDATED! Use request.sid to create the new room
        new_room_id = f"room_{request.sid}"
        join_room(new_room_id)
        rooms[new_room_id] = [request.sid]
        sid_to_room[request.sid] = new_room_id
        print(f"玩家 {username} ({request.sid}) 建立了新房間 {new_room_id}")
        emit('waiting_for_player', {'room': new_room_id})

@socketio.on('move')
def handle_move(data):
    room = data['room']
    move = data['move']
    print(f"收到來自房間 {room} 的棋步: {move}")
    emit('opponent_moved', move, room=room, include_self=False)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)