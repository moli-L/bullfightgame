
from bullgame import BullGame, Player


game = BullGame(3)
p1 = Player("张三")
p2 = Player("李四")
p3 = Player("郭正山")

game.add_player(p1)
game.add_player(p2)
game.add_player(p3)

for i in range(3):
    p1.bet_chips(10*i+10)
    p2.bet_chips(10*i+10)
    p3.bet_chips(10*i+10)
    report = game.loop_round()
    print(report+"\n\n=======================\n\n")
