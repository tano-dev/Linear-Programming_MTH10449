from backend.cores import Standardizer, TwoPhases
from backend.models import Problem, CanonicalProblem

class LPSolver:
    def __init__(self, problem: Problem, bland=False, verbose: bool = True):
        self.problem = problem
        self.standardizer = Standardizer()
        self.bland = bland
        self.verbose = verbose
        self.results = {}
    
    def solve(self) -> dict:
        canonical_probem: CanonicalProblem = self.standardizer(self.problem)

        if self.verbose:
            print("The information of the problem:\n")
            print(self.problem)
            print("The canonical problem:\n")
            canonical_probem.show()
            
        solver = TwoPhases(problem=canonical_probem, bland=self.bland, verbose=self.verbose)
        result = solver.solve()

        if self.verbose:
            print("=== FINAL RESULTS ===")
            print(f"STATUS: {result['status']}")
        
            if result["status"] == "OPTIMAL":
                print(f"optimal value (z): {result['optimal_value']}")
                print("Solution:")
                for var, val in result["solution"].items():
                    print(f"  {var} = {val}")

        self.results.update(result)
        return self.results