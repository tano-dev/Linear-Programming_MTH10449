from enum import Enum

from backend.utils import format_expression

class ConstraintType(Enum):
    """
    Type of constraint: <=, >=, =
    """
    LE = "<="
    GE = ">="
    EQ = "="

class Constraint:
    """
    Constraint: 
        - Coefficients : dict {"x1": 1,...}
        - Constraint Type
        - right_hand-side: is b in Ax (<=/ >= / =) b
    """
    def __init__(self, coeffs: dict[str, float], constraint_type, right_hand_side: float):
        self.coeffs = coeffs
        self.constraint_type = constraint_type
        self.right_hand_side = right_hand_side

    def __str__(self):
        left = format_expression(self.coeffs)
        
        return f"{left} {self.constraint_type.value} {self.right_hand_side}" 