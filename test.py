
from game import BullGame, Player


game = BullGame(num_player=3)
p1 = Player(1, "张三")
p2 = Player(2, "李四")
p3 = Player(3, "郭老六")

game.add_player(p1)
game.add_player(p2)
game.add_player(p3)

while not game.is_game_end():
    p1.bet_chips(10)
    p2.bet_chips(20)
    p3.bet_chips(66)
    report = game.loop_round()
    print(report+"\n\n===================\n\n")
