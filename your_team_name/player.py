import sys

BOARD = set()
for i in range(-3,1):
    for j in range(-3-i, 4):
        BOARD.add((i,j))
for i in range(1,4):
    for j in range(-3,4-i):
        BOARD.add((i,j))

COLOUR_LIST = ['red', 'green', 'blue']

def main():
    player = Player('red')

class Player:
    def __init__(self, colour):
        """
        This method is called once at the beginning of the game to initialise
        your player. You should use this opportunity to set up your own internal
        representation of the game state, and any other information about the
        game state you would like to maintain for the duration of the game.

        The parameter colour will be a string representing the player your
        program will play as (Red, Green or Blue). The value will be one of the
        strings "red", "green", or "blue" correspondingly.
        """
        # TODO: Set up state representation.
        ind = COLOUR_LIST.index(colour)
        self.colour = 0
        self.colour_dic = {'red': (ind) % 3,
            'green': (ind + 1) % 3, 'blue': (ind + 2) % 3}
        self.period = 0
        self.turn = self.colour_dic['red']
        self.score = {0: [4, 0], 1: [4, 0], 2: [4, 0]}
        self.state = []
        self.neighbours = {}
        self.initial_state()

    def action(self):
        """
        This method is called at the beginning of each of your turns to request
        a choice of action from your program.

        Based on the current state of the game, your player should select and
        return an allowed action to play on this turn. If there are no allowed
        actions, your player must return a pass instead. The action (or pass)
        must be represented based on the above instructions for representing
        actions.
        """
        # TODO: Decide what action to take.
        return ("PASS", None)


    def update(self, colour, action):
        """
        This method is called at the end of every turn (including your player’s
        turns) to inform your player about the most recent action. You should
        use this opportunity to maintain your internal representation of the
        game state and any other information about the game you are storing.

        The parameter colour will be a string representing the player whose turn
        it is (Red, Green or Blue). The value will be one of the strings "red",
        "green", or "blue" correspondingly.

        The parameter action is a representation of the most recent action (or
        pass) conforming to the above in- structions for representing actions.

        You may assume that action will always correspond to an allowed action
        (or pass) for the player colour (your method does not need to validate
        the action/pass against the game rules).
        """
        curr_colour = self.colour_dic[colour]
        change = action[1]
        if action[0] == "MOVE":
            self.state[curr_colour].remove(change[0])
            self.state[curr_colour].add(change[1])
        elif action[0] == "JUMP":
            self.state[curr_colour].remove(change[0])
            self.state[curr_colour].add(change[1])
            middle_piece = ((change[0][0] + change[1][0])/2,
                (change[0][1] + change[1][1])/2)
            self.state[curr_colour].add(middle_piece)
            self.score[curr_colour]
            for i in [1,2]:
                if middle_piece in self.state[curr_colour + i]:
                    self.state[curr_colour + i].remove(middle_piece)
        elif action[0] == 'EXIT':
            self.state[curr_colour].remove(change)
        self.update_neighbours()
        self.turn += 1
        # TODO: Update state representation in response to action.

    def initial_state(self):
        self.state = {
            self.colour_dic['red']: {(-3, 0), (-3, 1), (-3, 2), (-3, 3)},
            self.colour_dic['green']: {(0, -3), (1, -3), (2, -3), (3, -3)},
            self.colour_dic['blue']: {(3, 0), (2, 1), (1, 2), (0, 3)}}
        self.update_neighbours()

    def update_neighbours(self):
        occupied = set().union(*self.state.values())
        for piece in self.state[self.colour]:
            self.neighbours[piece] = set()
            for i,j in [(-1,0),(-1,1), (0,-1), (0,1), (1,0), (1,-1)]:
                new = (piece[0]+i,piece[1]+j)
                new_jump = (new[0] + i, new[1] + j)
                if new in BOARD:
                    if new not in occupied:
                        self.neighbours[piece].add(new)
                    elif new_jump in BOARD and new_jump not in occupied:
                        self.neighbours[piece].add(new_jump)

class

if __name__ == '__main__':
    main()
