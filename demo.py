from backend.models import (
    Variable, VariableSign,
    Constraint, ConstraintType,
    Objective, ObjectiveType,
    Problem,
    CanonicalProblem
)

from backend.cores import LPSolver
if __name__ == "__main__":

    # Problem (P): min 23x_1 - 7x_2
    # Subject to -2x_1 + x_2 <= -1
    #              x_1 + x_2 <= 5
    #              -x_1 - x_2 <= -2

    # Setup variables
    x1 = Variable("x_1", VariableSign.NON_NEGATIVE)
    x2 = Variable("x_2", VariableSign.NON_NEGATIVE)
    x = [x1, x2]

    # Setup constraints
    constraints = [
        Constraint({"x_1": -2, "x_2": 1}, ConstraintType.LE, -1),
        Constraint({"x_1": 1, "x_2": 1}, ConstraintType.LE, 5),
        Constraint({"x_1": -1, "x_2": -1}, ConstraintType.LE, -2),
    ]

    # Setup Objective function
    objective_func = Objective(ObjectiveType.MIN, {"x_1":23, "x_2":-7})

    # Setup problem (P)
    problem = Problem(objective=objective_func, constraints=constraints, variables=x)

    # Setup Linear Programming Solver
    co_may_quan_he_tuyen_tinh = LPSolver(problem=problem, bland=True, verbose=True)
    co_may_quan_he_tuyen_tinh.solve()
