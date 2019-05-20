import math
import time
import numpy as np

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
        """
        search sets a given input 'state' as the root of the tree and returns
        the best move from this state
        """
        state.to_mcts()
        state.mcts_parent = None
        self.root = state

        timeLimit = time.time() + self.timeLimit/1000
        while time.time() < timeLimit:
            self.dive()

        # set explorationvalue as 0 as want to exploit the best move
        bestIndex = self.getBestChild(self.root, 0)
        return self.root.children[bestIndex]

    def dive(self):
        """
        dive does a deep dive, selecting moves depending on the exploration
        constant until a terminal state is reached
        """

        # we search through the current tree until an unvisited node is reached
        node = self.root
        while node.is_terminal(self.root) is False:
            if node.isFullyExpanded is True:
                node.visits += 1
                index = self.getBestChild(node, self.explorationConstant)
                node = node.children[index]
            else:
                # we expand the first univsited node found
                self.expand(node)
                break

        # we simulate a game from the newly expanded node and propogate
        # the reward from this poisition
        node2 = node
        if node2.is_terminal(self.root) is True:
            reward = node2.getReward(self.root, delay = 1)
        else:
            feature, delay = node2.simulation(self.root)
            reward = node2.getReward(self.root, delay)
        self.propogate(node, reward)

    def propogate(self, node, reward):
        """
        propogate adds the values and changes the rewards of the states
        that led to the terminal state found
        """
        while node.mcts_parent is not None:
            node.addVisit()
            node.changeReward(reward)
            node = node.mcts_parent

    def expand(self, node):
        """
        expand converts the current node into one for the MCTS tree and
        expands it
        """
        node.get_children()
        node.to_mcts()

    def getBestChild(self, node, explorationValue):
        """
        returns the index of the best child depending on the
        exploration value provided
        """
        values = node.childRewards / ((1 + node.childVisits) + explorationValue
                        * np.sqrt(np.log(node.visits)/(1 + node.childVisits)))
        return np.argmax(values)
