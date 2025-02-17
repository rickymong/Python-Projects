board = {1 : " ",2 : " ",3 : " ",
         4 : " ",5 : " ",6 : " ",
         7 : " ",8 : " ",9 : " "}

def printboard(board):
    print(board[1] , "|" , board[2] , "|" , board[3])
    print("---------")
    print(board[4] , "|" , board[5] , "|" , board[6])
    print("---------")
    print(board[7] , "|" , board[8] , "|" , board[9])
    print()

def is_space_free(position):
    if board[position] == " ":
        return True
    else:
        return False

def check_draw():
    for key in board.keys():
        if board[key] == " ":
            return False
    return True

def check_winner(mark):
    if board[1] == board[2] and board[1] == board[3] and board[1] == mark:
        return True
    if board[4] == board[5] and board [4] == board[6] and board [4] == mark:
        return True
    if board[7] == board [8] and board[7] == board[9] and board[7] == mark:
        return True
    if board[1] == board [5] and board[1] == board[9] and board[1] == mark:
        return True
    if board[3] == board [5] and board[3] == board[7] and board[3] == mark:
        return True
    if board[1] == board [4] and board[1] == board[7] and board[1] == mark:
        return True
    if board[2] == board [5] and board[2] == board[8] and board[2] == mark:
        return True
    if board[3] == board [6] and board[3] == board[9] and board[3] == mark:
        return True
    else:
        return False

def insert_letter(letter,position):
    if is_space_free(position):
        board[position] = letter
        printboard(board)
        if check_draw():
            print("The game is draw")
            exit()
        if check_winner(letter):
            print(letter," Wins the game")
            print("Thank you for playing")
            exit()
        return
    else:
        print("The position/square is not free")
        print("Please try again")
        position = int(input("Enter the position again : "))
        insert_letter(letter , position)
        return

def player_move(player):
    position = int(input("Enter the position : "))
    insert_letter(player , position)
    return

print()
printboard(board)

first = "X"
second = "O"

while (not check_winner(first)) and (not check_winner(second)):
    player_move(first)
    player_move(second)

def print_scoreboard(score_board):
    print("--------------------------------")
    print("            SCOREBOARD       ")
    print("--------------------------------")