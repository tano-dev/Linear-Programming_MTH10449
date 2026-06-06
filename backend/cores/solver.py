from enum import Enum

from backend.cores import Standardizer, GraphicalSolver, Simplex, TwoPhases
from backend.models import Problem, StandardProblem

class SolverMethod(Enum):
    """
    DEFINE METHODS solving Linear Programming which are supported by system
    """
    AUTO = "auto"
    SIMPLEX = "simplex"
    GRAPHICAL = "graphical"

class LPSolver:
    """
    The Linear Programming Solver
    """
    def __init__(self, problem: Problem, method: SolverMethod = SolverMethod.AUTO, bland: bool = False, verbose = True):
        """
        :param problem: Original optimazation problem (Problem object)
        :param method: Solving method (SolverMethod.AUTO, SolverMethod.SIMPLEX, SolverMethod.GRAPHICAL)
        :param bland: Enable Bland's rule to prevent degeneracy (cycling) = True and otherwise
        :param verbose: Enable printing tableau logs to the terminal = True
        """
        self.problem = problem
        self.method = method
        self.bland = bland
        self.verbose = verbose

    def solve(self) -> dict:
        if self.verbose:
            print(f"\n[LPSolver] Problem received. Solving mode: {self.method.name}")
            print(f"Original problem")
            print(self.problem)

        # Graphical Method
        if self.method == SolverMethod.GRAPHICAL:
            if len(self.problem.variables) != 2:
                raise ValueError("The Graphical Method is only applicable to linear programming problems with exactly two variables.")
            
            if self.verbose:
                print(f"[Graphical Solver]")

            graphical_solver = GraphicalSolver(self.problem, verbose=self.verbose)
            results = graphical_solver.solve()
            if self.verbose:
                graphical_solver.plot_feasible_region(results)
            return results
        
        elif self.method in [SolverMethod.AUTO, SolverMethod.SIMPLEX]:
            if self.verbose:
                print(f"[Standardizer]")
                print("Normalize the original problem")

            standardizer = Standardizer()
            standard_problem: StandardProblem = standardizer(self.problem)

            if self.verbose:
                print("The standard problem")
                standard_problem.show()

            if standard_problem.need_two_phases:
                if self.verbose:
                    print("[Two Phase Solver] Detected b_i < 0, routing to Two-Phase Solver")
                solver = TwoPhases(problem=standard_problem, bland=self.bland, verbose=self.verbose)

            else:
                if self.verbose:
                    print("[Pure Simplex] Standard form detected. Routing to Pure Simplex Solver")
                solver = Simplex(problem=standard_problem, bland=self.bland, verbose=self.verbose)
            return solver.solve()
        
        else:
            raise ValueError("Invalid solving method. Please use the SolverMethod")