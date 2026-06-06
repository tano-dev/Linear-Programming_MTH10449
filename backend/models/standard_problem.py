from backend.utils.formating import format_expression, clean_number

class StandardProblem:
    """
    The Linear Programming form after Standardizing. It is the data structure used in Simplex, Two-phase, or Dual Problem
    The Canonical Problem:
        min c^T x
        Ax <= b
        x >= 0
    """
    def __init__(self, c: list[float], A: list[list[float]], b: list[float], variable_names: list[str], is_from_max: bool):
        self.c = c
        self.A = A
        self.b = b
        self.variable_names = variable_names
        self.is_from_max = is_from_max
        self.need_two_phases = True if any(val < 0 for val in b) else False

    def show(self):
        objective_coeff = {var: coeff for var, coeff in zip(self.variable_names, self.c)}

        objective_str = format_expression(objective_coeff)

        print(f"- min {objective_str}" if self.is_from_max else f"min {objective_str}" )
        print("Subject to")

        for row, rhs in zip(self.A, self.b):

            constraint_coeffs = {var: coeff for var, coeff in zip(self.variable_names, row)}
            constraint_str = format_expression(constraint_coeffs)

            rhs = clean_number(rhs)

            print(f"{constraint_str} <= {rhs}")
        print()

        for var in self.variable_names:
            print(f"{var} >=0")

        print()