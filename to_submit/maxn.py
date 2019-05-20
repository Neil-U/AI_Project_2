from .mcts import MCTS
from .nodes import Search_Node

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

