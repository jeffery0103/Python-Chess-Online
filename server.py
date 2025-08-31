# In server.py (WebSocket Version for Render)
from flask import Flask
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
# 這裡的 secret_key 不重要，但 Flask-SocketIO 需要它
app.config['SECRET_KEY'] = 'a_super_secret_key_that_no_one_will_guess'
# 允許所有來源連線，方便測試和部署
socketio = SocketIO(app, cors_allowed_origins="*")

# 遊戲房間的狀態管理 (用來儲存哪個房間有哪些玩家)
rooms = {}
# 用來追蹤每個玩家(sid)在哪個房間
sid_to_room = {}

@socketio.on('connect')
def handle_connect():
    print(f'一個客戶端連線了！ SID: {socketio.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    print(f'一個客戶端斷線了！ SID: {socketio.sid}')
    room_id = sid_to_room.get(socketio.sid)
    if room_id and room_id in rooms:
        # 通知房間裡的另一個玩家對手已斷線
        emit('opponent_disconnected', room=room_id, include_self=False)
        # 清理房間資訊
        del rooms[room_id]
    if socketio.sid in sid_to_room:
        del sid_to_room[socketio.sid]


@socketio.on('join_game')
def handle_join_game(data):
    username = data.get('username', '匿名玩家')
    
    # 尋找一個只有一個玩家在等待的房間
    available_room = None
    for room_id, players in rooms.items():
        if len(players) == 1:
            available_room = room_id
            break
            
    if available_room:
        # 加入現有房間 (成為黑方)
        join_room(available_room)
        rooms[available_room].append(socketio.sid)
        sid_to_room[socketio.sid] = available_room
        print(f"玩家 {username} ({socketio.sid}) 加入了房間 {available_room}")
        # 通知房間內的所有人，遊戲可以開始了
        # 白方是房間裡的第一個人，黑方是第二個
        emit('game_start', {'room': available_room, 'white': rooms[available_room][0], 'black': rooms[available_room][1]}, room=available_room)
    else:
        # 建立新房間 (成為白方)
        new_room_id = f"room_{socketio.sid}"
        join_room(new_room_id)
        rooms[new_room_id] = [socketio.sid]
        sid_to_room[socketio.sid] = new_room_id
        print(f"玩家 {username} ({socketio.sid}) 建立了新房間 {new_room_id}")
        emit('waiting_for_player', {'room': new_room_id})

@socketio.on('move')
def handle_move(data):
    room = data['room']
    move = data['move']
    print(f"收到來自房間 {room} 的棋步: {move}")
    # 把棋步轉發給同一個房間裡的「另一個」玩家
    emit('opponent_moved', move, room=room, include_self=False)

if __name__ == '__main__':
    # 用 eventlet 來啟動伺服器，這是 Render 部署需要的
    # Render 會自動找一個 PORT，我們本地測試可以用 5000
    socketio.run(app, host='0.0.0.0', port=5000)