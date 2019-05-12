import time
import math
import random

class MCTS_Node:
	def __init__(self, features, parent=None):
		self.features = features
		self.parent = parent
		self.isTerminal = self.isTerminal()
		self.isFullyExpanded = self.isTerminal
		self.numVisits = 0
		self.totalReward = 0
		self.children = {}

	def isTerminal(self):
    	for c in self.features.score.keys():
            if self.features.score[c][1] == 4:
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

    def getReward(self):
    	for colour in self.features.score:
            if self.features.score[colour][1] == 4:
                if colour == self.features.colour:
                    return 1
        return 0

class mcts:
	def __init__(self, timeLimit = None, explorationConstant = math.sqrt(2)):
		if timeLimit == None:
			raise ValueError("Need a time limit")
		else:
			self.timeLimit = timeLimit
			self.explorationConstant = explorationConstant

	def search(self, features):
		self.root = MCTS_Node(features)

		timeLimit = time.time() + self.timeLimit/1000
		while time.time() < timeLimit:
			self.dive()

		# 0 for exploitation constant as no exploration value
		bestChild = self.getBestChild(self.root, 0)
		for move, node in self.root.children.items():
			if node is bestChild:
				return move

	def dive(self):
		node = self.root
		while node.isTerminal == False:
			if node.isFullyExpanded:
				node = self.getBestChild(node, self.explorationConstant)
			else:
				node = self.expand(node)
				break

		node2 = node
		while node.isTerminal == False:
			move = random.choice(node.possibleMoves())
			node2 = node2.doMove(move)
		reward = node2.getReward()

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
    			if len(moves) == len(node.children):
    				node.isFullyExpanded = True
    			return new

    def getBestChild(self, node, exploration):
    	bestValue = float("-inf")
    	bestNodes = []
    	for child in node.children.values():
    		value = child.totalReward / child.numVisits + explorationValue * math.sqrt(
                2 * math.log(node.numVisits) / child.numVisits)
            if value > bestValue:
            	bestValue = value
            	bestNodes = [child]
            elif value == bestValue:
            	bestNodes.append(child)
        return random.choice(bestNodes)

