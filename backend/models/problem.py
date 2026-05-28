from .variable import Variable, VariableSign
from .constraint import Constraint, ConstraintType
from .objective import Objective, ObjectiveType

class Problem:
    """
    The entire linear programming problem.
    NOTE: This is a general problem -> Need to standardizing to the Canonical Problem
    """
    def __init__(self, objective: Objective, constraints: list[Constraint], variables: list[Variable]):
        self.objective = objective
        self.constraints = constraints
        self.variables = variables


    def __str__(self):
        result = str(self.objective) + "\n"
        for constraint in self.constraints:
            result += str(constraint) + "\n"
        for variable in self.variables:
            result += str(variable) + "\n"
        return result

