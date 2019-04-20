import sys
import copy
import random

BOARD = set()
for i in range(-3,1):
    for j in range(-3-i, 4):
        BOARD.add((i,j))
for i in range(1,4):
    for j in range(-3,4-i):
        BOARD.add((i,j))

MIN_DEPTH = 2

class Player:
    def __init__(self, colour):
        """
        This method is called once at the beginning of the game to initialise
        your player. You should use this opportunity to set up your own internal
        representation of the game state, and any other information about the
        game state you would like to maintain for the duration of the game.

        The parameter colour will be a string representing the player your
        program will play as (Red, Green or Blue). The value will be one of the
        strings "red", "green", or "blue" correspondingly.
        """
        # TODO: Set up state representation.
        self.features = Features(colour)

    def action(self):
        """
        This method is called at the beginning of each of your turns to request
        a choice of action from your program.

        Based on the current state of the game, your player should select and
        return an allowed action to play on this turn. If there are no allowed
        actions, your player must return a pass instead. The action (or pass)
        must be represented based on the above instructions for representing
        actions.
        """
        # TODO: Decide what action to take
        return curr_state.MaxN(self.features.colour, 0)[0]


    def update(self, colour, action):
        """
        This method is called at the end of every turn (including your player’s
        turns) to inform your player about the most recent action. You should
        use this opportunity to maintain your internal representation of the
        game state and any other information about the game you are storing.

        The parameter colour will be a string representing the player whose turn
        it is (Red, Green or Blue). The value will be one of the strings "red",
        "green", or "blue" correspondingly.

        The parameter action is a representation of the most recent action (or
        pass) conforming to the above in- structions for representing actions.

        You may assume that action will always correspond to an allowed action
        (or pass) for the player colour (your method does not need to validate
        the action/pass against the game rules).
        """
        self.features = self.features.update(self.features.colour_dic[colour], action)
        # TODO: Update state representation in response to action.

class Features:
    def __init__(self, colour):
        self.colour_dic = {'red': 0,
            'green': 1, 'blue': 2}
        self.turn = 0
        self.colour = self.colour_dic[colour]
        self.period = 0
        self.score = {0: [4, 0], 1: [4, 0], 2: [4, 0]}
        self.goal = {0: {(3,-3), (3,-2), (3,-1), (3,0)},
            2: {(0,-3), (-1,-2), (-2,-1), (-3,0)},
            1: {(-3,3), (-2,3), (-1,3), (0,3)}}[self.colour_dic[colour]]
        self.state = []
        self.poss_moves = []
        self.initial_state()

    def update(self, colour, action):
        new = copy.deepcopy(self)
        change = action[1]
        if action[0] == "MOVE":
            new.state[colour].remove(change[0])
            new.state[colour].add(change[1])
        elif action[0] == "JUMP":
            new.state[colour].remove(change[0])
            new.state[colour].add(change[1])
            middle_piece = ((change[0][0] + change[1][0])/2,
                (change[0][1] + change[1][1])/2)
            new.state[colour].add(middle_piece)
            new.score[colour][0] += 1
            for i in [1,2]:
                if middle_piece in new.state[curr_colour + i]:
                    new.state[colour + i].remove(middle_piece)
                    new.score[colour + i][0] -= 1
        elif action[0] == 'EXIT':
            new.state[colour].remove(change)
            new.score[colour][0] -= 1
            new.score[colour][1] += 1
        new.turn = (new.turn + 1) % 3
        new.update_poss_moves()
        return new

    def initial_state(self):
        self.state = {
            0: {(-3, 0), (-3, 1), (-3, 2), (-3, 3)},
            1: {(0, -3), (1, -3), (2, -3), (3, -3)},
            2: {(3, 0), (2, 1), (1, 2), (0, 3)}}
        self.update_poss_moves()

    def update_poss_moves(self):
        self.poss_moves = []
        occupied = set().union(*self.state.values())
        for piece in self.state[self.turn]:
            if piece in self.goal:
                self.poss_moves.append(("EXIT", piece))
                continue
            for i,j in [(-1,0),(-1,1), (0,-1), (0,1), (1,0), (1,-1)]:
                new = (piece[0]+i,piece[1]+j)
                new_jump = (new[0] + i, new[1] + j)
                if new in BOARD:
                    if new not in occupied:
                        self.poss_moves.append(("MOVE", (piece, new)))
                    elif new_jump in BOARD and new_jump not in occupied:
                        self.poss_moves.append(("JUMP", (piece, new_jump)))
            if not self.poss_moves:
                self.poss_moves.append(("PASS", None))


class Search_Node:
    def __init__(self, features):
        self.features = features

    def get_children(self):
        children = []
        for move in self.features.poss_moves:
            children.append((move, Search_Node(self.features.update(self.features.turn, move))))
        return children

    def MaxN(self, turn, depth):
        board_list = []
        ev = Evaluation_Function(turn)
        if depth < MIN_DEPTH:
            for move, future in [(move, child.MaxN((turn + 1) % 3, depth + 1)[-1]) for move, child in self.get_children()]:
                board_list.append((ev.random(future), (move, future)))
            return max(board_list)[-1]
        for move, child in self.get_children():
            board_list.append((ev.random(child), (move, child)))
        return max(board_list)[-1]

class MaxN_Tree:
    def __init__(self, player):
        self.root = Search_Node(player.features)

class Evaluation_Function:
    def __init__(self, turn):
        self.turn = turn

    def random(self, state):
        if state.features.score[state.features.turn][1] == 4:
            return 120
        elif (state.features.score[(state.features.turn + 1) % 3][1] == 4) or (state.features.score[(state.features.turn + 2) % 3][1] == 4):
            return 0
        return random.randint(1, 100)
