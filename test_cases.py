import unittest

from backend.models import (
    Variable,
    VariableSign,
    Constraint,
    ConstraintType,
    Objective,
    ObjectiveType,
    Problem,
)

from backend.cores import (
    LPSolver,
    SolverMethod
)


class TestOptimalProblems(unittest.TestCase):

    def test_pure_simplex_max_problem(self):
        """
        max 3x1 + 5x2
        x1 <= 4
        2x2 <= 12
        3x1 + 2x2 <= 18
        """
        x1 = Variable("x_1", VariableSign.NON_NEGATIVE)
        x2 = Variable("x_2", VariableSign.NON_NEGATIVE)

        constraints = [
            Constraint({"x_1": 1}, ConstraintType.LE, 4),
            Constraint({"x_2": 2}, ConstraintType.LE, 12),
            Constraint({"x_1": 3, "x_2": 2}, ConstraintType.LE, 18),
        ]

        objective = Objective(
            ObjectiveType.MAX,
            {"x_1": 3, "x_2": 5}
        )

        problem = Problem(
            objective=objective,
            constraints=constraints,
            variables=[x1, x2]
        )

        result = LPSolver(
            problem=problem,
            method=SolverMethod.SIMPLEX,
            bland=True,
            verbose=False
        ).solve()

        self.assertEqual(result["status"], "OPTIMAL")
        self.assertEqual(result["optimal_value"], "36")
        self.assertEqual(result["solution"]["x_1"], "2")
        self.assertEqual(result["solution"]["x_2"], "6")

    def test_two_phase_problem(self):
        """
        min 23x1 - 7x2
        """
        x1 = Variable("x_1", VariableSign.NON_NEGATIVE)
        x2 = Variable("x_2", VariableSign.NON_NEGATIVE)

        constraints = [
            Constraint({"x_1": -2, "x_2": 1}, ConstraintType.LE, -1),
            Constraint({"x_1": 1, "x_2": 1}, ConstraintType.LE, 5),
            Constraint({"x_1": -1, "x_2": -1}, ConstraintType.LE, -2),
        ]

        objective = Objective(
            ObjectiveType.MIN,
            {"x_1": 23, "x_2": -7}
        )

        problem = Problem(
            objective=objective,
            constraints=constraints,
            variables=[x1, x2]
        )

        result = LPSolver(
            problem=problem,
            bland=True,
            verbose=False
        ).solve()

        self.assertEqual(result["status"], "OPTIMAL")
        self.assertEqual(result["optimal_value"], "16")
        self.assertEqual(result["solution"]["x_1"], "1")
        self.assertEqual(result["solution"]["x_2"], "1")

    def test_mixed_constraints(self):
        x1 = Variable("x_1", VariableSign.NON_NEGATIVE)
        x2 = Variable("x_2", VariableSign.NON_NEGATIVE)

        constraints = [
            Constraint({"x_1": 3, "x_2": 1}, ConstraintType.EQ, 3),
            Constraint({"x_1": 4, "x_2": 3}, ConstraintType.GE, 6),
            Constraint({"x_1": 1, "x_2": 2}, ConstraintType.LE, 4),
        ]

        objective = Objective(
            ObjectiveType.MIN,
            {"x_1": 4, "x_2": 1}
        )

        problem = Problem(
            objective=objective,
            constraints=constraints,
            variables=[x1, x2]
        )

        result = LPSolver(
            problem=problem,
            bland=True,
            verbose=False
        ).solve()

        self.assertEqual(result["status"], "OPTIMAL")
        self.assertEqual(result["optimal_value"], "17/5")
        self.assertEqual(result["solution"]["x_1"], "2/5")
        self.assertEqual(result["solution"]["x_2"], "9/5")

    def test_free_variable(self):
        x1 = Variable("x_1", VariableSign.FREE)
        constraints = [
            Constraint({"x_1": 1}, ConstraintType.LE, 5)
        ]
        objective = Objective(ObjectiveType.MAX, {"x_1": 1})
        problem = Problem(objective=objective, constraints=constraints, variables=[x1])

        result = LPSolver(problem=problem, verbose=False).solve()

        self.assertEqual(result["status"], "OPTIMAL")
        self.assertEqual(result["optimal_value"], "5")
        self.assertEqual(result["solution"]["x_1"], "5")

    def test_non_positive_variable(self):
        x1 = Variable("x_1", VariableSign.NON_POSITIVE)
        constraints = [
            Constraint({"x_1": 1}, ConstraintType.LE, -2)
        ]
        objective = Objective(ObjectiveType.MAX, {"x_1": 1})
        problem = Problem(objective=objective, constraints=constraints, variables=[x1])

        result = LPSolver(problem=problem, verbose=False).solve()

        self.assertEqual(result["status"], "OPTIMAL")
        self.assertEqual(result["solution"]["x_1"], "-2")

    def test_graphical_solver(self):
        x1 = Variable("x_1", VariableSign.NON_NEGATIVE)
        x2 = Variable("x_2", VariableSign.NON_NEGATIVE)

        constraints = [
            Constraint({"x_1": 2, "x_2": 1}, ConstraintType.LE, 100),
            Constraint({"x_1": 1, "x_2": 1}, ConstraintType.LE, 80),
            Constraint({"x_2": 1}, ConstraintType.LE, 40),
        ]
        objective = Objective(ObjectiveType.MAX, {"x_1": 3, "x_2": 2})
        problem = Problem(objective=objective, constraints=constraints, variables=[x1, x2])

        result = LPSolver(problem=problem, method=SolverMethod.GRAPHICAL, verbose=False).solve()

        self.assertEqual(result["status"], "OPTIMAL")
        self.assertEqual(result["optimal_value"], "170")

    def test_graphical_solver_unbounded(self):
        """
        Kiểm tra tính năng Bounding Box của Graphical Solver
        max x1 + x2
        s.t: x1 >= 0, x2 >= 0
        """
        x1 = Variable("x_1", VariableSign.NON_NEGATIVE)
        x2 = Variable("x_2", VariableSign.NON_NEGATIVE)

        # Bài toán chỉ có đúng 1 điều kiện không giới hạn miền
        constraints = [
            Constraint({"x_1": -1, "x_2": 1}, ConstraintType.GE, -5), 
        ]
        objective = Objective(ObjectiveType.MAX, {"x_1": 1, "x_2": 1})
        problem = Problem(objective=objective, constraints=constraints, variables=[x1, x2])

        result = LPSolver(problem=problem, method=SolverMethod.GRAPHICAL, verbose=False).solve()

        self.assertEqual(result["status"], "UNBOUNDED")
        self.assertIsNone(result.get("solution"))


