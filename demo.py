from backend.models import (
    Variable, VariableSign,
    Constraint, ConstraintType,
    Objective, ObjectiveType,
    Problem
)

from backend.cores import LPSolver, SolverMethod

def main():
    print("==================================================")
    print("   DEMO: Cỗ máy quan hệ tuyến tính    ")
    print("==================================================\n")
    # Giải
    # max z = 2x_1 + 3x_2
    # s.t: x_1 + 2x_2 <= 6
    #      2x_1 + x_2 <= 9
    #      x_2 <= 2
    #      x_1, x_2 >= 0
    
    x1 = Variable("x_1", VariableSign.NON_NEGATIVE)
    x2 = Variable("x_2", VariableSign.NON_NEGATIVE)
    
    constraints = [
        Constraint({"x_1": 1, "x_2": 2}, ConstraintType.LE, 6),
        Constraint({"x_1": 2, "x_2": 1}, ConstraintType.LE, 9),
        Constraint({"x_2": 1}, ConstraintType.LE, 2)
    ]
    
    objective_func = Objective(ObjectiveType.MAX, {"x_1": 2, "x_2": 3})
    problem = Problem(objective=objective_func, constraints=constraints, variables=[x1, x2])

    # ---------------------------------------------------------
    # TEST 1: Graphical method
    # ---------------------------------------------------------
    print(">>> TEST 1: GRAPHICAL")
    solver_graphical = LPSolver(problem, method=SolverMethod.GRAPHICAL, verbose=True)
    res_graphical = solver_graphical.solve()
    print(f"Status: {res_graphical['status']}")
    print(f"Solution: {res_graphical['solution']}")
    print(f"optimal value: {res_graphical['optimal_value']}\n")

    # ---------------------------------------------------------
    # TEST 2: SIMPLEX
    # ---------------------------------------------------------
    print(">>> TEST 2: SIMPLEX")
    solver_simplex = LPSolver(problem, method=SolverMethod.SIMPLEX, verbose=False)
    res_simplex = solver_simplex.solve()
    print(f"status: {res_simplex['status']}")
    print(f"solution: {res_simplex['solution']}")
    print(f"optimal value: {res_simplex['optimal_value']}\n")

    # ---------------------------------------------------------
    # TEST 3: AUTO Method (Priority Simplex)
    # ---------------------------------------------------------
    print(">>> TEST 3: AUTO")
    solver_auto = LPSolver(problem, method=SolverMethod.AUTO, verbose=True)
    res_auto = solver_auto.solve()
    
    print("\n--- AUTO RESULTS ---")
    print(f"Solution: {res_auto['solution']} | z = {res_auto['optimal_value']}")

if __name__ == "__main__":
    main()