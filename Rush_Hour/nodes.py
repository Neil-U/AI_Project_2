import numpy as np
import random

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

        # the data for its children are stored in the parent using numpy arrays
        # to efficiently hold information as well as reduce memory usage
        self.childVisits = np.zeros(len(self.children), dtype=np.float32)
        self.childRewards = np.zeros(len(self.children), dtype=np.float32)
        index = 0
        for child in self.children:
            child.index = index
            child.mcts_parent = self
            index += 1

    def is_terminal(self, root):
        """
        is_terminal returns a boolean of whether or not the current state
        is a terminal state. In our case, does not go to an actual terminal
        state but one where someone exits to maximise no. of simulations.
        """
        for colour in self.features.score:
            if (self.features.score[colour][1] >
                                        root.features.score[colour][1]):
                return True
        if len(self.features.state[root.features.colour]) == 0:
            return True
        return False

    def getReward(self, root, delay):
        """
        returns the reward of a state
        """
        if self.features.score[root.features.colour][1] == 4:
                return 6/delay
        return -6/delay

    def simulation(self, root):
        """
        simulation simulates play until a terminal state is reached
        """

        # we introduce a delay factor to prioritise moves that reach
        # terminal state quicker
        delay = 1
        while self.is_terminal(root) is False:
            move =  random.choice(self.poss_moves())
            self = Search_Node(self.features.update(move), self, move)
            delay += 1
        return self, delay


    def changeReward(self, value):
        """
        changeReward is a setter for the reward of a given node
        """
        self.mcts_parent.childRewards[self.index] += value

    def addVisit(self):
        """
        addVisit is an incrementer for the visits of a node
        """
        self.mcts_parent.childVisits[self.index] += 1
