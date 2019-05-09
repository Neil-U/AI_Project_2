import time
import copy
from Rush_Hour.player import Search_Node
from Rush_Hour.mctslib import mcts

class gameState:
	def __init__(self, state, **kwargs):
		self.features = state
		self.state = Search_Node(state)

	def getPossibleActions(self):
		return self.state.poss_moves()

	def takeAction(self, action):
		newState = self.features.update(action)
		return newState

	def isTerminal(self):
		for colour in self.features.score:
			if self.features.score[colour][1] == 4:
				return True
			else:
				return False

	def getReward(self):
		for colour in self.features.score:
			if self.features.score[colour][1] == 4:
				if colour == self.features.colour:
					return 1
				else:
					return 0


