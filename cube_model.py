import itertools
import math

def nCr(n, r):
    """Calculates the binomial coefficient C(n, k)."""
    if r < 0 or r > n:
        return 0
    r = min(r, n - r)
    if r == 0:
        return 1
    # Using integer division throughout to prevent floating point errors
    numer = 1
    for i in range(r):
        numer = numer * (n - i) // (i + 1)
    return numer

class Cube:
    def __init__(self):
        self.cp = list(range(8))
        self.co = [0] * 8
        self.ep = list(range(12))
        self.eo = [0] * 12

    def __str__(self):
        return f"cp: {self.cp}\nco: {self.co}\nep: {self.ep}\neo: {self.eo}"

    def _cycle_pieces(self, p, pieces, orientation_delta=None):
        
        # --- Permute Pieces ---
        last_piece = p[pieces[-1]]
        for i in range(len(pieces) - 1, 0, -1):
            p[pieces[i]] = p[pieces[i-1]]
        p[pieces[0]] = last_piece

        # --- Permute Orientations ---
        o = self.co if p is self.cp else self.eo
        last_orientation = o[pieces[-1]]
        for i in range(len(pieces) - 1, 0, -1):
            o[pieces[i]] = o[pieces[i-1]]
        o[pieces[0]] = last_orientation

        # --- Apply Orientation Deltas ---
        if orientation_delta:
            mod = 3 if o is self.co else 2
            for i in range(len(pieces)):
                o[pieces[i]] = (o[pieces[i]] + orientation_delta[i]) % mod
    
    def _apply_single_move(self, move):
        if move == 'U':
            self._cycle_pieces(self.cp, [0, 1, 2, 3])
            self._cycle_pieces(self.ep, [0, 1, 2, 3])
        elif move == 'D':
            self._cycle_pieces(self.cp, [4, 7, 6, 5])
            self._cycle_pieces(self.ep, [4, 5, 6, 7])
        elif move == 'L':
            self._cycle_pieces(self.cp, [0, 4, 5, 1], [2, 1, 2, 1])
            self._cycle_pieces(self.ep, [0, 11, 4, 8])
        elif move == 'R':
            self._cycle_pieces(self.cp, [2, 6, 7, 3], [1, 2, 1, 2])
            self._cycle_pieces(self.ep, [2, 9, 6, 10])
        elif move == 'F':
            self._cycle_pieces(self.cp, [1, 5, 6, 2], [1,2,1,2])
            self._cycle_pieces(self.ep, [1, 8, 5, 9], [1,1,1,1])
        elif move == 'B':
            self._cycle_pieces(self.cp, [3, 7, 4, 0], [1,2,1,2])
            self._cycle_pieces(self.ep, [3, 10, 7, 11], [1,1,1,1])

    def apply_move(self, move_str):
        for move in move_str.split():
            if len(move) == 1:
                self._apply_single_move(move)
            elif move[1] == "'":
                self._apply_single_move(move[0])
                self._apply_single_move(move[0])
                self._apply_single_move(move[0])
            elif move[1] == '2':
                self._apply_single_move(move[0])
                self._apply_single_move(move[0])

    def corner_orientation_coord(self):
        coord = 0
        for i in range(7):
            coord = coord * 3 + self.co[i]
        return coord

    def edge_orientation_coord(self):
        coord = 0
        for i in range(11):
            coord = coord * 2 + self.eo[i]
        return coord

    def ud_slice_coord(self):
        """
        Calculates a coordinate for the UD slice edges.
        The 4 UD slice edges are those with original indices 8, 9, 10, 11.
        The coordinate is a combinatorial number from 0 to C(12,4)-1 = 494.
        """
        coord = 0
        k = 4
        # Iterate through the 12 edge positions from highest to lowest
        for n in range(11, -1, -1):
            # If we find a slice edge and we still need to count slice edges
            if k > 0 and self.ep[n] >= 8:
                # Add C(n, k) to the coordinate
                coord += nCr(n, k)
                k -= 1
        return coord
