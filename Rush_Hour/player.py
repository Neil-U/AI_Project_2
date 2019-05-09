rimport sys
import copy
import random
from Rush_Hour.mctslib import mcts

BOARD = set()
for i in range(-3,1):
    for j in range(-3-i, 4):
        BOARD.add((i,j))

for i in range(1,4):
    for j in range(-3,4-i):
        BOARD.add((i,j))

RED = 0
GREEN = 1
BLUE = 2

mcts = mcts(timeLimit = 1000)

class Player:
    def __init__(self, colour):
        self.features = Features(RED)

    def action2(self):
        if not self.features.state[self.features.colour]:
            return ("PASS", None)
        functions = Evaluation_Function()
        maxn = Minimax(self.features, functions)
        return maxn.find()

    def action(self):
        return mcts.search(initialState = Search_Node(self.features))

    def update(self, colour, action):
        self.features = self.features.update(action)


class Features:
    def __init__(self, colour):
        self.colour = colour
        self.period = 0
        self.score = {RED: [4, 0], GREEN: [4, 0], BLUE: [4, 0]}
        self.state = {
            RED: {(-3, 0), (-3, 1), (-3, 2), (-3, 3)},
            GREEN: {(0, -3), (1, -3), (2, -3), (3, -3)},
            BLUE: {(3, 0), (2, 1), (1, 2), (0, 3)}}

    def update(self, action):
        new = copy.deepcopy(self)
        colour = self.colour
        new.colour = (colour + 1) % 3
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
            for i in [1,2]:
                if middle_piece in new.state[(colour + i) % 3]:
                    new.state[(colour + i) % 3].remove(middle_piece)
                    new.score[(colour + i) % 3][0] -= 1
                    new.score[colour][0] += 1

        elif action[0] == 'EXIT':
            new.state[colour].remove(change)
            new.score[colour][0] -= 1
            new.score[colour][1] += 1

        return new

class Search_Node:

    def __init__(self, features, parent = None, move = None):
        self.features = features
        self.parent = parent
        self.children = []
        self.move = move
        self.turn = features.colour
        self.goal = {}
        self.update_goal()


    def getPossibleActions(self):
        return self.poss_moves()
    def takeAction(self, action):
        newState = self.features.update(action)
        return Search_Node(newState)
    # very dodgy isTerminal function. need to find actual rules that confirm that it is terminal
    def isTerminal(self):
        if len(self.getPossibleActions()) == 0:
            return True
        for c in self.features.score.keys():
            if self.features.score[c][1] == 4:
                return True
        return False
    def getReward(self):
        for colour in self.features.score:
            if self.features.score[colour][1] == 4:
                if colour == self.features.colour:
                    return 1
                else:
                    return -1
        return 0


    def poss_moves(self):
        poss_moves = []
        occupied = set().union(*self.features.state.values())

        for piece in self.features.state[self.features.colour]:
            if piece in self.goal:
                poss_moves.append(("EXIT", piece))
                continue

            for i,j in [(-1,0),(-1,1), (0,-1), (0,1), (1,0), (1,-1)]:
                new = (piece[0]+i,piece[1]+j)
                new_jump = (new[0] + i, new[1] + j)

                if new in BOARD:
                    if new not in occupied:
                        poss_moves.append(("MOVE", (piece, new)))
                    elif new_jump in BOARD and new_jump not in occupied:
                        poss_moves.append(("JUMP", (piece, new_jump)))

            if not poss_moves:
                poss_moves.append(("PASS", None))

        return poss_moves

    def get_children(self):
        for move in self.poss_moves():
            self.children.append(Search_Node(self.features.update(move), self, move))

    def update_goal(self):
        self.goal = {
            RED: {(3,-3), (3,-2), (3,-1), (3,0)},
            GREEN: {(-3,3), (-2,3), (-1,3), (0,3)},
            BLUE: {(0,-3), (-1,-2), (-2,-1), (-3,0)}}[self.turn]

class Evaluation_Function:
    def __init__(self):
        return

    def is_terminal(self, state):
        for piece in state.features.state[state.turn]:
            if piece in state.goal:
                return piece
        return False

    def random(self, state):

        return random.randint(1, 100)

    def euclid(self, state):
        dist = 0
        for j in state.features.state[state.turn]:
            if state.turn == 0:
                dist -= 3 - j[0]
            if state.turn == 1:
                dist -= 3 - j[1]
            if state.turn == 2:
                dist -= 3 - (-j[0]-j[1])
        dist+= (state.features.score[state.turn][0])*6
        dist+= (state.features.score[state.turn][1])*12
        return dist

class Minimax:
    def __init__(self, features, functions, max_depth=2):
        self.features = features
        self.max_depth = max_depth
        self._f_terminal = functions.is_terminal
        self._f_evaluate = functions.euclid

    def find(self):
        state = Search_Node(self.features)
        for piece in state.features.state[state.turn]:
            if piece in state.goal:
                return (("EXIT", piece))
        future = self._minimax(state, self.max_depth)

        if future == state:
            return future.move

        while future.parent != state:
            future = future.parent

        return future.move

    def _minimax(self, state, depth):

        if self._f_terminal(state):
            state.turn = (state.turn - 1) % 3
            state.update_goal()
            return state

        if depth == 0:
            state.turn = (state.turn - 1) % 3
            state.update_goal()
            return state

        best_state = state
        best_value = float("-inf")
        state.get_children()

        for child in state.children:
            next_state = self._minimax(child, depth-1)
            if next_state == None:
                continue
            value = self._f_evaluate(next_state)
            if (value > best_value) or (value == best_value and random.random() < 0.3):
                best_state = next_state
                best_value = value

        best_state.turn = (best_state.turn - 1) % 3
        best_state.update_goal()
        return best_state

if __name__ == "__main__":
    main()
