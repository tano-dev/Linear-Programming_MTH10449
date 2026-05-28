import unittest
from fractions import Fraction

from backend.models import (
    Variable, VariableSign,
    Constraint, ConstraintType,
    Objective, ObjectiveType,
    Problem
)
from backend.cores import LPSolver, SolverMethod

class TestLPOptimal(unittest.TestCase):
    
    def test_pure_simplex_max_problem(self):
        """
        Test thuật toán Đơn hình thuần túy (Pure Simplex).
        Không có hằng số âm, không cần biến giả.
        Problem: max 3x_1 + 5x_2
        Subject to:
             x_1 <= 4
             2x_2 <= 12
             3x_1 + 2x_2 <= 18
             x_1, x_2 >= 0
        Nghiệm tối ưu: x_1 = 2, x_2 = 6, z_max = 36
        """
        x1 = Variable("x_1", VariableSign.NON_NEGATIVE)
        x2 = Variable("x_2", VariableSign.NON_NEGATIVE)
        
        constraints = [
            Constraint({"x_1": 1}, ConstraintType.LE, 4),
            Constraint({"x_2": 2}, ConstraintType.LE, 12),
            Constraint({"x_1": 3, "x_2": 2}, ConstraintType.LE, 18),
        ]
        
        objective = Objective(ObjectiveType.MAX, {"x_1": 3, "x_2": 5})
        problem = Problem(objective=objective, constraints=constraints, variables=[x1, x2])
        
        solver = LPSolver(problem=problem, method=SolverMethod.SIMPLEX, bland=True, verbose=False)
        result = solver.solve()
        
        self.assertEqual(result["status"], "OPTIMAL")
        self.assertEqual(str(result["optimal_value"]), "36")
        self.assertEqual(str(result["solution"]["x_1"]), "2")
        self.assertEqual(str(result["solution"]["x_2"]), "6")

    def test_two_phases_min_problem(self):
        """
        Test bài toán cần sử dụng thuật toán 2 pha (do có b_i < 0)
        Problem (P): min 23x_1 - 7x_2
        Subject to:
             -2x_1 + x_2 <= -1
               x_1 + x_2 <= 5
              -x_1 - x_2 <= -2
               x_1, x_2 >= 0
        Nghiệm tối ưu: x_1 = 1, x_2 = 1, z_min = 16
        """
        x1 = Variable("x_1", VariableSign.NON_NEGATIVE)
        x2 = Variable("x_2", VariableSign.NON_NEGATIVE)

        constraints = [
            Constraint({"x_1": -2, "x_2": 1}, ConstraintType.LE, -1),
            Constraint({"x_1": 1, "x_2": 1}, ConstraintType.LE, 5),
            Constraint({"x_1": -1, "x_2": -1}, ConstraintType.LE, -2),
        ]

        objective = Objective(ObjectiveType.MIN, {"x_1": 23, "x_2": -7})
        problem = Problem(objective=objective, constraints=constraints, variables=[x1, x2])
        
        solver = LPSolver(problem=problem, method=SolverMethod.AUTO, bland=True, verbose=False)
        result = solver.solve()
        
        self.assertEqual(result["status"], "OPTIMAL")
        self.assertEqual(str(result["optimal_value"]), "16")
        self.assertEqual(str(result["solution"]["x_1"]), "1")
        self.assertEqual(str(result["solution"]["x_2"]), "1")

    def test_mixed_constraints_problem(self):
        """
        Test bài toán chứa hỗn hợp các dấu <=, >=, =
        Problem: min 4x_1 + x_2
        Subject to:
             3x_1 + x_2 = 3
             4x_1 + 3x_2 >= 6
             x_1 + 2x_2 <= 4
             x_1, x_2 >= 0
        Nghiệm tối ưu: x_1 = 3/5, x_2 = 6/5, z_min = 18/5
        """
        x1 = Variable("x_1", VariableSign.NON_NEGATIVE)
        x2 = Variable("x_2", VariableSign.NON_NEGATIVE)

        constraints = [
            Constraint({"x_1": 3, "x_2": 1}, ConstraintType.EQ, 3),
            Constraint({"x_1": 4, "x_2": 3}, ConstraintType.GE, 6),
            Constraint({"x_1": 1, "x_2": 2}, ConstraintType.LE, 4),
        ]

        objective = Objective(ObjectiveType.MIN, {"x_1": 4, "x_2": 1})
        problem = Problem(objective=objective, constraints=constraints, variables=[x1, x2])
        
        solver = LPSolver(problem=problem, method=SolverMethod.SIMPLEX, bland=True, verbose=False)
        result = solver.solve()
        
        self.assertEqual(result["status"], "OPTIMAL")
        self.assertEqual(result["optimal_value"], "17/5")
        self.assertEqual(result["solution"]["x_1"], "2/5")
        self.assertEqual(result["solution"]["x_2"], "9/5")

    def test_free_variable_problem(self):
        """
        Test hệ thống có xử lý đúng Biến Tự Do (Free Variable) không.
        (Biến tự do x_1 sẽ bị tách thành x_1_pos - x_1_neg)
        Problem: max x_1
        Subject to:
             x_1 <= 5
             x_1, tự do
        Nghiệm tối ưu: x_1 = 5, z_max = 5
        """
        x1 = Variable("x_1", VariableSign.FREE)
        
        constraints = [
            Constraint({"x_1": 1}, ConstraintType.LE, 5),
        ]
        
        objective = Objective(ObjectiveType.MAX, {"x_1": 1})
        problem = Problem(objective=objective, constraints=constraints, variables=[x1])
        
        solver = LPSolver(problem=problem, bland=True, verbose=False)
        result = solver.solve()
        
        self.assertEqual(result["status"], "OPTIMAL")
        self.assertEqual(str(result["optimal_value"]), "5")
        self.assertEqual(str(result["solution"]["x_1"]), "5")

    def test_graphical_routing(self):
        """
        Test bộ định tuyến Facade có gọi đúng phương pháp Hình học không.
        Sử dụng bài toán nội thất: max 3x1 + 2x2.
        Nghiệm: x1=30, x2=40, z=170
        """
        x1 = Variable("x_1", VariableSign.NON_NEGATIVE)
        x2 = Variable("x_2", VariableSign.NON_NEGATIVE)
        
        constraints = [
            Constraint({"x_1": 2, "x_2": 1}, ConstraintType.LE, 100),
            Constraint({"x_1": 1, "x_2": 1}, ConstraintType.LE, 80),
            Constraint({"x_2": 1}, ConstraintType.LE, 40)
        ]
        
        objective = Objective(ObjectiveType.MAX, {"x_1": 3, "x_2": 2})
        problem = Problem(objective=objective, constraints=constraints, variables=[x1, x2])
        
        # Ép dùng GRAPHICAL
        solver = LPSolver(problem=problem, method=SolverMethod.GRAPHICAL, verbose=False)
        result = solver.solve()
        
        self.assertEqual(result["status"], "OPTIMAL")
        self.assertEqual(str(result["optimal_value"]), "170")
        self.assertIn("feasible_vertices", result, "Phương pháp hình học phải trả về mảng feasible_vertices")


