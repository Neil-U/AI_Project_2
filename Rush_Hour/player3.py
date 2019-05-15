import sys
import copy
import random
import time
import math
import numpy as np

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

TIME = {0: 500, 1: 1200, 2: 2000}

class Player:
    def __init__(self, colour):
        self.features = Features(RED)


    def action(self):
        self.mcts = MCTS(TIME[1])
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
        self.goal = {}
        self.update_goal()

    def update_goal(self):
        self.goal = {
            RED: {(3,-3), (3,-2), (3,-1), (3,0)},
            GREEN: {(-3,3), (-2,3), (-1,3), (0,3)},
            BLUE: {(0,-3), (-1,-2), (-2,-1), (-3,0)}}[self.colour]

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

        new.update_goal()

        return new

    def f_euclid(self, b, n):
        colour = self.colour
        if colour == 0:
            dist = n[0] - b[0] + 1
        if colour == 1:
            dist = n[1] - b[1] + 1
        if colour == 2:
            dist = (-n[0] - n[1]) - (-b[0]-b[1]) + 1
        return dist

    def prune(self, b, n):
        if self.f_euclid(b, n):
            return False
        return True

    def simulation(self, colour):
        delay = 1
        score = self.score
        while self.isTerminal(colour, score) is False:
            self = self.update(random.choice(self.f_possibleMoves()))
            delay += 1
        return self, delay

    def f_possibleMoves(self):
        poss_moves = []
        occupied = set().union(*self.state.values())

        for piece in self.state[self.colour]:
            if piece in self.goal:
                poss_moves.append(("EXIT", piece))
                continue

            for i,j in [(-1,0),(-1,1), (0,-1), (0,1), (1,0), (1,-1)]:
                new = (piece[0]+i,piece[1]+j)
                new_jump = (new[0] + i, new[1] + j)

                if new in BOARD:
                    if new not in occupied:
                        #if self.features.prune(piece, new) is False:
                        poss_moves.append(("MOVE", (piece, new)))
                    elif new_jump in BOARD and new_jump not in occupied:
                        poss_moves.append(("JUMP", (piece, new_jump)))

        if not poss_moves:
            poss_moves.append(("PASS", None))
        return poss_moves

    def isTerminal(self, colour, score):
        for c in self.score.keys():
            if self.score[c][1] > score[c][1]:
                return True
        if self.score[colour][0] == 0:
            return True
        return False


class MCTS_Node():
    def __init__(self, features, index, parent=None):
        self.features = features
        self.parent = parent
        self.index = index
        self.goal = {}
        self.turn = self.features.colour
        self.update_goal()
        self.isFullyExpanded = False
        self.possMoves = self.possibleMoves()
        self.visits = np.zeros(len(self.possMoves), dtype=np.float32)
        self.childVisits = np.zeros(len(self.possMoves), dtype=np.float32)
        self.childRewards = np.zeros(len(self.possMoves), dtype=np.float32)
        self.numChildren = 0
        self.children = {}

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
                        if self.features.prune(piece, new) is False:
                            poss_moves.append(("MOVE", (piece, new)))

                    elif new_jump in BOARD and new_jump not in occupied:
                        poss_moves.append(("JUMP", (piece, new_jump)))

        if not poss_moves:
            poss_moves.append(("PASS", None))
        return poss_moves

    def doMove(self, move, index):
        newState = self.features.update(move)
        return MCTS_Node(newState, index, self)

    def getReward(self, node, delay):
        # get an exit
        colour = node.features.colour
        if sum(self.features.score[colour]) < 4:
            return -6/delay
        elif self.features.score[colour][1] > node.features.score[colour][1]:
            if self.features.score[colour][0] > node.features.score[colour][0]:
                return 12/delay
            else:
                return 4/delay
        return -4/delay

    def changeReward(self, value):
        self.parent.childRewards[self.index] += value

    def addVisit(self):
        self.parent.childVisits[self.index] += 1

    def numVisits(self):
        return self.parent.childVisits[self.index]

class MCTS():
    def __init__(self, timeLimit = None, explorationConstant = math.sqrt(2)):
        if timeLimit == None:
            raise ValueError("Need a time limit")
        else:
            self.timeLimit = timeLimit
            self.explorationConstant = explorationConstant

    def search(self, features):
        self.root = MCTS_Node(copy.deepcopy(features), None)

        timeLimit = time.time() + self.timeLimit/1000
        while time.time() < timeLimit:
            self.dive()
        bestIndex = self.getBestChild(self.root, 0)
        return self.root.possMoves[bestIndex]

    def dive(self):
        node = self.root
        self.expand(node)
        while node.isTerminal(self.root.features.colour) is False:
            node.visits += 1
            if node.isFullyExpanded is True:
                index = self.getBestChild(node, self.explorationConstant)
                if node.possMoves[index] not in node.children:
                    node.children[node.possMoves[index]] = node.doMove(node.possMoves[index], index)
                node = node.children[node.possMoves[index]]
            else:
                self.expand(node)
                break

        node2 = node
        if node2.isTerminal(self.root.features.colour) is True:
            reward = node2.getReward(self.root, delay = 1)
        else:
            feature, delay = node2.features.simulation(self.root.features.colour)
            node2 = MCTS_Node(feature, None)
            reward = node2.getReward(self.root, delay)
        self.propogate(node, reward)

    def propogate(self, node, reward):
        while node.parent is not None:
            node.addVisit()
            node.changeReward(reward)
            node = node.parent

    def expand(self, node):
        node.isFullyExpanded = True

    def getBestChild(self, node, explorationValue):
        if explorationValue == 0:
            print(self.root.features.colour)
            print('a')
            for i in range(len(node.childRewards)):
                print(node.possMoves[i], node.childRewards[i], node.childVisits[i])
        values = node.childRewards / (1 + node.childVisits) + explorationValue * np.sqrt(np.log(node.visits)/(1 + node.childVisits))
        return np.argmax(values)

def main():
    hey = Player(0)
    hey.update(0, hey.action())
    hey.update(0, hey.action())
    hey.update(0, hey.action())
    hey.update(0, hey.action())
    hey.update(0, hey.action())

if __name__ == "__main__":
    main()
