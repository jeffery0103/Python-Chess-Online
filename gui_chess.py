# In gui_chess.py (WebSocket Version)
import pygame
import chess_game
import socketio # NEW! 引入新的函式庫
import threading

# --- 常數設定 (不變) ---
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 800
BOARD_SIZE = SCREEN_WIDTH
SQUARE_SIZE = BOARD_SIZE // 8
COLOR_WHITE = (238, 238, 210)
COLOR_BLACK = (118, 150, 86)
HIGHLIGHT_COLOR = (255, 255, 51, 150)
POSSIBLE_MOVE_COLOR = (0, 0, 0, 70)
PIECE_MAPPING = {
    'P': 'w_pawn', 'R': 'w_rook', 'N': 'w_knight', 'B': 'w_bishop', 'Q': 'w_queen', 'K': 'w_king',
    'p': 'b_pawn', 'r': 'b_rook', 'n': 'b_knight', 'b': 'b_bishop', 'q': 'b_queen', 'k': 'b_king'
}

# --- 繪圖函式 (維持原樣) ---
def load_piece_images():
    images = {}
    for piece_char, piece_key in PIECE_MAPPING.items():
        path = f"images/{piece_key}.png"
        image = pygame.image.load(path); images[piece_char] = pygame.transform.scale(image, (SQUARE_SIZE, SQUARE_SIZE))
    return images
def draw_board(screen):
    for row in range(8):
        for col in range(8):
            color = COLOR_WHITE if (row + col) % 2 == 0 else COLOR_BLACK
            pygame.draw.rect(screen, color, [col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE])
def draw_pieces(screen, board_state, piece_images):
    for row in range(8):
        for col in range(8):
            piece = board_state[row][col]
            if piece != '.': screen.blit(piece_images[piece], (col * SQUARE_SIZE, row * SQUARE_SIZE))
def draw_highlights(screen, selected_pos, valid_moves):
    if selected_pos:
        row, col = selected_pos; s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA); s.fill(HIGHLIGHT_COLOR)
        screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))
    for move in valid_moves:
        row, col = move[1]; s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(s, POSSIBLE_MOVE_COLOR, (SQUARE_SIZE // 2, SQUARE_SIZE // 2), SQUARE_SIZE // 6)
        screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))
def draw_message(screen, font, message):
    text_surf = font.render(message, True, (200, 20, 20))
    bg_rect = pygame.Rect(0, 0, text_surf.get_width() + 40, text_surf.get_height() + 40)
    bg_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    bg_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA); bg_surf.fill((0, 0, 0, 180))
    screen.blit(bg_surf, bg_rect.topleft)
    text_rect = text_surf.get_rect(center=bg_rect.center)
    screen.blit(text_surf, text_rect)

# --- 主程式 (WebSocket 大改造) ---
def main():
    # 1. 初始化 & 資源載入
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    font = pygame.font.SysFont("Arial", 50, bold=True)
    pygame.display.set_caption("華麗的西洋棋！正在連線...")
    piece_images = load_piece_images()
    game_board = chess_game.Board()

    # 2. NEW! 連線到 WebSocket 伺服器
    sio = socketio.Client()
    
    # 3. NEW! 定義事件處理器
    game_state = {'status': 'connecting', 'room': None, 'my_color': None}

    @sio.event
    def connect():
        print("成功連線到伺服器！正在加入遊戲...")
        sio.emit('join_game', {'username': 'Player'})

    @sio.event
    def disconnect():
        print("與伺服器斷線！"); game_state['status'] = 'disconnected'

    @sio.on('waiting_for_player')
    def on_waiting(data):
        game_state['status'] = 'waiting'; game_state['room'] = data['room']; game_state['my_color'] = 'white'
        pygame.display.set_caption(f"等待對手... (你是白方)")

    @sio.on('game_start')
    def on_game_start(data):
        game_state['status'] = 'playing'; game_state['room'] = data['room']
        # 伺服器會告訴我們誰是白方誰是黑方
        game_state['my_color'] = 'white' if sio.sid == data['white'] else 'black'
        pygame.display.set_caption(f"遊戲進行中！你是 {game_state['my_color']} 方")

    @sio.on('opponent_moved')
    def on_opponent_moved(move):
        start_notation, end_notation = move
        print(f"收到對手棋步: {start_notation} -> {end_notation}")
        game_board.move_piece(start_notation, end_notation)

    @sio.on('opponent_disconnected')
    def on_opponent_disconnected():
        game_state['status'] = 'opponent_disconnected'

    # 4. 建立連線
    server_address = input("請輸入伺服器網址 (本地測試請用 http://127.0.0.1:5000): ")
    try: sio.connect(server_address)
    except Exception as e: print(f"連線失敗: {e}"); return

    # 5. 狀態變數
    selected_piece_pos = None; valid_moves_for_piece = []
    
    running = True
    while running:
        # 事件處理
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            
            if game_state['status'] == 'playing' and game_board.current_turn == game_state['my_color']:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pixel_pos = pygame.mouse.get_pos(); col = pixel_pos[0] // SQUARE_SIZE; row = pixel_pos[1] // SQUARE_SIZE
                    clicked_pos = (row, col)

                    if selected_piece_pos:
                        is_a_valid_move = any(move[1] == clicked_pos for move in valid_moves_for_piece)
                        if is_a_valid_move:
                            start_notation = game_board.coords_to_notation(selected_piece_pos)
                            end_notation = game_board.coords_to_notation(clicked_pos)
                            sio.emit('move', {'room': game_state['room'], 'move': (start_notation, end_notation)})
                            game_board.move_piece(start_notation, end_notation)
                        selected_piece_pos = None; valid_moves_for_piece = []
                    else:
                        piece = game_board.get_piece(clicked_pos)
                        if piece != '.' and (piece.isupper() if game_state['my_color'] == 'white' else piece.islower()):
                            selected_piece_pos = clicked_pos
                            all_legal_moves = game_board.generate_legal_moves(game_board.current_turn)
                            valid_moves_for_piece = [move for move in all_legal_moves if move[0] == selected_piece_pos]

        # 繪製畫面
        draw_board(screen)
        draw_highlights(screen, selected_piece_pos, valid_moves_for_piece)
        draw_pieces(screen, game_board.board, piece_images)

        # 繪製狀態訊息
        if game_state['status'] == 'waiting':
             draw_message(screen, font, "等待對手加入...")
        elif game_state['status'] == 'opponent_disconnected':
             draw_message(screen, font, "對手已斷線！")
        # 這裡可以加入更多遊戲結束的判斷與繪圖

        pygame.display.flip()

    sio.disconnect()
    pygame.quit()

if __name__ == '__main__':
    main()