class TestSpecialCases(unittest.TestCase):

    def test_infeasible(self):
        x1 = Variable("x_1", VariableSign.NON_NEGATIVE)
        x2 = Variable("x_2", VariableSign.NON_NEGATIVE)

        constraints = [
            Constraint({"x_1": 1, "x_2": 1}, ConstraintType.LE, 2),
            Constraint({"x_1": 1, "x_2": 1}, ConstraintType.GE, 4),
        ]
        objective = Objective(ObjectiveType.MAX, {"x_1": 1, "x_2": 1})
        problem = Problem(objective=objective, constraints=constraints, variables=[x1, x2])

        result = LPSolver(problem=problem, verbose=False).solve()

        self.assertEqual(result["status"], "INFEASIBLE")

    def test_unbounded(self):
        x1 = Variable("x_1", VariableSign.NON_NEGATIVE)
        x2 = Variable("x_2", VariableSign.NON_NEGATIVE)

        constraints = [
            Constraint({"x_1": 1, "x_2": -1}, ConstraintType.LE, 1),
            Constraint({"x_1": -1, "x_2": 1}, ConstraintType.LE, 1),
        ]
        objective = Objective(ObjectiveType.MAX, {"x_1": 1, "x_2": 1})
        problem = Problem(objective=objective, constraints=constraints, variables=[x1, x2])

        result = LPSolver(problem=problem, verbose=False).solve()

        self.assertEqual(result["status"], "UNBOUNDED")

    def test_multiple_optima(self):
        x1 = Variable("x_1", VariableSign.NON_NEGATIVE)
        x2 = Variable("x_2", VariableSign.NON_NEGATIVE)

        constraints = [
            Constraint({"x_1": 1, "x_2": 1}, ConstraintType.LE, 1)
        ]
        objective = Objective(ObjectiveType.MAX, {"x_1": 1, "x_2": 1})
        problem = Problem(objective=objective, constraints=constraints, variables=[x1, x2])

        result = LPSolver(problem=problem, verbose=False).solve()

        self.assertEqual(result["status"], "OPTIMAL")
        self.assertTrue(result.get("has_multiple_optimal", False))
        self.assertEqual(result["optimal_value"], "1")

    def test_zero_objective(self):
        x1 = Variable("x_1", VariableSign.NON_NEGATIVE)

        constraints = [
            Constraint({"x_1": 1}, ConstraintType.LE, 5)
        ]
        objective = Objective(ObjectiveType.MAX, {"x_1": 0})
        problem = Problem(objective=objective, constraints=constraints, variables=[x1])

        result = LPSolver(problem=problem, verbose=False).solve()

        self.assertEqual(result["status"], "OPTIMAL")
        self.assertTrue(result.get("has_multiple_optimal", False))
        self.assertEqual(result["optimal_value"], "0")

    def test_redundant_constraints(self):
        x1 = Variable("x_1", VariableSign.NON_NEGATIVE)
        x2 = Variable("x_2", VariableSign.NON_NEGATIVE)

        constraints = [
            Constraint({"x_1": 1, "x_2": 1}, ConstraintType.LE, 5),
            Constraint({"x_1": 2, "x_2": 2}, ConstraintType.LE, 10),
        ]
        objective = Objective(ObjectiveType.MAX, {"x_1": 1, "x_2": 1})
        problem = Problem(objective=objective, constraints=constraints, variables=[x1, x2])

        result = LPSolver(problem=problem, verbose=False).solve()

        self.assertEqual(result["status"], "OPTIMAL")
        self.assertTrue(result.get("has_multiple_optimal", False))
        self.assertEqual(result["optimal_value"], "5")

    def test_no_constraints_unbounded(self):
        x1 = Variable("x_1", VariableSign.NON_NEGATIVE)
        objective = Objective(ObjectiveType.MAX, {"x_1": 1})
        problem = Problem(objective=objective, constraints=[], variables=[x1])

        result = LPSolver(problem=problem, verbose=False).solve()

        self.assertEqual(result["status"], "UNBOUNDED")

    def test_degeneracy_cycling_beale(self):
        """
        Bài toán của Beale: Nếu không có luật Bland (hoặc cài sai luật), 
        hệ thống sẽ bị Infinite Loop (Lặp vòng vô tận).
        max 0.75x1 - 20x2 + 0.5x3 - 6x4
        s.t.
        0.25x1 - 8x2 - 1x3 + 9x4 <= 0
        0.5x1 - 12x2 - 0.5x3 + 3x4 <= 0
        x3 <= 1
        x >= 0
        """
        x1 = Variable("x_1", VariableSign.NON_NEGATIVE)
        x2 = Variable("x_2", VariableSign.NON_NEGATIVE)
        x3 = Variable("x_3", VariableSign.NON_NEGATIVE)
        x4 = Variable("x_4", VariableSign.NON_NEGATIVE)

        constraints = [
            Constraint({"x_1": 0.25, "x_2": -8, "x_3": -1, "x_4": 9}, ConstraintType.LE, 0),
            Constraint({"x_1": 0.5, "x_2": -12, "x_3": -0.5, "x_4": 3}, ConstraintType.LE, 0),
            Constraint({"x_3": 1}, ConstraintType.LE, 1),
        ]

        objective = Objective(
            ObjectiveType.MAX,
            {"x_1": 0.75, "x_2": -20, "x_3": 0.5, "x_4": -6}
        )

        problem = Problem(objective, constraints, [x1, x2, x3, x4])

        # Bật bland=True, nếu Luật Bland cài sai code sẽ kẹt ở đây mãi mãi
        result = LPSolver(problem=problem, method=SolverMethod.SIMPLEX, bland=True, verbose=False).solve()

        self.assertEqual(result["status"], "OPTIMAL")
        self.assertEqual(result["optimal_value"], "5/4") 
        self.assertEqual(result["solution"]["x_1"], "1")
        self.assertEqual(result["solution"]["x_3"], "1")

