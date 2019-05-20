"""
Rush_Hour
Solution to Project Part B: Playing the Game

This solution uses a general maxn structure to evaluate the best move
for a player to take in the game Chexers. It also employs a Monte Carlo Tree
Search to determine the best move when the MaxN search is indeterminate.

Authors: Neil Umoh and Toai Trinh
"""

import sys
import copy
import random
import numpy as np
import math
import time
from .maxn import MaxN

 # # #
 # Here we define a board to contain all possible destinations
 # This ensures that the pieces never move to a piece outside the bounds

BOARD = set()
for i in range(-3, 1):
    for j in range(-3-i, 4):
        BOARD.add((i, j))

for i in range(1, 4):
    for j in range(-3, 4-i):
        BOARD.add((i, j))

# As every game is conducted in the same order, i.e. with red starting, we
# each piece has an associated number determined by their order in the game

RED = 0
GREEN = 1
BLUE = 2

class Player:
    """
    The Player class holds the current information for each player, including
    the board configuration. It also determines a move given the
    current state and updates the board state accordingly.
    """
    def __init__(self, colour):
        """
        Player is initialised to be the red player, regardless of their
        actual colour in the game
        """
        self.features = Features(RED)

    def action(self):
        """
        action takes the current state and conducts the MaxN search to
        determine a move for the player to take
        """
        # passes immediately if there is no move to take
        if self.features.score[self.features.colour][0] == 0:
            return ("PASS", None)

        maxn = MaxN(self.features)

        return maxn.find()

    def update(self, colour, action):
        """
        update takes an action and evaluates the resulting state for each
        player after the move is made
        """
        self.features = self.features.update(action)


class Features:
    """
    Features represents a configuration of the board including the
    player to move, the current score, pieces and board state
    """
    def __init__(self, colour):
        """
        Each feature is initialised as defined in the specification of the game
        """
        # colour is the player to move next
        self.colour = colour

        # the score for each player is the number of pieces of that colour
        # on the board and the number of exits they have made
        self.score = {RED: [4, 0], GREEN: [4, 0], BLUE: [4, 0]}

        # the state stores the location of pieces of each piece on the board
        # and its colour
        self.state = {
            RED: {(-3, 0), (-3, 1), (-3, 2), (-3, 3)},
            GREEN: {(0, -3), (1, -3), (2, -3), (3, -3)},
            BLUE: {(3, 0), (2, 1), (1, 2), (0, 3)}}

    def update(self, action):
        """
        update returns a new set of features to represent the board
        after a specific action is made
        """
        new = copy.deepcopy(self)
        colour = self.colour

        # the colour is incremented as the player to move has changed
        new.colour = (colour + 1) % 3
        change = action[1]

        # a move action takes the prior piece location from the board state
        # and replaces it with its new location
        if action[0] == "MOVE":
            new.state[colour].remove(change[0])
            new.state[colour].add(change[1])

        # a jump action takes the prior piece location from the board state
        # and replaces it with its new location, chaning the colour
        # of a piece if jumped by an opponent, in the process
        elif action[0] == "JUMP":
            new.state[colour].remove(change[0])
            new.state[colour].add(change[1])

            # find the piece that was jumped over
            middle_piece = ((change[0][0] + change[1][0])/2,
                (change[0][1] + change[1][1])/2)
            new.state[colour].add(middle_piece)

            # change the colour of the jumped piece, if different to the jumper
            for succ in [1,2]:
                if middle_piece in new.state[(colour + succ) % 3]:
                    new.state[(colour + succ) % 3].remove(middle_piece)
                    new.score[(colour + succ) % 3][0] -= 1
                    new.score[colour][0] += 1

        # an exit action removes the piece from the board state and
        # increments the number of exits achieved in the scoresd
        elif action[0] == 'EXIT':
            new.state[colour].remove(change)
            new.score[colour][0] -= 1
            new.score[colour][1] += 1

        return new


