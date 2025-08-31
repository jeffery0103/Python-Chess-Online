import copy # 引入 copy 函式庫，用來進行安全的棋盤模擬

class Board:
    def __init__(self):
        self.col_to_index = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
        self.index_to_col = {v: k for k, v in self.col_to_index.items()}
        self.board = [
            ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'], ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
            ['.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.'],
            ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'], ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
        ]
        self.current_turn = 'white'
        self.en_passant_target = None
        self.has_moved = {
            'w_king': False, 'b_king': False, 'w_rook_a': False, 'w_rook_h': False,
            'b_rook_a': False, 'b_rook_h': False
        }

    def print_board(self):
        print(f"\n--- {self.current_turn.capitalize()}'s Turn ---"); print("  a b c d e f g h"); print("  ---------------")
        for i, row in enumerate(self.board): print(f"{8 - i}| {' '.join(row)}")
    
    def coords_to_notation(self, pos):
        row, col = pos
        if not (0 <= row <= 7 and 0 <= col <= 7):
            return None
        col_char = self.index_to_col[col]
        row_char = str(8 - row)
        return col_char + row_char
        
    def _notation_to_coords(self, notation):
        if len(notation) != 2 or not notation[0].isalpha() or not notation[1].isdigit(): return None
        col_char = notation[0].lower(); row_char = notation[1]
        if col_char not in self.col_to_index or not (1 <= int(row_char) <= 8): return None
        col = self.col_to_index[col_char]; row = 8 - int(row_char)
        return (row, col)
        
    def get_piece(self, pos): row, col = pos; return self.board[row][col]
    
    def switch_turn(self): self.current_turn = 'black' if self.current_turn == 'white' else 'white'
        
    def is_square_attacked(self, position, attacker_color):
        for r in range(8):
            for c in range(8):
                piece = self.get_piece((r, c))
                if piece != '.':
                    is_white_piece = piece.isupper()
                    if (attacker_color == 'white' and is_white_piece) or \
                       (attacker_color == 'black' and not is_white_piece):
                        
                        # UPDATED! 核心修正！在「偵查」模式下，我們不再遞迴檢查「將軍」狀態
                        # 這樣就打破了 is_in_check <-> is_valid_move 的無限循環
                        if self.is_valid_move((r, c), position, check_for_check=False):
                            return True
        return False

    def is_in_check(self, king_color):
        king_char = 'K' if king_color == 'white' else 'k'
        attacker_color = 'black' if king_color == 'white' else 'white'
        king_pos = None
        for r in range(8):
            for c in range(8):
                if self.get_piece((r, c)) == king_char:
                    king_pos = (r, c)
                    break
            if king_pos: break
        if king_pos:
            return self.is_square_attacked(king_pos, attacker_color)
        return False

    def is_valid_move(self, start_pos, end_pos, check_for_check=True):
        piece = self.get_piece(start_pos)
        target_piece = self.get_piece(end_pos)
        if target_piece != '.' and piece.isupper() == target_piece.isupper():
            return False
        
        # 預言未來：模擬這一步棋，並檢查自己是否會被將軍
        if check_for_check:
            temp_board = copy.deepcopy(self)
            temp_board.board[end_pos[0]][end_pos[1]] = piece
            temp_board.board[start_pos[0]][start_pos[1]] = '.'
            if temp_board.is_in_check(self.current_turn):
                return False # 如果移動後自己會被將軍，這就是不合法棋步

        p_type = piece.lower()
        # 核心修正！在檢查王車易位時，把 check_for_check 參數也傳下去！
        if p_type == 'k' and self._is_valid_castling(start_pos, end_pos, check_for_check):
            return True

        # 其他棋子的檢查維持不變
        if p_type == 'p': return self._is_valid_pawn_move(start_pos, end_pos, piece)
        if p_type == 'r': return self._is_valid_rook_move(start_pos, end_pos)
        if p_type == 'n': return self._is_valid_knight_move(start_pos, end_pos)
        if p_type == 'b': return self._is_valid_bishop_move(start_pos, end_pos)
        if p_type == 'q': return self._is_valid_queen_move(start_pos, end_pos)
        if p_type == 'k': return self._is_valid_king_move(start_pos, end_pos)
        return False

    def _is_valid_castling(self, start_pos, end_pos, check_for_check=True):
        start_row, start_col = start_pos; end_row, end_col = end_pos
        if start_row != end_row or abs(start_col - end_col) != 2:
            return False
        
        # 核心修正！只有在「真實世界」的檢查中，才需要檢查是否被將軍
        if check_for_check and self.is_in_check(self.current_turn):
            return False

        # 後續的檢查邏輯不變
        if self.current_turn == 'white':
            if self.has_moved['w_king']: return False
            if end_col > start_col:
                if self.has_moved['w_rook_h']: return False
                if self.get_piece((7, 5)) != '.' or self.get_piece((7, 6)) != '.': return False
            else:
                if self.has_moved['w_rook_a']: return False
                if self.get_piece((7, 1)) != '.' or self.get_piece((7, 2)) != '.' or self.get_piece((7, 3)) != '.': return False
        else:
            if self.has_moved['b_king']: return False
            if end_col > start_col:
                if self.has_moved['b_rook_h']: return False
                if self.get_piece((0, 5)) != '.' or self.get_piece((0, 6)) != '.': return False
            else:
                if self.has_moved['b_rook_a']: return False
                if self.get_piece((0, 1)) != '.' or self.get_piece((0, 2)) != '.' or self.get_piece((0, 3)) != '.': return False
        return True

    def _is_valid_pawn_move(self, start_pos, end_pos, piece):
        start_row, start_col = start_pos
        end_row, end_col = end_pos
        
        # 決定前進方向 (白兵向上-1, 黑兵向下+1)
        direction = -1 if piece.isupper() else 1
        
        # --- 情況一：直走 (不能吃子) ---
        if start_col == end_col:
            # 檢查目標格子是否為空。如果不為空，就直接判定為非法移動 (修正Bug #2)
            if self.get_piece(end_pos) != '.':
                return False

            # 1. 普通走一步
            if end_row == start_row + direction:
                return True
            
            # 2. 從起點走兩步
            start_rank = 6 if piece.isupper() else 1
            if start_row == start_rank and end_row == start_row + 2 * direction:
                # 檢查中間的路徑是否也被擋住 (更嚴謹的檢查)
                if self.get_piece((start_row + direction, start_col)) == '.':
                    return True

        # --- 情況二：斜走 (一定要吃子) ---
        elif abs(start_col - end_col) == 1 and end_row == start_row + direction:
            target_piece = self.get_piece(end_pos)
            
            # 1. 一般吃子
            # 目標格子必須「有東西」而且「是敵人」(修正Bug #3)
            if target_piece != '.' and (target_piece.isupper() != piece.isupper()):
                return True

            # 2. 吃過路兵
            if end_pos == self.en_passant_target:
                return True
        
        # 如果以上所有合法情況都不滿足 (例如後退)，就判定為非法移動 (修正Bug #1)
        return False

    def _is_valid_rook_move(self, start_pos, end_pos):
        start_row, start_col = start_pos; end_row, end_col = end_pos
        if start_row != end_row and start_col != end_col: return False
        if start_row == end_row:
            step = 1 if end_col > start_col else -1
            for c in range(start_col + step, end_col, step):
                if self.get_piece((start_row, c)) != '.': return False
        else:
            step = 1 if end_row > start_row else -1
            for r in range(start_row + step, end_row, step):
                if self.get_piece((r, start_col)) != '.': return False
        return True

    def _is_valid_knight_move(self, start_pos, end_pos):
        start_row, start_col = start_pos; end_row, end_col = end_pos
        row_diff = abs(start_row - end_row); col_diff = abs(start_col - end_col)
        return (row_diff == 2 and col_diff == 1) or (row_diff == 1 and col_diff == 2)

    def _is_valid_bishop_move(self, start_pos, end_pos):
        start_row, start_col = start_pos; end_row, end_col = end_pos
        if abs(start_row - end_row) != abs(start_col - end_col): return False
        row_step = 1 if end_row > start_row else -1; col_step = 1 if end_col > start_col else -1
        r, c = start_row + row_step, start_col + col_step
        while r != end_row:
            if self.get_piece((r, c)) != '.': return False
            r += row_step; c += col_step
        return True

    def _is_valid_queen_move(self, start_pos, end_pos):
        return self._is_valid_rook_move(start_pos, end_pos) or self._is_valid_bishop_move(start_pos, end_pos)

    def _is_valid_king_move(self, start_pos, end_pos):
        start_row, start_col = start_pos; end_row, end_col = end_pos
        row_diff = abs(start_row - end_row); col_diff = abs(start_col - end_col)
        return row_diff <= 1 and col_diff <= 1
        
    def generate_legal_moves(self, color):
        legal_moves = []
        for r1 in range(8):
            for c1 in range(8):
                piece = self.get_piece((r1, c1))
                if piece != '.' and (piece.isupper() if color == 'white' else piece.islower()):
                    for r2 in range(8):
                        for c2 in range(8):
                            # UPDATED! 核心修正！在這裡也加上 check_for_check=False
                            # 這樣它在模擬時，就不會再掉進 is_in_check 的無窮迴圈了
                            if self.is_valid_move((r1, c1), (r2, c2), check_for_check=False):
                                # 雖然上面初步檢查通過了，但我們還是要在這裡做一次「真實的」合法性檢查
                                # 也就是模擬移動後，自己的國王不能被將軍
                                temp_board = copy.deepcopy(self)
                                temp_board.board[r2][c2] = piece
                                temp_board.board[r1][c1] = '.'
                                if not temp_board.is_in_check(color):
                                    legal_moves.append( ((r1, c1), (r2, c2)) )
        return legal_moves

    def move_piece(self, start_notation, end_notation):
        start_pos = self._notation_to_coords(start_notation)
        end_pos = self._notation_to_coords(end_notation)
        if start_pos is None or end_pos is None:
            print(f"\n唉呀！座標格式不對喔！")
            return

        piece = self.get_piece(start_pos)
        
        # 1. 檢查是否為空格
        if piece == '.':
            print(f"\n唉呀！{start_notation} 這個位置是空的！")
            return

        # 2. 檢查是否輪到該玩家
        is_white_piece = piece.isupper()
        if (self.current_turn == 'white' and not is_white_piece) or \
           (self.current_turn == 'black' and is_white_piece):
            print(f"\n不行喔！現在是 {self.current_turn} 方回合！")
            return
            
        # 3. 呼叫總規則檢查官，進行最終審判！
        if self.is_valid_move(start_pos, end_pos):
            # --- 合法移動！開始執行！ ---
            is_castling = piece.lower() == 'k' and abs(start_pos[1] - end_pos[1]) == 2
            en_passant_capture = (piece.lower() == 'p' and end_pos == self.en_passant_target)
            target_piece = self.get_piece(end_pos)
            action_text = ""

            if is_castling:
                self.board[end_pos[0]][end_pos[1]] = piece; self.board[start_pos[0]][start_pos[1]] = '.'
                if end_pos[1] > start_pos[1]:
                    rook = self.get_piece((start_pos[0], 7)); self.board[start_pos[0]][5] = rook; self.board[start_pos[0]][7] = '.'
                    action_text = "發動了「王翼易位」！"
                else:
                    rook = self.get_piece((start_pos[0], 0)); self.board[start_pos[0]][3] = rook; self.board[start_pos[0]][0] = '.'
                    action_text = "發動了「后翼易位」！"
            elif en_passant_capture:
                action_text = f"移動 {piece} 從 {start_notation} 到 {end_notation}"
                captured_pawn_pos = (start_pos[0], end_pos[1]); captured_pawn = self.get_piece(captured_pawn_pos)
                self.board[captured_pawn_pos[0]][captured_pawn_pos[1]] = '.'; action_text += f"，順路吃掉了 '{captured_pawn}'！"
                self.board[end_pos[0]][end_pos[1]] = piece; self.board[start_pos[0]][start_pos[1]] = '.'
            else:
                action_text = f"移動 {piece} 從 {start_notation} 到 {end_notation}"
                if target_piece != '.':
                    action_text += f"，吃掉了 '{target_piece}'！"
                self.board[end_pos[0]][end_pos[1]] = piece; self.board[start_pos[0]][start_pos[1]] = '.'

            print(f"\n{action_text}")

            # 更新履歷和記憶
            if piece == 'K': self.has_moved['w_king'] = True
            elif piece == 'k': self.has_moved['b_king'] = True
            elif piece == 'R' and start_pos == (7, 0): self.has_moved['w_rook_a'] = True
            elif piece == 'R' and start_pos == (7, 7): self.has_moved['w_rook_h'] = True
            elif piece == 'r' and start_pos == (0, 0): self.has_moved['b_rook_a'] = True
            elif piece == 'r' and start_pos == (0, 7): self.has_moved['b_rook_h'] = True
            self.en_passant_target = None
            if piece.lower() == 'p' and abs(start_pos[0] - end_pos[0]) == 2:
                self.en_passant_target = ((start_pos[0] + end_pos[0]) // 2, start_pos[1])
            
            self.switch_turn()
        else:
            # 不合法移動！駁回！
            print(f"\n不行喔！'{piece}' 不能這樣走！")
            return