class TestMultipleOptimalDetection(unittest.TestCase):

    def test_case_1_equality_ge_multiple(self):
        """
        min x1 + x2

        x1 - x2 = 1
        x1 + x2 >= 2

        => vô số nghiệm tối ưu
        """
        x1 = Variable("x_1", VariableSign.NON_NEGATIVE)
        x2 = Variable("x_2", VariableSign.NON_NEGATIVE)

        constraints = [
            Constraint({"x_1": 1, "x_2": -1}, ConstraintType.EQ, 1),
            Constraint({"x_1": 1, "x_2": 1}, ConstraintType.GE, 2),
        ]

        objective = Objective(
            ObjectiveType.MIN,
            {"x_1": 1, "x_2": 1}
        )

        problem = Problem(objective, constraints, [x1, x2])

        result = LPSolver(problem=problem, verbose=False).solve()

        self.assertEqual(result["status"], "OPTIMAL")
        self.assertEqual(result["optimal_value"], "2")
        self.assertFalse(result.get("has_multiple_optimal", False))

    def test_case_2_unique_origin(self):
        """
        min x1+x2
        x1+x2<=4

        => nghiệm duy nhất (0,0)
        """
        x1 = Variable("x_1", VariableSign.NON_NEGATIVE)
        x2 = Variable("x_2", VariableSign.NON_NEGATIVE)

        constraints = [
            Constraint({"x_1": 1, "x_2": 1}, ConstraintType.LE, 4)
        ]

        objective = Objective(
            ObjectiveType.MIN,
            {"x_1": 1, "x_2": 1}
        )

        problem = Problem(objective, constraints, [x1, x2])

        result = LPSolver(problem=problem, verbose=False).solve()

        self.assertEqual(result["status"], "OPTIMAL")
        self.assertFalse(result.get("has_multiple_optimal", False))

    def test_case_3_max_multiple(self):
        """
        max x1+x2

        x1+x2<=4
        x1<=4
        x2<=4

        => vô số nghiệm tối ưu
        """
        x1 = Variable("x_1", VariableSign.NON_NEGATIVE)
        x2 = Variable("x_2", VariableSign.NON_NEGATIVE)

        constraints = [
            Constraint({"x_1": 1, "x_2": 1}, ConstraintType.LE, 4),
            Constraint({"x_1": 1}, ConstraintType.LE, 4),
            Constraint({"x_2": 1}, ConstraintType.LE, 4),
        ]

        objective = Objective(
            ObjectiveType.MAX,
            {"x_1": 1, "x_2": 1}
        )

        problem = Problem(objective, constraints, [x1, x2])

        result = LPSolver(problem=problem, verbose=False).solve()

        self.assertEqual(result["status"], "OPTIMAL")
        self.assertEqual(result["optimal_value"], "4")
        self.assertTrue(result.get("has_multiple_optimal", False))

    def test_case_4_edge_multiple(self):
        """
        max x1+x2

        x1<=2
        x2<=2
        x1+x2<=2

        => vô số nghiệm tối ưu
        """
        x1 = Variable("x_1", VariableSign.NON_NEGATIVE)
        x2 = Variable("x_2", VariableSign.NON_NEGATIVE)

        constraints = [
            Constraint({"x_1": 1}, ConstraintType.LE, 2),
            Constraint({"x_2": 1}, ConstraintType.LE, 2),
            Constraint({"x_1": 1, "x_2": 1}, ConstraintType.LE, 2),
        ]

        objective = Objective(
            ObjectiveType.MAX,
            {"x_1": 1, "x_2": 1}
        )

        problem = Problem(objective, constraints, [x1, x2])

        result = LPSolver(problem=problem, verbose=False).solve()

        self.assertEqual(result["status"], "OPTIMAL")
        self.assertEqual(result["optimal_value"], "2")
        self.assertTrue(result.get("has_multiple_optimal", False))

    def test_case_5_infeasible(self):
        """
        vô nghiệm
        """
        x1 = Variable("x_1", VariableSign.NON_NEGATIVE)

        constraints = [
            Constraint({"x_1": 1}, ConstraintType.LE, 1),
            Constraint({"x_1": 1}, ConstraintType.GE, 2),
        ]

        objective = Objective(
            ObjectiveType.MIN,
            {"x_1": 1}
        )

        problem = Problem(objective, constraints, [x1])

        result = LPSolver(problem=problem, verbose=False).solve()

        self.assertEqual(result["status"], "INFEASIBLE")

    def test_case_6_unbounded(self):
        """
        max x1
        x1 >= 0

        => không giới nội
        """
        x1 = Variable("x_1", VariableSign.NON_NEGATIVE)

        objective = Objective(
            ObjectiveType.MAX,
            {"x_1": 1}
        )

        problem = Problem(objective, [], [x1])

        result = LPSolver(problem=problem, verbose=False).solve()

        self.assertEqual(result["status"], "UNBOUNDED")

    def test_case_7_single_point(self):
        """
        x1 = 0
        x2 = 0

        => chỉ có 1 nghiệm tối ưu
        """
        x1 = Variable("x_1", VariableSign.FREE)
        x2 = Variable("x_2", VariableSign.FREE)

        constraints = [
            Constraint({"x_1": 1}, ConstraintType.EQ, 0),
            Constraint({"x_2": 1}, ConstraintType.EQ, 0),
        ]

        objective = Objective(
            ObjectiveType.MIN,
            {"x_1": 1, "x_2": 1}
        )

        problem = Problem(objective, constraints, [x1, x2])

        result = LPSolver(problem=problem, verbose=False).solve()

        self.assertEqual(result["status"], "OPTIMAL")
        self.assertEqual(result["optimal_value"], "0")
        self.assertFalse(result.get("has_multiple_optimal", False))

    def test_case_8_ge_multiple(self):
        """
        min x1+x2
        x1+x2>=4

        => vô số nghiệm tối ưu
        """
        x1 = Variable("x_1", VariableSign.NON_NEGATIVE)
        x2 = Variable("x_2", VariableSign.NON_NEGATIVE)

        constraints = [
            Constraint({"x_1": 1, "x_2": 1}, ConstraintType.GE, 4),
        ]

        objective = Objective(
            ObjectiveType.MIN,
            {"x_1": 1, "x_2": 1}
        )

        problem = Problem(objective, constraints, [x1, x2])

        result = LPSolver(problem=problem, verbose=False).solve()

        self.assertEqual(result["status"], "OPTIMAL")
        self.assertEqual(result["optimal_value"], "4")
        self.assertTrue(result.get("has_multiple_optimal", False))

    def test_case_9_unique_single_variable(self):
        """
        min x1
        x1<=5

        => nghiệm duy nhất
        """
        x1 = Variable("x_1", VariableSign.NON_NEGATIVE)

        constraints = [
            Constraint({"x_1": 1}, ConstraintType.LE, 5),
        ]

        objective = Objective(
            ObjectiveType.MIN,
            {"x_1": 1}
        )

        problem = Problem(objective, constraints, [x1])

        result = LPSolver(problem=problem, verbose=False).solve()

        self.assertEqual(result["status"], "OPTIMAL")
        self.assertEqual(result["optimal_value"], "0")
        self.assertFalse(result.get("has_multiple_optimal", False))

    def test_case_10_irrelevant_variable_multiple(self):
        """
        min x1

        x1<=5
        x2<=10

        => vô số nghiệm tối ưu
        """
        x1 = Variable("x_1", VariableSign.NON_NEGATIVE)
        x2 = Variable("x_2", VariableSign.NON_NEGATIVE)

        constraints = [
            Constraint({"x_1": 1}, ConstraintType.LE, 5),
            Constraint({"x_2": 1}, ConstraintType.LE, 10),
        ]

        objective = Objective(
            ObjectiveType.MIN,
            {"x_1": 1}
        )

        problem = Problem(objective, constraints, [x1, x2])

        result = LPSolver(problem=problem, verbose=False).solve()

        self.assertEqual(result["status"], "OPTIMAL")
        self.assertEqual(result["optimal_value"], "0")
        self.assertTrue(result.get("has_multiple_optimal", False))

if __name__ == "__main__":
    unittest.main()