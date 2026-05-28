from enum import Enum

from backend.utils import format_expression

class ObjectiveType(Enum):
    """
    Min or Max
    """
    MIN = "min"
    MAX = "max"


class Objective:
    """
    Objective function: include objective type (min/ max) and coefficients
    Ex: min z = 3x1 - 2x2 + 5x3
    """
    def __init__(self, objective_type, coeffs: dict[str, float]):
        self.objective_type = objective_type
        self.coeffs = coeffs

    def __str__(self):
        expression = format_expression(self.coeffs)

        return f"{self.objective_type.value} z = {expression}"
        