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
        self.isTerminal = self.isTerminal()
        self.isFullyExpanded = False
        self.numVisits = 0
        self.totalReward = 0
        self.children = {}
        self.turn = self.features.colour
        self.goal = {}
        self.update_goal()

    def update_goal(self):
        self.goal = {
            RED: {(3,-3), (3,-2), (3,-1), (3,0)},
            GREEN: {(-3,3), (-2,3), (-1,3), (0,3)},
            BLUE: {(0,-3), (-1,-2), (-2,-1), (-3,0)}}[self.features.colour]

    def isTerminal(self):
        if self.parent is None:
            return False
        for c in self.features.score.keys():
            if self.features.score[c][1] > self.parent.features.score[c][1]:
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

    def doMove(self, move, parent):
        newState = self.features.update(move)
        return MCTS_Node(newState, parent)

    def getReward(self, colour):
        if self.features.score[colour][1] > self.parent.features.score[colour][1]:
                return 1
        for i in [1,2]:
            if self.features.score[(colour + i) % 3][1] > self.parent.features.score[(colour + i) % 3][1]:
                    return -1
        return 0

    def isSole(self):
        for i in [1,2]:
            if self.features.score[(self.features.colour + i) % 3][0] != 0:
                return False
        return True

    def euclid(self, colour):
        dist = 0
        for j in self.features.state[colour]:
            if colour == 0:
                dist -= 3 - j[0]
            if colour == 1:
                dist -= 3 - j[1]
            if colour == 2:
                dist -= 3 - (-j[0]-j[1])
        return dist

    def huer(self, colour):
        dist = 0
        for j in self.features.state[colour]:
            if colour == 0:
                dist -= 3 - j[0]
            if colour == 1:
                dist -= 3 - j[1]
            if colour == 2:
                dist -= 3 - (-j[0]-j[1])
        dist+= (self.features.score[colour][1])*12
        return dist

class MCTS():
    def __init__(self, timeLimit = None, explorationConstant = math.sqrt(2)):
        if timeLimit == None:
            raise ValueError("Need a time limit")
        else:
            self.timeLimit = timeLimit
            self.explorationConstant = explorationConstant

    def search(self, features):
        self.root = MCTS_Node(copy.deepcopy(features))
        timeLimit = time.time() + self.timeLimit/1000
        while time.time() < timeLimit:
            self.dive()
        if self.root.isSole():
            print('a')
            bestChild = self.solegetBestChild(self.root)
        else:
            print('a')
            bestChild = self.getBestChild(self.root, 0)
        for move, node in self.root.children.items():
            if node is bestChild:
                return move

    def dive(self):
        node = self.root
        while node.isTerminal == False:
            if node.isFullyExpanded is True:
                node = self.getBestChild(node, self.explorationConstant)
            else:
                self.expand(node)
                node = node.children[random.choice(list(node.children.keys()))]
                break

        while node.isTerminal == False:
            move = random.choice(node.possibleMoves())
            if move not in node.children:
                node.children[move] = node.doMove(move, node)
            node = node.children[move]
        reward = node.getReward(self.root.features.colour)

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
        for child in node.children.values():
            value = child.totalReward / (1+ child.numVisits) + explorationValue * (
                2*child.features.score[self.root.features.colour][1] +
                child.features.score[self.root.features.colour][0])
            if value > bestValue:
                bestValue = value
                bestNodes = [child]
            elif value == bestValue:
                bestNodes.append(child)
        return random.choice(bestNodes)

    def solegetBestChild(self, node):
        bestValue = float("-inf")
        bestNodes = []
        for child in node.children.values():
            value = child.huer(self.root.features.colour)
            if value > bestValue:
                bestValue = value
                bestNodes = [child]
            elif value == bestValue:
                bestNodes.append(child)
        return random.choice(bestNodes)

def main():
    hey = Player(0)

if __name__ == "__main__":
    main()
