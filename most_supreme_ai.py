# SPDX-License-Identifier: BSD-3-Clause

import numpy as np

# This is your team name
CREATOR = "HAL9999"


class PlayerAi:
    """
    This is the AI bot that will be instantiated for the competition.
    """

    def __init__(self):
        self.team = CREATOR  # Mandatory attribute
        self.ntanks = {}
        self.nships = {}
        self.njets = {}
        self.base_numbers = {}
        self.targets = {}
        # self.target = {"tank0" : (x, y)}


    def get_targets(self, info):
        self.targets = {}
        if len(info) > 1:
            for name in info:
                if name != self.team:
                    for target_name, target_list in info[name].items():
                        for target in target_list:
                            self.targets[f"{target_name}{target.uid}"] = (target.x, target.y)

    def find_target(self, my_self):
        targets_dict = {"jet": (np.inf, (my_self.owner.x,my_self.owner.y)),
                        "base": (np.inf, (my_self.owner.x,my_self.owner.y)),
                        "ship": (np.inf, (my_self.owner.x,my_self.owner.y)),
                        "tank": (np.inf, (my_self.owner.x,my_self.owner.y))}

        for target, location in self.targets.items():
            t_x, t_y = location
            dist = my_self.get_distance(t_x, t_y)
            if "jet" in target and dist < targets_dict["jet"][0]:
                targets_dict["jet"] = (dist, location)
            if "base" in target and dist < targets_dict["base"][0]:
                targets_dict["base"] = (dist, location)
            if "ship" in target and dist < targets_dict["ship"][0]:
                targets_dict["ship"] = (dist, location)
            if "tank" in target and dist < targets_dict["tank"][0]:
                targets_dict["tank"] = (dist, location)

        return targets_dict

    def run(self, t: float, dt: float, info: dict, game_map: np.ndarray):
        """
        This is the main function that will be called by the game engine.

        Parameters
        ----------
        t : float
            The current time in seconds.
        dt : float
            The time step in seconds.
        info : dict
            A dictionary containing all the information about the game.
            The structure is as follows:
            {
                "team_name_1": {
                    "bases": [base_1, base_2, ...],
                    "tanks": [tank_1, tank_2, ...],
                    "ships": [ship_1, ship_2, ...],
                    "jets": [jet_1, jet_2, ...],
                },
                "team_name_2": {
                    ...
                },
                ...
            }
        game_map : np.ndarray
            A 2D numpy array containing the game map.
            1 means land, 0 means water, -1 means no info.
        """

        # Get information about my team
        myinfo = info[self.team]
        self.get_targets(info)

        # Controlling my bases =================================================

        # Description of information available on bases:
        #
        # This is read-only information that all the bases (enemy and your own) have.
        # We define base = info[team_name_1]["bases"][0]. Then:
        #
        # base.x (float): the x position of the base
        # base.y (float): the y position of the base
        # base.position (np.ndarray): the (x, y) position as a numpy array
        # base.team (str): the name of the team the base belongs to, e.g. ‘John’
        # base.number (int): the player number
        # base.mines (int): the number of mines inside the base
        # base.crystal (int): the amount of crystal the base has in stock
        #     (crystal is per base, not shared globally)
        # base.uid (str): unique id for the base
        #
        # Description of base methods:
        #
        # If the base is your own, the object will also have the following methods:
        #
        # base.cost("mine"): get the cost of an object.
        #     Possible types are: "mine", "tank", "ship", "jet"
        # base.build_mine(): build a mine
        # base.build_tank(): build a tank
        # base.build_ship(): build a ship
        # base.build_jet(): build a jet

        # Iterate through all my bases (vehicles belong to bases)
        for base in myinfo["bases"]:
            # Bookkeeping
            uid = base.uid
            if uid not in self.base_numbers:
                pass
                #self.base_numbers[uid]
            if uid not in self.ntanks:
                self.ntanks[uid] = 0
                self.nships[uid] = 0
                self.njets[uid] = 0

            # Firstly, each base should build a mine if it has less than 3 mines
            if base.mines < 3:
                if base.crystal > base.cost("mine"):
                    base.build_mine()
            # If we have enough mines, pick something at random
            else:
                if self.ntanks[uid] < 5:
                    if base.crystal > base.cost("tank"):
                        tank = base.build_tank(heading=360 * np.random.random())
                        self.ntanks[uid] += 1
                elif self.nships[uid] < 3:
                    if base.crystal > base.cost("ship"):
                        ship = base.build_ship(heading=360 * np.random.random())
                        self.nships[uid] += 1
                elif base.crystal > base.cost("jet"):
                    if self.njets[uid] > 0 and self.njets[uid] % 5 == 0:
                        base.build_ship(heading=360 * np.random.random())
                    else:
                        jet = base.build_jet(heading=360 * np.random.random())
                        self.njets[uid] += 1

        # Try to find an enemy target
        target = None
        # If there are multiple teams in the info, find the first team that is not mine
        """
        if len(info) > 1:
            for name in info:
                if name != self.team:
                    # Target only bases
                    if "bases" in info[name]:
                        # Simply target the first base
                        t = info[name]["bases"][0]
                        target = [t.x, t.y]
                        break"""

        # Controlling my vehicles ==============================================

        # Description of information available on vehicles
        # (same info for tanks, ships, and jets):
        #
        # This is read-only information that all the vehicles (enemy and your own) have.
        # We define tank = info[team_name_1]["tanks"][0]. Then:
        #
        # tank.x (float): the x position of the tank
        # tank.y (float): the y position of the tank
        # tank.team (str): the name of the team the tank belongs to, e.g. ‘John’
        # tank.number (int): the player number
        # tank.speed (int): vehicle speed
        # tank.health (int): current health
        # tank.attack (int): vehicle attack force (how much damage it deals to enemy
        #     vehicles and bases)
        # tank.stopped (bool): True if the vehicle has been told to stop
        # tank.heading (float): the heading angle (in degrees) of the direction in
        #     which the vehicle will advance (0 = east, 90 = north, 180 = west,
        #     270 = south)
        # tank.vector (np.ndarray): the heading of the vehicle as a vector
        #     (basically equal to (cos(heading), sin(heading))
        # tank.position (np.ndarray): the (x, y) position as a numpy array
        # tank.uid (str): unique id for the tank
        # tank.stuck(bool): True if the vehicle is stuck
        #
        # Description of vehicle methods:
        #
        # If the vehicle is your own, the object will also have the following methods:
        #
        # tank.get_position(): returns current np.array([x, y])
        # tank.get_heading(): returns current heading in degrees
        # tank.set_heading(angle): set the heading angle (in degrees)
        # tank.get_vector(): returns np.array([cos(heading), sin(heading)])
        # tank.set_vector(np.array([vx, vy])): set the heading vector
        # tank.goto(x, y): go towards the (x, y) position
        # tank.stop(): halts the vehicle
        # tank.start(): starts the vehicle if it has stopped
        # tank.get_distance(x, y): get the distance between the current vehicle
        #     position and the given point (x, y) on the map
        # ship.convert_to_base(): convert the ship to a new base (only for ships).
        #     This only succeeds if there is land close to the ship.
        #
        # Note that by default, the goto() and get_distance() methods will use the
        # shortest path on the map (i.e. they may go through the map boundaries).

        # Iterate through all my tanks


        if "tanks" in myinfo:
            for tank in myinfo["tanks"]:
                tank.stop()
                targets = self.find_target(tank)

                if targets["jet"][0] < 25:
                    tank.goto(targets["jet"][1][0], targets["jet"][1][1])
                elif targets["tank"][0] < 25:
                    tank.goto(targets["tank"][1][0], targets["tank"][1][1])
                else:
                    tank.goto(tank.owner.x, tank.owner.y)
                """
                if not tank.stopped:
                    # If the tank position is the same as the previous position,
                    # set a random heading
                    if tank.stuck:
                        tank.set_heading(np.random.random() * 360.0)
                    # Else, if there is a target, go to the target
                    elif target is not None:
                        tank.goto(*target)"""

        # Iterate through all my ships
        if "ships" in myinfo:
            for ship in myinfo["ships"]:
                if not ship.stopped:
                    # If the ship position is the same as the previous position,
                    # convert the ship to a base if it is far from the owning base,
                    # set a random heading otherwise
                    if ship.stuck:
                        if ship.get_distance(ship.owner.x, ship.owner.y) > 60:
                            ship.convert_to_base()
                        else:
                            ship.set_heading(np.random.random() * 360.0)

        # Iterate through all my jets
        if "jets" in myinfo:
            for jet in myinfo["jets"]:
                # Jets simply go to the target if there is one, they never get stuck
                targets = self.find_target(jet)

                if targets["base"][0] < 600:
                    jet.goto(targets["base"][1][0], targets["base"][1][1])

