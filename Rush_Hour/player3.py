import sys
import copy
import random
import time
import math

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

EXPLORATION = 1
TIME = 2000

class Player:
    def __init__(self, colour):
        self.features = Features(RED)


    def action(self):
        self.mcts = MCTS(TIME)
        return self.mcts.search(self.features)

    def update(self, colour, action):
        self.features = self.features.update(action)


class Features:
    def __init__(self, colour):
        self.colour = colour
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

class MCTS_Node():
    def __init__(self, features, parent=None):
        self.features = features
        self.parent = parent
        self.isFullyExpanded = False
        self.numVisits = 0
        self.totalReward = 0
        self.children = {}
        self.goal = {}
        self.turn = self.features.colour
        self.update_goal()

    def update_goal(self):
        self.goal = {
            RED: {(3,-3), (3,-2), (3,-1), (3,0)},
            GREEN: {(-3,3), (-2,3), (-1,3), (0,3)},
            BLUE: {(0,-3), (-1,-2), (-2,-1), (-3,0)}}[self.features.colour]

    def isTerminal(self, colour):
        if self.parent is None:
            return False
        for c in self.features.score.keys():
            if self.features.score[c][1] > self.parent.features.score[c][1]:
                return True
        if self.features.score[colour][0] == 0:
            return True
        return False

    def possibleMoves(self):
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

    def doMove(self, move):
        newState = self.features.update(move)
        return MCTS_Node(newState, self)

    def getReward(self, colour):
        if self.features.score[colour][1] > self.parent.features.score[colour][1]:
                return sum(self.features.score[colour])/2
        for i in [1,2]:
            if self.features.score[(colour + i) % 3][1] > self.parent.features.score[(colour + i) % 3][1]:
                    return -4/sum(self.features.score[colour])
        if self.features.score[colour][0] == 0:
            return -2
        return 0

    def isSole(self):
        for i in [1,2]:
            if self.features.score[(self.features.colour + i) % 3][0] != 0:
                return False
        return True

    def euclid(self):
        dist = 0
        colour = self.features.colour
        for j in self.features.state[colour]:
            if colour == 0:
                dist -= 3 - j[0]
            if colour == 1:
                dist -= 3 - j[1]
            if colour == 2:
                dist -= 3 - (-j[0]-j[1])
        dist+= (self.features.score[colour][0])*6
        dist+= (self.features.score[colour][1])*12
        return dist

    def huer(self):
        dist = 0
        for j in self.features.state[self.features.colour]:
            if colour == 0:
                dist -= 3 - j[0]
            if colour == 1:
                dist -= 3 - j[1]
            if colour == 2:
                dist -= 3 - (-j[0]-j[1])
        dist+= (self.features.score[colour][1])*12
        return dist

    def find(self):
        for piece in self.features.state[self.features.colour]:
            if piece in self.goal:
                return self.doMove(("EXIT", piece))
        future = self._minimax(2)

        while future.parent != self:
            future = future.parent
        return future

    def _minimax(self, depth):

        if self.isTerminal(self.features.colour) or depth == 0:
            self.turn = (self.turn - 1) % 3
            self.update_goal()
            return self

        best_state = self
        best_value = float("-inf")
        moves = self.possibleMoves()

        for move in moves:
            child = self.doMove(move)
            next_state = child._minimax(depth-1)
            if next_state is None:
                continue
            value = next_state.euclid()
            if (value > best_value) or (value == best_value and random.random() < 0.3):
                best_state = next_state
                best_value = value

        best_state.turn = (best_state.turn - 1) % 3
        best_state.update_goal()
        return best_state


class MCTS():
    def __init__(self, timeLimit = None, explorationConstant = 1):
        if timeLimit == None:
            raise ValueError("Need a time limit")
        else:
            self.timeLimit = timeLimit
            self.explorationConstant = explorationConstant

    def search(self, features):
        self.root = MCTS_Node(copy.deepcopy(features))
        if self.root.isSole():
            bestChild = self.sologetBestChild(self.root)
        timeLimit = time.time() + self.timeLimit/1000
        while time.time() < timeLimit:
            self.dive()
        print('a')
        bestChild = self.getBestChild(self.root, 0)
        for move, node in self.root.children.items():
            if node is bestChild:
                return move

    def dive(self):
        node = self.root
        while node.isTerminal(self.root.features.colour) == False:
            if node.isFullyExpanded is True:
                node = self.getBestChild(node, self.explorationConstant)
            else:
                self.expand(node)
                node = node.children[random.choice(list(node.children.keys()))]
                break

        node2 = node
        while node2.isTerminal(self.root.features.colour) == False:
            move = random.choice(node2.possibleMoves())
            node2 = node2.doMove(move)
        reward = node2.getReward(self.root.features.colour)

        self.propogate(node, reward)

    def propogate(self, node, reward):
        while node is not None:
            node.numVisits += 1
            node.totalReward += reward
            node = node.parent

    def expand(self, node):
        moves = node.possibleMoves()
        for move in moves:
            if move not in node.children.keys():
                new = MCTS_Node(node.features.update(move), node)
                node.children[move] = new
                node.isFullyExpanded = True

    def getBestChild(self, node, explorationValue):
        bestValue = float("-inf")
        bestNodes = []
        for move, child in node.children.items():
            value = child.totalReward / (1+ child.numVisits) + explorationValue * math.sqrt(
                2 * math.log(node.numVisits) / (1+ child.numVisits))
            if explorationValue == 0:
                print(move, child.numVisits, value)
            if value > bestValue:
                bestValue = value
                bestNodes = [child]
            elif value == bestValue:
                bestNodes.append(child)
        return random.choice(bestNodes)

    def solegetBestChild(self, node):
        bestValue = float("-inf")
        bestNodes = []
        for move, child in node.children.items():
            value = child.huer(self.root.features.colour)
            if value > bestValue:
                bestValue = value
                bestNodes = [move]
            elif value == bestValue:
                bestNodes.append(move)
        return random.choice(bestNodes)

def main():
    hey = Player(0)
    hey.update(0, hey.action())
    hey.update(0, hey.action())
    hey.update(0, hey.action())
    hey.update(0, hey.action())
    hey.update(0, hey.action())
    hey.update(0, hey.action())
    hey.update(0, hey.action())
    hey.update(0, hey.action())
    hey.update(0, hey.action())

if __name__ == "__main__":
    main()
