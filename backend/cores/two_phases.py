import numpy as np
from fractions import Fraction

from backend.models import StandardProblem
from backend.cores import SimplexCyclingError

class TwoPhases:
    """
    Two - phases algorithm
    """
    def __init__(self, problem: StandardProblem, bland: bool = False, verbose: bool=True):
        if not problem.need_two_phases:
            raise ValueError("This problem does not need Two - Phases algorithm. Please try to use another algorithm")
        self.problem = problem
        self.num_variables = len(problem.variable_names)
        self.num_constraints = len(problem.b)
        self.bland = bland
        self.verbose = verbose
        self.status = "INITIALIZED"

        self.M = np.zeros((self.num_constraints + 2, self.num_variables + 2))
        if self.num_constraints > 0:
            self.M[:self.num_constraints, 0] = problem.b
            self.M[:self.num_constraints, 1:self.num_variables+1] = -np.array(problem.A)
            self.M[:self.num_constraints, -1] = 1.0
        self.M[self.num_constraints, self.num_variables+1] = 1.0 
        self.M[self.num_constraints+1, 1:self.num_variables+1] = problem.c

        self.non_basic_vars = problem.variable_names + ["x_0"]
        self.basic_vars = [f"w_{i+1}" for i in range(self.num_constraints)]

    def find_entering_variable(self, obj_row_idx: int) -> int:
        obj_row = self.M[obj_row_idx, 1:]
        
        if self.bland:
            neg_indices = np.where(obj_row < -1e-9)[0]
            if len(neg_indices) == 0:
                return -1
            return neg_indices[0] + 1
        
        if np.min(obj_row) >= -1e-9:
            return -1
        return np.argmin(obj_row) + 1
    
    def find_leaving_variable(self, c_in: int) -> int:
        rows = []
        for i in range(self.num_constraints):
            a_ij = self.M[i, c_in]
            b_i = self.M[i, 0]
            if a_ij < -1e-9:
                ratio = b_i / abs(a_ij)
                rows.append((ratio, i))
                
        if not rows:
            return -1
            
        _, idx = min(rows, key=lambda x: (x[0], x[1])) 
        return idx

    def pivot(self, r_out: int, c_in: int):
        """
        Turning Simplex Dictionary
        """
        p = self.M[r_out, c_in]
        
        new_row = self.M[r_out, :] / (-p)
        new_row[c_in] = 1.0 / p

        multipliers = self.M[:, c_in].copy()
        self.M += np.outer(multipliers, new_row)
        self.M[:, c_in] = multipliers * new_row[c_in]
        self.M[r_out, :] = new_row
        
        entering_var = self.non_basic_vars[c_in - 1]
        leaving_var = self.basic_vars[r_out]

        self.basic_vars[r_out] = entering_var
        self.non_basic_vars[c_in - 1] = leaving_var

    def print_dictionary(self, phase_name: str):
        """
        Print dictionary to terminal
        """
        obj_name = "xi" if phase_name == "Phase 1" else "z"
        
        obj_val = self.M[self.num_constraints, 0]
        
        if abs(obj_val) > 1e-9:
            frac_obj_val = Fraction(obj_val).limit_denominator(1000000)
            obj_str = f"{obj_name:<4} = {frac_obj_val}"
        else:
            obj_str = f"{obj_name:<4} ="
        
        for j, nb_var in enumerate(self.non_basic_vars):
            coeff = self.M[self.num_constraints, j+1]
            if abs(coeff) > 1e-9:
                sign = '+' if coeff > 0 else '-'
                val = abs(coeff)
                frac_val = Fraction(val).limit_denominator(1000000)
                
                coeff_str = "" if frac_val == 1 else f"{frac_val}"
                obj_str += f"  {sign} {coeff_str}{nb_var}"
                
        print(obj_str)
        print("-" * max(30, len(obj_str)))
        
        for i, b_var in enumerate(self.basic_vars):
            rhs = self.M[i, 0]
            if abs(rhs) > 1e-9:
                frac_rhs = Fraction(rhs).limit_denominator(1000000)
                eq_str = f"{b_var:<4} = {frac_rhs}"
            else:
                eq_str = f"{b_var:<4} ="
                
            for j, nb_var in enumerate(self.non_basic_vars):
                coeff = self.M[i, j+1]
                if abs(coeff) > 1e-9:
                    sign = '+' if coeff > 0 else '-'
                    val = abs(coeff)
                    frac_val = Fraction(val).limit_denominator(1000000)
                    
                    coeff_str = "" if frac_val == 1 else f"{frac_val}"
                    eq_str += f"  {sign} {coeff_str}{nb_var}"
            print(eq_str)
        print("\n")

    def has_multiple_optima(self):
        obj_row = self.M[self.num_constraints, 1:]

        for j in range(len(self.non_basic_vars)):

            if abs(obj_row[j]) > 1e-9:
                continue

            ratios = []

            for i in range(self.num_constraints):
                a = self.M[i, j + 1]

                if a < -1e-9:
                    ratios.append(
                        self.M[i, 0] / abs(a)
                    )

            if ratios and min(ratios) > 1e-9:
                return True

        return False

    def _run_simplex(self, obj_row: int, phase_name : str, max_iter: int = 1000):
        iter = 0
        while True:
            if iter > max_iter:
                raise SimplexCyclingError("Thuật toán bị lặp vòng vô tận do bài toán suy biến")
            c_in = self.find_entering_variable(obj_row)
            if c_in == -1:
                return "OPTIMAL"
            
            r_out = self.find_leaving_variable(c_in)
            if r_out == -1:
                return "UNBOUNDED"
            
            self.pivot(r_out=r_out, c_in=c_in)
            if self.verbose:
                self.print_dictionary(phase_name)
            iter += 1

    def solve(self) -> dict:
        if self.verbose:
            print(f"---INITIAL STATUS: {self.status}---")
            print(f"---Phase 1: Solving the support problem---")
            self.print_dictionary("Phase 1")

        r_out = np.argmin(self.M[:self.num_constraints, 0])
        c_in = self.num_variables + 1
        self.pivot(r_out, c_in)

        if self.verbose:
            print(">> After add x_0 to basis variables")
            self.print_dictionary("Phase 1")
        
        self.status = self._run_simplex(obj_row=self.num_constraints, phase_name="Phase 1")

        if abs(self.M[self.num_constraints, 0]) > 1e-9:
            return {"status": "INFEASIBLE"}

        if self.status == "UNBOUNDED":
            return {"status": "UNBOUNDED", "optimal_value": float("inf") if self.problem.is_from_max else float("-inf")}
        
        if self.M[self.num_constraints, 0] > 1e-9:
            return {"status": "INFEASIBLE"}
        
        if "x_0" in self.basic_vars:
            r_x0 = self.basic_vars.index("x_0")
            pivoted = False
            for j in range(1, self.M.shape[1]):
                if abs(self.M[r_x0, j]) > 1e-9:
                    self.pivot(r_x0, j)
                    if self.verbose:
                        self.print_dictionary("Phase 1")
                    pivoted = True
                    break
            
            if not pivoted:
                self.M = np.delete(self.M, r_x0, axis=0)
                self.basic_vars.pop(r_x0)
                self.num_constraints -= 1

        if "x_0" in self.non_basic_vars:
            col_to_delete = self.non_basic_vars.index("x_0") + 1
            self.M = np.delete(self.M, col_to_delete, axis=1)
            self.non_basic_vars.remove("x_0")

        self.M = np.delete(self.M, self.num_constraints, axis=0)
        
        if self.verbose:
            print("---Phase 2: Simplex---")
            self.print_dictionary("Phase 2")
            
        self.status = self._run_simplex(obj_row=self.num_constraints, phase_name="Phase 2")
    
        if self.status == "UNBOUNDED":
            return {"status": "UNBOUNDED", "optimal_value": float("inf") if self.problem.is_from_max else float("-inf")}

        result = self._extract_solution()

        if self.status == "OPTIMAL":
            if self.has_multiple_optima():
                result["has_multiple_optimal"] = True
                if self.verbose:
                    print('Multiple Optimal Solutions')

        return result
    
    def _extract_solution(self):
        std_solution = {}
        for var in self.problem.variable_names:
            if var in self.basic_vars:
                idx = self.basic_vars.index(var)
                std_solution[var] = self.M[idx, 0]
            else:
                std_solution[var] = 0.0
                
        original_solution = {}
        for var, val in std_solution.items():
            if var.endswith("_pos"):
                orig_var = var[:-4]
                original_solution[orig_var] = original_solution.get(orig_var, 0.0) + val
            
            elif var.endswith("_neg"):
                orig_var = var[:-4]
                original_solution[orig_var] = original_solution.get(orig_var, 0.0) - val
                
            elif var.endswith("_prime"):
                orig_var = var[:-6]
                original_solution[orig_var] = -val
                
            else:
                original_solution[var] = val

        opt_val = self.M[self.num_constraints, 0]
        if self.problem.is_from_max:
            opt_val = -opt_val

        def to_frac_str(val):
            if abs(val) < 1e-9:
                return "0"
            return str(Fraction(val).limit_denominator(1000000))

        return {
            "status": self.status,
            "optimal_value": to_frac_str(opt_val),
            "solution": {k: to_frac_str(v) for k, v in original_solution.items()}
        }