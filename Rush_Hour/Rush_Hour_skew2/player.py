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

class Search_Node:
    """
    The Search_Node represents a node in the MaxN search tree. It is later
    converted into a node for the Monte Carlo Tree Search (MCTS)
    """
    def __init__(self, features, parent = None, move = None):
        """
        Each search_node stores the board features at a particular
        instance, with its immediate parent, children and other information
        necessary for both the MCTS and MaxN trees
        """
        self.features = features
        self.parent = parent
        self.children = []

        # move is the action that brought the parent to the current state
        self.move = move

        # goal represents the end pieces relative to the colour of the node
        self.goal = {
            RED: {(3, -3), (3, -2), (3, -1), (3, 0)},
            GREEN: {(-3, 3), (-2, 3), (-1, 3), (0, 3)},
            BLUE: {(0, -3), (-1, -2), (-2, -1), (-3, 0)}}

        # an MCTS feature that indicates that a node has been reached before
        self.isFullyExpanded = False

    # # #
    # MaxN Functions
    #

    def poss_moves(self):
        """
        poss_moves generates the available moves for a search_node given
        its features
        """
        poss_moves = []
        occupied = set().union(*self.features.state.values())

        # we cover all four action cases, and only move to another position
        # if it is within the bounds of the global board
        for piece in self.features.state[self.features.colour]:
            if piece in self.goal[self.features.colour]:
                poss_moves.append(("EXIT", piece))

            for x, y in [(-1, 0),(-1, 1), (0, -1), (0, 1), (1, 0), (1, -1)]:
                new = (piece[0] + x, piece[1] + y)
                new_jump = (new[0] + x, new[1] + y)

                # we move if there is neighbour without a piece and jump
                # otherwise if there is an empty space two positions away
                if new in BOARD:
                    if new not in occupied:
                        poss_moves.append(("MOVE", (piece, new)))
                    elif new_jump in BOARD and new_jump not in occupied:
                        poss_moves.append(("JUMP", (piece, new_jump)))

        # we pass if and only if there are no other available moves
        if not poss_moves:
            poss_moves.append(("PASS", None))

        return poss_moves

    def get_children(self):
        """
        get_children takes the possible moves relative to the search_nodes
        features and creates a new search_node as its child
        """
        for move in self.poss_moves():
            self.children.append(Search_Node(
                                    self.features.update(move), self, move))

    def manhat(self):
        """
        manhat takes a search_node and finds the average manhatten distance
        from the pieces to the goal of the player to move
        """
        dist = 0
        if self.features.score[self.features.colour][0] == 0:
            return dist

        # we consider the position of all pieces of the player
        for j in self.features.state[self.features.colour]:
            if self.features.colour == 0:
                dist += 3 - j[0]
            if self.features.colour == 1:
                dist += 3 - j[1]
            if self.features.colour == 2:
                dist += 3 - (- j[0] - j[1])

            # an extra condition that lowers dist if a piece is in the goal
            if j in self.goal[self.features.colour]:
                dist -= 1

        return dist/(self.features.score[self.features.colour][0])

    def manhat_diff(self, prior):
        """
        manhat_diff finds the change in distance to the goal between
        search_nodes after a series of actions
        """
        return (prior.manhat() - self.manhat())


    def attack(self, player):
        """
        attack takes a search_node and a player to attack and finds the average
        distance of the pieces for the two players
        """
        dist = 0
        if self.features.score[self.features.colour][0] == 0 or (
                                        self.features.score[player][0] == 0):
            return dist

        # consider the positions of all pieces of both players
        for opp_x, opp_y in self.features.state[player]:
            for my_x, my_y in self.features.state[self.features.colour]:
                dist += abs(my_x - opp_x) + abs(my_y - opp_y)

        return dist/((self.features.score[self.features.colour][0]) *
                                            (self.features.score[player][0]))

    def attack_diff(self, prior, player):
        """
        attack_diff finds the change in distance to the pieces of a player to
        attack between search_nodes after a series of actions
        """
        return (prior.attack(player) - self.attack(player))

    def eat_diff(self, prior):
        """
        eat_diff finds the change in total pieces of a player between
        search_nodes after a series of actions
        """

        exits =  self.features.score[self.features.colour][1] - (
                            prior.features.score[self.features.colour][1])

        return self.features.score[self.features.colour][0] + exits - (
                            prior.features.score[self.features.colour][0])

    def leave_diff(self, prior):
        """
        leave_diff finds the change in exits made by a player between
        search_nodes after a series of actions
        """
        return (self.features.score[self.features.colour][1]
                            - prior.features.score[self.features.colour][1])

    # # #
    # The following functions detail evaluation functions based on the
    # difference of certain features of the search_nodes. Each have a unique
    # weight based on the number of pieces a player has in possession
    #

    def total_attack(self, prior):
        """
        total_attack is called if the player has an insufficient
        amount of pieces to win the game
        """
        lst = []

        # find the piece that is most prime to win the game
        for colour in self.features.state:
            if colour != self.features.colour:
                lst.append((self.features.score[colour][0]
                                + 3 * self.features.score[colour][1], colour))
        colour = max(lst)[1]

        return self.attack_diff(prior, colour) + (3 * (self.eat_diff(prior))
                                            + -1 * (self.leave_diff(prior)))

    def total_four_five(self, prior):
        """
        total_four_five is called if the player has four or five toal pieces
        """
        return (self.manhat_diff(prior) + 4 * (self.eat_diff(prior))
                                                + 2 * (self.leave_diff(prior)))

    def total_six_seven(self, prior):
        """
        total_six_seven is called if the player has six or seven toal pieces
        """
        return (self.manhat_diff(prior) + (self.eat_diff(prior))
                                                + 4 * (self.leave_diff(prior)))

    def total_eight_nine(self, prior):
        """
        total_eight_nine is called if the player has eight or nine toal pieces
        """
        return (self.manhat_diff(prior) + 3 * (self.eat_diff(prior))
                                                + 6 * (self.leave_diff(prior)))

    def total_exit(self, prior):
        """
        total_exit is called if the player is in a prime position to win the
        game or has enough pieces such that its opponents cannot win
        """
        return (self.manhat_diff(prior) + (self.eat_diff(prior))
                                                + 6 * (self.leave_diff(prior)))

    def choose_function(self, prior, colour):
        """
        choose_function determines the evaluation function to apply
        given the features of the search_node
        """
        colour = prior.features.colour

        # total represents the number of pieces
        total = sum(prior.features.score[colour])

        # current player is in a good position to win the game
        if (prior.features.score[colour][1] == 3 and
            prior.features.score[colour][0] > 1) or total > 9:
            return self.total_exit(prior)

        if total <= 3:
            return self.total_attack(prior)

        elif 4 <= total <= 5:
            return self.total_four_five(prior)

        elif 6 <= total <= 7:
            return self.total_six_seven(prior)

        else:
            return self.total_eight_nine(prior)

    def choose_depth(self):
        """
        choose_depth determines the depth of the MaxN search tree
        depending on the number of pieces that have not exited
        """
        on_board = 0

        for colour in self.features.score:
            on_board += self.features.score[colour][0]

        if 8 <= on_board <= 12:
            return 3

        elif 5 <= on_board < 8:
            return 4

        elif on_board < 5:
            return 6

    def paranoid_addition(self, state, colour):
        """
        paranoid_addition adds a small factor to opponent moves,
        which adds weight when they can to jump the current players
        """
        if state.features.colour != colour:
            if (sum(self.features.score[colour]) <
                                        sum(state.features.score[colour])):
                return 3
        return 0


    # # #
    # MCTS Functions
    #

    def to_mcts(self):
        """
        to_mcts converts a search_node for MaxN to one for MCTS. Records of
        visitation and rewards are added along with an index for each child
        for later access
        """
        self.isFullyExpanded = True
        self.visits = np.zeros(len(self.children), dtype=np.float32)
        self.childVisits = np.zeros(len(self.children), dtype=np.float32)
        self.childRewards = np.zeros(len(self.children), dtype=np.float32)
        index = 0
        for child in self.children:
            child.index = index
            child.mcts_parent = self
            index += 1

    def is_terminal(self, root):
        for colour in self.features.score:
            if (self.features.score[colour][1] >
                                        root.features.score[colour][1]):
                return True
        if len(self.features.state[root.features.colour]) == 0:
            return True
        return False

    def getReward(self, root, delay):
        if self.features.score[root.features.colour][1] == 4:
                return 6/delay
        return -6/delay

    def simulation(self, root):
        delay = 1
        while self.end_simulation(root) is False:
            move =  random.choice(self.poss_moves())
            self = Search_Node(self.features.update(move), self, move)
            delay += 1
        return self, delay

    def end_simulation(self, root):
        if self.is_terminal(root):
            return True
        return False

    def changeReward(self, value):
        self.mcts_parent.childRewards[self.index] += value

    def addVisit(self):
        self.mcts_parent.childVisits[self.index] += 1

