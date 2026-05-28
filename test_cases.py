import unittest

from backend.models import (
    Variable, VariableSign,
    Constraint, ConstraintType,
    Objective, ObjectiveType,
    Problem
)
from backend.cores import LPSolver

class TestLPOptimal(unittest.TestCase):
    def test_two_phases_min_problem(self):
        """
        Test bài toán cần sử dụng thuật toán 2 pha (do có b_i < 0)
        Problem (P): min 23x_1 - 7x_2
        Subject to:
             -2x_1 + x_2 <= -1
               x_1 + x_2 <= 5
              -x_1 - x_2 <= -2
               x_1, x_2 >= 0
        """
        x1 = Variable("x_1", VariableSign.NON_NEGATIVE)
        x2 = Variable("x_2", VariableSign.NON_NEGATIVE)
        x = [x1, x2]

        constraints = [
            Constraint({"x_1": -2, "x_2": 1}, ConstraintType.LE, -1),
            Constraint({"x_1": 1, "x_2": 1}, ConstraintType.LE, 5),
            Constraint({"x_1": -1, "x_2": -1}, ConstraintType.LE, -2),
        ]

        objective_func = Objective(ObjectiveType.MIN, {"x_1": 23, "x_2": -7})
        problem = Problem(objective=objective_func, constraints=constraints, variables=x)
        LP = LPSolver(problem=problem, bland=True, verbose=False)
        result = LP.solve()
        self.assertEqual(result["status"], "OPTIMAL", "Trạng thái bài toán phải là OPTIMAL")
        self.assertEqual(str(result["optimal_value"]), "16", "Giá trị tối ưu phải bằng 16")
        self.assertEqual(str(result["solution"]["x_1"]), "1", "Nghiệm x_1 phải bằng 1")
        self.assertEqual(str(result["solution"]["x_2"]), "1", "Nghiệm x_2 phải bằng 1")

class TestInfeasible(unittest.TestCase):
    def test_infeasible_problem(self):
        """
        Test bài toán vô nghiệm (INFEASIBLE).
        Problem: max x_1 + x_2
        Subject to:
             x_1 + x_2 <= 2
             x_1 + x_2 >= 4  (Mâu thuẫn với ràng buộc trên)
             x_1, x_2 >= 0
        """
        x1 = Variable("x_1", VariableSign.NON_NEGATIVE)
        x2 = Variable("x_2", VariableSign.NON_NEGATIVE)
        x = [x1, x2]

        constraints = [
            Constraint({"x_1": 1, "x_2": 1}, ConstraintType.LE, 2),
            Constraint({"x_1": 1, "x_2": 1}, ConstraintType.GE, 4),
        ]

        objective_func = Objective(ObjectiveType.MAX, {"x_1": 1, "x_2": 1})
        problem = Problem(objective=objective_func, constraints=constraints, variables=x)

        solver = LPSolver(problem=problem, bland=True, verbose=False)
        result = solver.solve()
        self.assertEqual(result["status"], "INFEASIBLE", "Bài toán chứa mâu thuẫn phải trả về INFEASIBLE")

class TestUnbounded(unittest.TestCase):
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
        x = [x1, x2]

        constraints = [
            Constraint({"x_1": 1, "x_2": -1}, ConstraintType.LE, 1),
            Constraint({"x_1": -1, "x_2": 1}, ConstraintType.LE, 1),
        ]

        objective_func = Objective(ObjectiveType.MAX, {"x_1": 1, "x_2": 1})
        problem = Problem(objective=objective_func, constraints=constraints, variables=x)
        solver = LPSolver(problem=problem, bland=True, verbose=False)
        result = solver.solve()
        self.assertEqual(result["status"], "UNBOUNDED", "Bài toán có miền nghiệm mở phải trả về UNBOUNDED")
        self.assertEqual(str(result["optimal_value"]), "inf", "Giá trị tối ưu của bài toán Max Unbounded phải là inf")

if __name__ == "__main__":
    unittest.main(exit=True)

"""
NOTE: Yêu cầu tester viết thêm các test cases để kiểm tra thêm các bài toán với các trường hợp đặc biệt.
"""