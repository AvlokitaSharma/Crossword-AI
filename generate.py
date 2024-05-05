import sys

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        This involves ensuring that all words in the domain of a variable
        have the same length as the variable requires.
        """

        for variable in self.domains:
            words_to_remove = set()
            for word in self.domains[variable]:
                if len(word) != variable.length:
                    words_to_remove.add(word)
            for word in words_to_remove:
                self.domains[variable].remove(word)


    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """

        revised = False
        overlap = self.crossword.overlaps[x, y]
        if overlap is None:
            return False

        i, j = overlap  # Indices where x and y overlap
        to_remove = []

        for word_x in self.domains[x]:
            match_found = False
            for word_y in self.domains[y]:
                if word_x[i] == word_y[j]:
                    match_found = True
                    break
            if not match_found:
                to_remove.append(word_x)

        for word in to_remove:
            self.domains[x].remove(word)
            revised = True

        return revised

    def ac3(self, arcs=None):
        """
        Update `self.domains` to ensure each variable is arc-consistent using the AC3 algorithm.
        An arc (x, y) is processed to ensure that for every value in the domain of x, there is some
        allowed value in the domain of y.

        :param arcs: Optional, a list of arcs to start with. If None, start with all arcs in the problem.
        :return: True if arc consistency is achieved without emptying any domain, False otherwise.
        """
        
        if arcs is None:
            arcs = [(x, y) for x in self.crossword.variables for y in self.crossword.neighbors(x)]

        queue = arcs.copy()

        while queue:
            (x, y) = queue.pop(0)
            if self.revise(x, y):
                if len(self.domains[x]) == 0:
                    return False
                for neighbor in self.crossword.neighbors(x) - {y}:
                    queue.append((neighbor, x))
        
        return True


    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """

        return not len(set(self.crossword.variables - assignment.keys()))
        

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        
        if len(list(assignment.values())) != len(set(assignment.values())): return False
        
        for i in assignment:
            if len(assignment[i]) != i.length: return False
            
        for i in assignment:
            n = self.crossword.neighbors(i)
            for j in n:
                if j in set(assignment.keys()):
                    if assignment[i][self.crossword.overlaps[(i,j)][0]] != assignment[j][self.crossword.overlaps[(i,j)][1]]: return False
        
        return True
        

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        def _neighbor(temp, v):
            count = 0
            if temp not in assignment:
                for i in self.domains[temp]:
                    if i == v: count += 1
                        
                    elif self.crossword.overlaps[var, temp]:
                        k, j = self.crossword.overlaps[var, temp]
                        if v[k] != i[j]: count += 1
            return count
        
        def _value(val):
            count = 0
            temp = self.domains[var].copy()
            self.domains[var] = set([val])
            
            for i in self.crossword.neighbors(var):
                if i in _vars: count += _neighbor(i, val)
            self.domains[var] = temp
            return count

        if not self.domains[var]: return []
            
        temp_domain = self.domains.copy()

        for i in assignment: self.domains[i] = set([assignment[i]])
            

        _vars = set(self.crossword.variables - set(assignment.keys()))

        _val = sorted(self.domains[var], key = lambda value: _value(value))
        
        self.domains = temp_domain
        
        _val = self.domains[var].copy()
        return _val

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        _vars = list(self.crossword.variables - set(assignment.keys()))
        sorted_vars_left = sorted(_vars, key=lambda var: (len(self.domains[var]), -len(self.crossword.neighbors(var))))
        return sorted_vars_left[0] if sorted_vars_left else None

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        if not self.consistent(assignment): return None
        if self.assignment_complete(assignment): return assignment
        _var = self.select_unassigned_variable(assignment)
        for i in self.order_domain_values(_var, assignment):
            assignment[_var] = i
            result = self.backtrack(assignment)
            if result is not None: return result
                
            del assignment[_var]
        return None


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