class MaxN:
    """
    A MaxN tree that can conduct a MaxN search to find a move for
    the current player to take
    """
    def __init__(self, features):
        """
        MaxN initialise a root node, which represents the current player
        to move in the game
        """
        self.root = Search_Node(features)

    def find(self):
        """
        find returns a move for the player to take based on the
        result of the MaxN search
        """
        state = self.root

        # we choose the depth of the tree based on the number of pieces
        # in play (branching factor)
        self.max_depth = state.choose_depth()
        future = self._MaxN(state, self.max_depth)

        return future.move

    def _MaxN(self, state, depth):
        """
        MaxN uses the MaxN algorithm to find the best move for a search_node
        to take based on the evaluation functions in Search_Node
        """
        if depth == 0:
            return state

        best_states = [state]
        best_value = float("-inf")
        state.get_children()

        # iterate through all possible children
        for child in state.children:

            # find the optimal configuration for the next child
            next_state = self._MaxN(child, depth-1)
            if next_state == None:
                continue

            # evaluate the board chosen by the child from the current player's
            # perspective
            next_state.features.colour = state.features.colour
            value = next_state.choose_function(state,
                                                self.root.features.colour)
            value += next_state.paranoid_addition(state,
                                                self.root.features.colour)

            # Record the state(s) with the best value
            if (value > best_value):
                best_states = [next_state]
                best_value = value
            elif value == best_value:
                best_states.append(next_state)

        # choose a piece with the highest value using MCTS if
        # there is a draw for the root node
        if len(best_states) == 1 or depth != self.max_depth:
            best_state = random.choice(best_states)
        else:
            mcts = MCTS(1000)
            # we only consider children that have the best MaxN value
            state.children = best_states
            best_state = mcts.search(state)

        if depth != self.max_depth:
            best_state.move = state.move

        return best_state

