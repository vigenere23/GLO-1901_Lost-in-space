"""Définition de la classe MyWindow."""

import pyglet as pg
from pyglet.window import key

import common.file_helper as fh
from .ship import Ship
from .player_ship import PlayerShip
from .map_gen import Map
from .win_handler import WinHandler
from .keys_handler import KeysHandler
from .glo1901 import Chrono


class Game(pg.window.Window):
    """Encapsulation des fonctionnalités de base de la fenêtre (et du jeu).

    Paramètres
    ----------
    client : ClientReseau()
        Instantiation d'un client connecté au serveur python.gel.ulaval.ca.

    n : int
        Nombre de joueurs.

    start_pos, end_pos : tuple ou liste
        Position de départ et d'arrivée du vaisseau2.

    obstacles : liste de listes de listes ou tuples
        Liste des sommets des obstacles.

    *ship_params : tuple (accel, energy, ang_velocity, bounciness)
        Contient les paramètres du vaisseau à instancier.
    """

    def __init__(
            self,
            client, username, host, players,
            animate=False,
            fps=False,
            offline=False,
            start_pos=[0, 0],
            end_pos=[100, 100],
            obstacles=[],
            **ship_params):

        super().__init__(
            width=700,
            height=700,
            caption="Lost in space - {}".format(username),
            vsync=False)

        self.__client = client
        self.__username = username
        self.__host = host
        self.__animate = animate
        self.__fps = fps
        self.__offline = offline

        self.__server_timer = Chrono(autostart=True)
        self.__map = Map(obstacles, end_pos)
        self.__keys = KeysHandler()
        self.__win_handler = WinHandler(700, 700, self.__keys)

        self.__player_ship, self.__other_ships = self.init_ships(
            username, players, start_pos, ship_params)
        self.__background = self.init_background()

        self.push_handlers(self.__keys)

    def init_ships(self, pseudo, players, start_pos, ship_params):
        """Assigne les vaisseaux.

        Paramètres
        ----------
        players : list
            Pseudonymes des joueurs.

        start_pos : list (coordonnées 2D).
            Position initiale des vaisseaux.

        ship_params : list
            Liste des paramètres du vaisseau joueur.

        Retourne
        --------
        tuple of pyglet.sprite.Sprite()
            Tuple des vaisseaux (vaisseau_joueur, vaisseaux_ennemis).
        """
        player_ship = None
        other_ships = {}

        for i, player in enumerate(players):
            image_path = fh.get_path("client/images/ship{}.png".format(i + 1))
            if player != self.__username:
                other_ships[player] = Ship(
                    player, image_path, *start_pos)
            else:
                player_ship = PlayerShip(
                    pseudo, image_path, *start_pos, **ship_params)

        return player_ship, other_ships

    def init_background(self):
        """Assigne le fond d'écran.

        Retourne
        --------
        pyglet.sprite.Sprite()
            Sprite du fonc d'écran.
        """
        bg_path = fh.get_path("client/images/space.jpg")
        bg_image = pg.image.load(bg_path)
        bg_image.anchor_x = bg_image.width // 2
        bg_image.anchor_y = bg_image.height // 2
        return pg.sprite.Sprite(
            bg_image, self.width // 2, self.height // 2)

    def start(self):
        """Débute les appels répétitifs."""
        pg.clock.schedule_interval(self.update, 1/self.__fps)
        pg.clock.set_fps_limit(self.__fps)

    def stop(self):
        """Arrête les appels répétitifs."""
        pg.clock.unschedule(self.update)

    def exit(self):
        """Quitte le jeu."""
        self.stop()
        pg.app.exit()
        self.close()

    def check_keys(self, detla_time):
        """Vérifie l'appui de touches et appelle les fonctions associées."""

        if self.__keys[key.RIGHT] and not self.__keys[key.LEFT]:
            self.__player_ship.update_rotation(detla_time, clockwise=True)
        elif self.__keys[key.LEFT] and not self.__keys[key.RIGHT]:
            self.__player_ship.update_rotation(detla_time, clockwise=False)

        if self.__keys[key.UP]:
            self.__player_ship.update_velocity(detla_time)

    def on_draw(self):
        """Regroupe les fonctions de dessin.

        Appelé à chaque itération
        """
        self.clear()
        self.__background.draw()
        self.__map.draw()
        self.__player_ship.draw()
        for ship in self.__other_ships.values():
            ship.draw()

        if self.__win_handler.has_winner():
            self.__win_handler.draw()

    def update(self, delta_time):
        """Regroupe les fonctions de mise-à-jour.

        Appelée à toutes les detla_time secondes.
        """

        if not self.__win_handler.has_winner():
            self.check_keys(delta_time)
            self.__map.check_collision(delta_time, self.__player_ship)
            self.__player_ship.update(delta_time)

            if self.__animate:
                for ship in self.__other_ships.values():
                    ship.update(delta_time)
            
            report = None

            if not self.__offline:
                report = self.update_server()
                if report:
                    self.update_positions(report["statuses"])
            
            self.update_winner(report)
    
        else:
            if self.__keys[key.ENTER]:
                self.exit()

    def update_server(self):
        """Envoi les rapports au serveur et traite les données reçues."""
        time = self.__server_timer.get()
        report = None

        if time > 0.025:
            try:
                self.__server_timer.reset()
                report = self.__client.report(self.__player_ship.get_status())

            except BaseException as e:
                print("""\nLe débit des requêtes est trop élevé...
                      \nDernière requête il y a {} secondes.""".format(time))
                print(e)
                self.exit()
                return None

            if report.get("error"):
                raise BaseException("Une erreur est survenue...\n{}".format(report["error"]))
            elif report.get("data"):
                report = report["data"]
            else:
                raise BaseException("Une erreur inconnue est survenue...")

        return report

    def update_winner(self, report):
        if report and report.get("winner"):
            self.__win_handler.set_winner(report["winner"])
        elif self.__map.is_winner(self.__player_ship.get_position()):
            self.__win_handler.set_winner(self.__player_ship.username)

    def update_positions(self, report):
        for player, ship in self.__other_ships.items():
            if report.get(player):
                ship.set_status(*report[player])
            else:
                ship.disappear()
