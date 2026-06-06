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
        self.BIG_M = 1e6  # Thêm hộp giới hạn (Bounding Box) để bắt lỗi Unbounded

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

        # 3. Add Bounding Box limits (Giới hạn vùng vẽ để bắt Unbounded)
        lines_M.extend([[1.0, 0.0], [-1.0, 0.0], [0.0, 1.0], [0.0, -1.0]])
        lines_v.extend([self.BIG_M, self.BIG_M, self.BIG_M, self.BIG_M])

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

        if best_pt is not None and (abs(best_pt[0]) >= self.BIG_M - 1e-3 or abs(best_pt[1]) >= self.BIG_M - 1e-3):
            return {
                "status": "UNBOUNDED",
                "optimal_value": float('inf') if is_max else float('-inf'),
                "solution": None,
                "feasible_vertices": []
            }

        self.status = "OPTIMAL"

        def to_frac_str(val):
            if abs(val) < 1e-9:
                return "0"
            return str(Fraction(val).limit_denominator(1000000))

        solution = {
            self.var1.name: to_frac_str(best_pt[0]),
            self.var2.name: to_frac_str(best_pt[1])
        }
        
        formatted_vertices = [(round(float(p[0]), 5), round(float(p[1]), 5)) for p in feasible_pts if abs(p[0]) < self.BIG_M - 1e-3 and abs(p[1]) < self.BIG_M - 1e-3]

        return {
            "status": self.status,
            "optimal_value": to_frac_str(best_val),
            "solution": solution,
            "feasible_vertices": formatted_vertices
        }
    
    def plot_feasible_region(self, result: dict):
        if result['status'] != "OPTIMAL":
            if self.verbose:
                print("\n[Plot Error] Cannot plot the graph because the problem is Infeasible or Unbounded.")
            return None

        pts = np.array(result['feasible_vertices'])
        if len(pts) == 0:
            return None

        # Sắp xếp đỉnh ngược chiều kim đồng hồ
        centroid = np.mean(pts, axis=0)
        angles = np.arctan2(pts[:, 1] - centroid[1], pts[:, 0] - centroid[0])
        sorted_pts = pts[np.argsort(angles)]

        fig, ax = plt.subplots(figsize=(9, 7))

        min_x, max_x = min(pts[:, 0]), max(pts[:, 0])
        min_y, max_y = min(pts[:, 1]), max(pts[:, 1])
        pad_x = max((max_x - min_x) * 0.25, 3.0)
        pad_y = max((max_y - min_y) * 0.25, 3.0)

        x_lo, x_hi = min_x - pad_x, max_x + pad_x
        y_lo, y_hi = min_y - pad_y, max_y + pad_y

        x_range = np.linspace(x_lo, x_hi, 400)
        colors = plt.cm.tab10.colors

        for idx, c in enumerate(self.problem.constraints):
            a1 = c.coeffs.get(self.var1.name, 0.0)
            a2 = c.coeffs.get(self.var2.name, 0.0)
            b  = c.right_hand_side
            color = colors[idx % len(colors)]

            if abs(a2) > 1e-9:
                y_range = (b - a1 * x_range) / a2
                label = (
                    f"${a1:g}x_1 + {a2:g}x_2 {c.constraint_type.value} {b:g}$"
                    .replace("+ -", "- ")
                )
                ax.plot(x_range, y_range, color=color, linewidth=1.5,
                        linestyle='--', label=label)
            elif abs(a1) > 1e-9:
                x_val = b / a1
                ax.axvline(x_val, color=color, linewidth=1.5, linestyle='--',
                        label=f"$x_1 = {b/a1:g}$")

        poly = Polygon(sorted_pts, closed=True,
                    facecolor='lightblue', edgecolor='blue',
                    alpha=0.45, linewidth=2, zorder=2)
        ax.add_patch(poly)

        offset_x = (x_hi - x_lo) * 0.025
        offset_y = (y_hi - y_lo) * 0.025

        for pt in pts:
            ax.plot(pt[0], pt[1], 'ko', markersize=6, zorder=4)
            ax.text(pt[0] + offset_x, pt[1] + offset_y,
                    f"({pt[0]:.2f}, {pt[1]:.2f})",
                    fontsize=9, color='#222222', zorder=5)

        opt_x = float(Fraction(result['solution'][self.var1.name]))
        opt_y = float(Fraction(result['solution'][self.var2.name]))
        ax.plot(opt_x, opt_y, 'r*', markersize=14, zorder=6,
                label=f"Optimal: $z^* = {result['optimal_value']}$")

        ax.axhline(0, color='black', linewidth=1.2)
        ax.axvline(0, color='black', linewidth=1.2)
        ax.set_xlim(x_lo, x_hi)
        ax.set_ylim(y_lo, y_hi)
        ax.grid(True, linestyle='--', alpha=0.5)

        ax.set_title("Graphical Method: Feasible Region & Optimal Point",
                    fontsize=14, fontweight='bold')
        ax.set_xlabel(f"${self.var1.name}$", fontsize=12)
        ax.set_ylabel(f"${self.var2.name}$", fontsize=12)
        ax.legend(loc="upper right", fontsize=9, framealpha=0.9)

        fig.tight_layout()
        return fig