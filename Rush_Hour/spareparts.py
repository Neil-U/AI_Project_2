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