class TestExceptions(unittest.TestCase):
    
    def test_infeasible_problem(self):
        """
        Test bài toán vô nghiệm (INFEASIBLE).
        Problem: max x_1 + x_2
        Subject to:
             x_1 + x_2 <= 2
             x_1 + x_2 >= 4  (Mâu thuẫn)
             x_1, x_2 >= 0
        """
        x1 = Variable("x_1", VariableSign.NON_NEGATIVE)
        x2 = Variable("x_2", VariableSign.NON_NEGATIVE)
        
        constraints = [
            Constraint({"x_1": 1, "x_2": 1}, ConstraintType.LE, 2),
            Constraint({"x_1": 1, "x_2": 1}, ConstraintType.GE, 4),
        ]
        
        objective = Objective(ObjectiveType.MAX, {"x_1": 1, "x_2": 1})
        problem = Problem(objective=objective, constraints=constraints, variables=[x1, x2])
        
        solver = LPSolver(problem=problem, bland=True, verbose=False)
        result = solver.solve()
        
        self.assertEqual(result["status"], "INFEASIBLE")

    def test_unbounded_problem(self):
        """
        Test bài toán không giới nội (UNBOUNDED).
        Problem: max x_1 + x_2
        Subject to:
              x_1 - x_2 <= 1
             -x_1 + x_2 <= 1
              x_1, x_2 >= 0
        """
        x1 = Variable("x_1", VariableSign.NON_NEGATIVE)
        x2 = Variable("x_2", VariableSign.NON_NEGATIVE)
        
        constraints = [
            Constraint({"x_1": 1, "x_2": -1}, ConstraintType.LE, 1),
            Constraint({"x_1": -1, "x_2": 1}, ConstraintType.LE, 1),
        ]
        
        objective = Objective(ObjectiveType.MAX, {"x_1": 1, "x_2": 1})
        problem = Problem(objective=objective, constraints=constraints, variables=[x1, x2])
        
        solver = LPSolver(problem=problem, bland=True, verbose=False)
        result = solver.solve()
        
        self.assertEqual(result["status"], "UNBOUNDED")
        self.assertEqual(str(result["optimal_value"]), "inf")

if __name__ == "__main__":
    unittest.main(exit=True)

"""
NOTE: Yêu cầu tester viết thêm các test cases để kiểm tra thêm các bài toán với các trường hợp đặc biệt.
"""