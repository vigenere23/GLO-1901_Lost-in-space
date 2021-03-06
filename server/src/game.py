from common.vec2 import Vec2

class Game:
  def __init__(self, host, nb_players, mission):
    self.host = host
    self.nb_players = nb_players
    self.mission = mission
    self.players = [] # Player
    self.end_point = Vec2.from_list(mission["end_pos"])
    self.winner = None

  def get_players(self):
    return [player.username for player in self.players]

  def is_full(self):
    return len(self.players) == self.nb_players

  def remaining_places(self):
    return self.nb_players - len(self.players)

  def get_statuses(self):
    statuses = {}
    for player in self.players:
      statuses[player.username] = player.status

    return statuses

  def update_winner(self):
    if not self.winner:
      for player in self.players:
        if len(player.status) == 3:
          vec_pos = Vec2.from_list(player.status[0])
          if Vec2.dist(vec_pos, self.end_point) <= 10:
            self.winner = player.username
            return