class MCTS:
    """
    A Monte Carlo Tree Seach, used to aid the decision making process of the
    MaxN tree algorithm. Models full games from selected search_node children
    using the Upper Confidence Bound applied to trees
    """
    def __init__(self, timeLimit = None, explorationConstant = math.sqrt(2)):
        """
        The MCTS is initialised with a time limit to play out through and an
        exploration constant determining which child is searched next
        """
        self.timeLimit = timeLimit
        self.explorationConstant = explorationConstant

    def search(self, state):
        state.to_mcts()
        state.mcts_parent = None
        self.root = state

        timeLimit = time.time() + self.timeLimit/1000
        while time.time() < timeLimit:
            self.dive()
        bestIndex = self.getBestChild(self.root, 0)
        return self.root.children[bestIndex]

    def dive(self):
        node = self.root
        while node.is_terminal(self.root) is False:
            if node.isFullyExpanded is True:
                node.visits += 1
                index = self.getBestChild(node, self.explorationConstant)
                node = node.children[index]
            else:
                self.expand(node)
                break

        node2 = node
        if node2.is_terminal(self.root) is True:
            reward = node2.getReward(self.root, delay = 1)
        else:
            feature, delay = node2.simulation(self.root)
            reward = node2.getReward(self.root, delay)
        self.propogate(node, reward)

    def propogate(self, node, reward):
        while node.mcts_parent is not None:
            node.addVisit()
            node.changeReward(reward)
            node = node.mcts_parent

    def expand(self, node):
        node.get_children()
        node.to_mcts()

    def getBestChild(self, node, explorationValue):
        values = node.childRewards / (1 + node.childVisits) + explorationValue * np.sqrt(np.log(node.visits)/(1 + node.childVisits))
        return np.argmax(values)
