import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from itertools import combinations
from fractions import Fraction

from backend.models import Problem, ConstraintType, VariableSign

class GraphicalSolver:
    """
    Graphical method to solve the original 2-variable Linear Programming problem.
    """
    def __init__(self, problem: Problem, verbose: bool = True):
        if len(problem.variables) != 2:
            raise ValueError("The graphical method is only applicable for problems with exactly 2 variables.")
        
        self.problem = problem
        self.verbose = verbose
        self.var1 = problem.variables[0]
        self.var2 = problem.variables[1]
        self.status = "INITIALIZED"

    def _get_line_equation(self, constraint) -> tuple:
        """Extract coefficients a1, a2 and constant b from a constraint"""
        a1 = constraint.coeffs.get(self.var1.name, 0.0)
        a2 = constraint.coeffs.get(self.var2.name, 0.0)
        return [a1, a2], constraint.right_hand_side

    def _get_all_intersections(self) -> list:
        lines_M = []
        lines_v = []
        
        # 1. Add lines from the constraint system
        for c in self.problem.constraints:
            M_row, v_val = self._get_line_equation(c)
            lines_M.append(M_row)
            lines_v.append(v_val)
            
        # 2. Add lines from the coordinate axes boundaries (based on variable signs)
        if self.var1.sign in [VariableSign.NON_NEGATIVE, VariableSign.NON_POSITIVE]:
            lines_M.append([1.0, 0.0]) # x1 = 0
            lines_v.append(0.0)
            
        if self.var2.sign in [VariableSign.NON_NEGATIVE, VariableSign.NON_POSITIVE]:
            lines_M.append([0.0, 1.0]) # x2 = 0
            lines_v.append(0.0)

        intersections = []
        # Solve the system of 2 equations for every pair of lines
        for (i, j) in combinations(range(len(lines_M)), 2):
            M_pair = np.array([lines_M[i], lines_M[j]])
            v_pair = np.array([lines_v[i], lines_v[j]])
            try:
                pt = np.linalg.solve(M_pair, v_pair)
                intersections.append(pt)
            except np.linalg.LinAlgError:
                # Skip parallel or coincident pairs of lines
                continue
                
        return intersections

    def _is_feasible(self, pt) -> bool:
        """Check if point pt(x1, x2) satisfies ALL constraints of the Problem"""
        x1_val, x2_val = pt[0], pt[1]

        # 1. Check variable signs
        if self.var1.sign == VariableSign.NON_NEGATIVE and x1_val < -1e-9: return False
        if self.var1.sign == VariableSign.NON_POSITIVE and x1_val > 1e-9: return False
        
        if self.var2.sign == VariableSign.NON_NEGATIVE and x2_val < -1e-9: return False
        if self.var2.sign == VariableSign.NON_POSITIVE and x2_val > 1e-9: return False

        # 2. Check the constraints
        for c in self.problem.constraints:
            a1 = c.coeffs.get(self.var1.name, 0.0)
            a2 = c.coeffs.get(self.var2.name, 0.0)
            val = a1 * x1_val + a2 * x2_val
            
            if c.constraint_type == ConstraintType.LE and val > c.right_hand_side + 1e-9: return False
            if c.constraint_type == ConstraintType.GE and val < c.right_hand_side - 1e-9: return False
            if c.constraint_type == ConstraintType.EQ and abs(val - c.right_hand_side) > 1e-9: return False
            
        return True

    def solve(self) -> dict:
        if self.verbose:
            print("--- Solving using Graphical Method ---")
        
        all_pts = self._get_all_intersections()
        
        feasible_pts = []
        for pt in all_pts:
            if self._is_feasible(pt):
                # Remove duplicate points (due to float precision errors)
                if not any(np.allclose(pt, f_pt, atol=1e-9) for f_pt in feasible_pts):
                    feasible_pts.append(pt)
                    
        if not feasible_pts:
            self.status = "INFEASIBLE"
            return {"status": self.status, "optimal_value": None, "solution": None}

        # Extract objective function coefficients
        c1 = self.problem.objective.coeffs.get(self.var1.name, 0.0)
        c2 = self.problem.objective.coeffs.get(self.var2.name, 0.0)
        is_max = (self.problem.objective.objective_type.value == "max")

        # Initialize the best value record
        best_val = float('-inf') if is_max else float('inf')
        best_pt = None
        
        if self.verbose:
            print("\n[Feasible region vertices and their corresponding z values]")
        for pt in feasible_pts:
            val = c1 * pt[0] + c2 * pt[1]
            if self.verbose:
                print(f"Vertex ({pt[0]:.2f}, {pt[1]:.2f}) -> z = {val:.2f}")
            
            if is_max and val > best_val:
                best_val, best_pt = val, pt
            elif not is_max and val < best_val:
                best_val, best_pt = val, pt

        self.status = "OPTIMAL"

        def to_frac_str(val):
            if abs(val) < 1e-9:
                return "0"
            return str(Fraction(val).limit_denominator(1000000))

        solution = {
            self.var1.name: to_frac_str(best_pt[0]),
            self.var2.name: to_frac_str(best_pt[1])
        }

        
        formatted_vertices = [(round(float(p[0]), 5), round(float(p[1]), 5)) for p in feasible_pts]

        return {
            "status": self.status,
            "optimal_value": to_frac_str(best_val),
            "solution": solution,
            "feasible_vertices": formatted_vertices
        }
    
    def plot_feasible_region(self, result: dict):
        """
        Plot the feasible polygon region and highlight the optimal solution.
        Call this method ONLY AFTER running the solve() method.
        """
        if result['status'] != "OPTIMAL":
            if self.verbose:
                print("\n[Plot Error] Cannot plot the graph because the problem is Infeasible or Unbounded.")
            return

        # 1. Get the list of feasible vertices
        # result['feasible_vertices'] contains tuples, we cast it to a numpy array for easier calculation
        pts = np.array(result['feasible_vertices'])
        
        # 2. Sort the vertices in counterclockwise order to prevent self-intersecting polygons
        # Calculate the centroid of the polygon
        centroid = np.mean(pts, axis=0)
        # Calculate the angle of each vertex relative to the centroid using arctan2
        angles = np.arctan2(pts[:, 1] - centroid[1], pts[:, 0] - centroid[0])
        # Sort the points array by increasing angle
        sorted_pts = pts[np.argsort(angles)]

        # 3. Initialize the plot
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # 4. Plot the feasible region (Light blue polygon)
        poly = Polygon(sorted_pts, closed=True, facecolor='lightblue', edgecolor='blue', alpha=0.5, linewidth=2)
        ax.add_patch(poly)

        # 5. Plot the vertices on the graph
        for pt in pts:
            ax.plot(pt[0], pt[1], 'ko') # Black dot
            # Add coordinate labels next to each vertex
            ax.text(pt[0] + 0.5, pt[1] + 0.5, f"({pt[0]:.1f}, {pt[1]:.1f})", fontsize=10, color='black')

        # 6. Highlight the Optimal Point
        opt_x = float(Fraction(result['solution'][self.var1.name]))
        opt_y = float(Fraction(result['solution'][self.var2.name]))
        
        ax.plot(opt_x, opt_y, 'ro', markersize=10, label=f"Optimal: z = {result['optimal_value']}")

        # 7. Decorate and format the coordinate axes
        ax.set_title("Graphical Method: Feasible Region & Optimal Point", fontsize=14, fontweight='bold')
        ax.set_xlabel(self.var1.name, fontsize=12)
        ax.set_ylabel(self.var2.name, fontsize=12)
        
        # Set axis limits (Add padding so the graph isn't right against the edge)
        max_x = max(pts[:, 0]) if len(pts) > 0 else 10
        max_y = max(pts[:, 1]) if len(pts) > 0 else 10
        ax.set_xlim(min(pts[:, 0]) - 5, max_x + 10)
        ax.set_ylim(min(pts[:, 1]) - 5, max_y + 10)
        
        # Show grid and the 2 main coordinate axes (x=0, y=0)
        ax.axhline(0, color='black', linewidth=1.5)
        ax.axvline(0, color='black', linewidth=1.5)
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.legend(loc="upper right", fontsize=12)

        # Render the plot
        plt.show()