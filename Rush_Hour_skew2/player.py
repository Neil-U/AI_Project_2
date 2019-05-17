import sys
import copy
import random
import numpy as np
import math
import time

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

class Player:
    def __init__(self, colour):
        self.features = Features(RED)

    def action(self):
        if not self.features.state[self.features.colour]:
            return ("PASS", None)
        maxn = Minimax(self.features)
        return maxn.find()

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
        self.isFullyExpanded = False
        self.depth = 1
        self.update_goal()

    def is_terminal(self, root):
        colour = root.features.colour
        if len(self.features.state[colour]) == 0:
            return True
        if self.features.score[colour][1] > root.features.score[colour][1]:
            return True
        return False

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

    def manhat(self, colour = None):
        if colour == None:
            colour = self.turn
        dist = 0
        if self.features.score[colour][0] == 0:
            return 10
        for j in self.features.state[colour]:
            if self.turn == 0:
                dist += 3 - j[0]
            if self.turn == 1:
                dist += 3 - j[1]
            if self.turn == 2:
                dist += 3 - (-j[0]-j[1])
        return dist/(self.features.score[colour][0])

    def eat(self, prior):
        diff =  self.features.score[self.turn][1] - prior.features.score[self.turn][1]
        return self.features.score[self.turn][0] + diff - prior.features.score[self.turn][0]

    def leave(self):
        return (self.features.score[self.turn][1])

    def total_three(self, prior):
        lst = []
        for colour in self.features.state:
            if colour != self.turn:
                lst.append((self.features.score[colour][0]+ 2*self.features.score[colour][1], colour))
        colour = max(lst)[1]
        print(colour)
        return (prior.manhat(colour) - self.manhat(colour)) + 9*(self.eat(prior)) + -1*(self.leave() - prior.leave())

    def total_four_five(self, prior):
        return (prior.manhat() - self.manhat()) + 8*(self.eat(prior)) + 4*(self.leave() - prior.leave())

    def total_six_seven(self, prior):
        return (prior.manhat() - self.manhat()) + 3*(self.eat(prior)) + 3*(self.leave() - prior.leave())

    def total_eight_nine(self, prior):
        return (prior.manhat() - self.manhat()) + 3*(self.eat(prior)) + 6*(self.leave() - prior.leave())

    def total_more_than_nine(self, prior):
        return (prior.manhat() - self.manhat()) + 6*(self.eat(prior)) + 12*(self.leave() - prior.leave())

    def to_mcts(self):
        self.isFullyExpanded = True
        self.visits = np.zeros(len(self.children), dtype=np.float32)
        self.childVisits = np.zeros(len(self.children), dtype=np.float32)
        self.childRewards = np.zeros(len(self.children), dtype=np.float32)
        self.visits = np.zeros(len(self.children), dtype=np.float32)
        index = 0
        for child in self.children:
            child.index = index
            child.mcts_parent = self
            index += 1

    def getReward(self, root, delay):
        if self.features.score[root.features.colour][1] > root.features.score[root.features.colour][1]:
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

    def choose_function(self, prior, colour):
        self.turn = prior.turn
        total = sum(prior.features.score[prior.turn])
        for i in [1,2]:
            if sum(prior.features.score[prior.turn]) < sum(prior.features.score[(prior.turn + i)%3]):
                return self.total_three(prior)

        if total <= 3:
            return self.total_three(prior)
        elif 4 <= total <= 5:
            return self.total_four_five(prior)
        elif 6 <= total <= 7:
            return self.total_six_seven(prior)
        elif 8 <= total <= 9:
            return self.total_eight_nine(prior)
        else:
            return self.total_more_than_nine(prior)

    def choose_depth(self):
        on_board = 0

        for colour in self.features.score:
            on_board += self.features.score[colour][0]

        if 3 <= on_board <= 12:
            return 3
        elif 1 <= on_board <= 3:
            return 6
        else:
            return 9

    def paranoid_addition(self, state, colour):
        if state.features.colour != colour:
            if sum(self.features.score[colour]) < sum(state.features.score[colour]):
                return 2
        return 0


class Minimax:
    def __init__(self, features):
        self.features = features
        self.root = Search_Node(self.features)

    def find(self):
        state = self.root
        self.max_depth = state.choose_depth()
        future = self._minimax(state, self.max_depth)

        return future.move

    def _minimax(self, state, depth):

        if state.is_terminal(self.root):
            state.turn = (state.turn - 1) % 3
            state.update_goal()
            return state

        if depth == 0:
            state.turn = (state.turn - 1) % 3
            state.update_goal()
            return state

        best_states = [state]
        best_value = float("-inf")
        state.get_children()

        for child in state.children:
            next_state = self._minimax(child, depth-1)
            next_state.depth = state.depth + .5
            if next_state == None:
                continue
            value = next_state.choose_function(state, self.root.features.colour)/next_state.depth
            value += next_state.paranoid_addition(state, self.root.features.colour)
            if (value > best_value):
                best_states = [next_state]
                best_value = value
            elif value == best_value:
                best_states.append(next_state)

        best_state = random.choice(best_states)
        if len(best_states) == 1 or depth != self.max_depth:
            best_state = random.choice(best_states)
        else:
            mcts = MCTS(1000)
            state.children = best_states
            best_state = mcts.search(state)

        if depth != self.max_depth:
            best_state.move = state.move

        best_state.turn = (best_state.turn - 1) % 3
        best_state.update_goal()
        return best_state

class MCTS():
    def __init__(self, timeLimit = None, explorationConstant = math.sqrt(2)):
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


def main():
    hey = Player(0)
    hey.action()

if __name__ == "__main__":
    main()
