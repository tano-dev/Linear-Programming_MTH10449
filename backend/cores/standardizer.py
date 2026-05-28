from backend.models.variable import VariableSign, Variable
from backend.models.objective import ObjectiveType, Objective
from backend.models.constraint import ConstraintType, Constraint
from backend.models.problem import Problem
from backend.models.canonical_problem import CanonicalProblem

class Standardizer:
    """
    The Standardizer transform an arbitrary problem to the Canonical problem.
    The Canonical problem form: min c^Tx, Ax <= b, x >= 0
    """

    def __call__(self, problem):
        return self.standardize(problem)

    def standardize(self, problem: Problem) -> CanonicalProblem:
        
        # Normalize variables
        (variables, objective, constraints) = self._normalize_variables(problem=problem)

        # Normalize objective
        objective = self._normalize_objective(objective=objective)

        # Normalize constraints
        normalized_constraints = []

        for constraint in constraints:
            # equality
            eq_constraints = self._normalize_eq_constraint(constraint)

            for eq_constraint in eq_constraints:

                # >= to <= 
                final_constraint = (self._normalize_ge_constraint(eq_constraint))

                normalized_constraints.append(final_constraint)

        # Buld Canonical matrices

        variable_names = self._get_variable_names(variables=variables)

        c = self._build_c_vector(objective=objective, variable_names=variable_names)

        A = self._build_A_matrix(constraints=normalized_constraints, variable_names=variable_names)

        b = self._build_b_vector(constraints=normalized_constraints)

        return CanonicalProblem(
            c=c,
            A=A,
            b=b,
            variable_names=variable_names,
            is_from_max=(problem.objective.objective_type == ObjectiveType.MAX)
        )

    def _normalize_variables(self, problem: Problem) -> tuple[list[Variable], Objective, list[Constraint]]:

        new_variables = []
        new_objective_coeffs = (problem.objective.coeffs.copy())
        new_constraints = []

        # Handle variable transformations
        for variable in problem.variables:
            var_name = variable.name

            # Free variable, x = x_pos - x_neg
            if variable.sign == VariableSign.FREE:
                pos_name = f"{var_name}_pos"
                neg_name = f"{var_name}_neg"

                new_variables.append(
                    Variable(pos_name, VariableSign.NON_NEGATIVE)
                )

                new_variables.append(
                    Variable(neg_name, VariableSign.NON_NEGATIVE)
                )

                # Objective
                if var_name in new_objective_coeffs:
                    val = new_objective_coeffs[var_name]

                    del new_objective_coeffs[var_name]

                    new_objective_coeffs[pos_name] = val
                    new_objective_coeffs[neg_name] = -val

            # x <= 0 , x' = -x >= 0
            elif variable.sign == VariableSign.NON_POSITIVE:
                prime_name = f"{var_name}_prime"

                new_variables.append(
                    Variable(prime_name, VariableSign.NON_NEGATIVE)
                )

                # Objective
                if var_name in new_objective_coeffs:
                    val = new_objective_coeffs[var_name]

                    del new_objective_coeffs[var_name]

                    new_objective_coeffs[prime_name] = -val

            else:
                new_variables.append(
                    Variable(var_name, VariableSign.NON_NEGATIVE)
                )

        # Transform constraints
        for constraint in problem.constraints:
            coeffs = constraint.coeffs.copy()

            for variable in problem.variables:
                var_name = variable.name

                # Free
                if variable.sign == VariableSign.FREE:
                    if var_name in coeffs:
                        val = coeffs[var_name]

                        del coeffs[var_name]

                        coeffs[f"{var_name}_pos"] = val
                        coeffs[f"{var_name}_neg"] = -val

                # Non postive
                elif variable.sign == VariableSign.NON_POSITIVE:
                    if var_name in coeffs:
                        val = coeffs[var_name]

                        del coeffs[var_name]

                        coeffs[f"{var_name}_prime"] = -val
            new_constraints.append(
                Constraint(coeffs=coeffs, constraint_type=constraint.constraint_type, right_hand_side=constraint.right_hand_side)
            )
        
        new_objective = Objective(
            objective_type=problem.objective.objective_type,
            coeffs=new_objective_coeffs
        )

        return (new_variables, new_objective, new_constraints)
    
    def _normalize_objective(self, objective: Objective) -> Objective:
        """
        Objective func normalization:
        Max c^T x -> Min (-c^T)x
        """
        coeffs = objective.coeffs.copy()
        objective_type = objective.objective_type

        if objective_type == ObjectiveType.MAX:
            coeffs = {var: -val for var, val in coeffs.items()}
            objective_type = ObjectiveType.MIN
        return Objective(objective_type=objective_type, coeffs=coeffs)
    
    def _normalize_eq_constraint(self, constraint: Constraint) -> list[Constraint]:
        """
        Normalizing constraint Ax = b to 
        1. Ax <= b
        2. Ax >= b
        """
        if constraint.constraint_type != ConstraintType.EQ:
            return [constraint]
        
        coeffs = constraint.coeffs.copy()
        rhs = constraint.right_hand_side

        # Ax <= b
        le_constraint = Constraint(coeffs=coeffs.copy(), constraint_type=ConstraintType.LE, right_hand_side=rhs)

        # Ax >= b 
        ge_constraint = Constraint(coeffs=coeffs.copy(), constraint_type=ConstraintType.GE, right_hand_side=rhs)

        return [le_constraint, ge_constraint]
    
    def _normalize_ge_constraint(self, constraint: Constraint) -> Constraint:
        """
        Normalizing Ax >= b to -Ax <= -b
        """
        coeffs = constraint.coeffs.copy()
        rhs = constraint.right_hand_side

        constraint_type = constraint.constraint_type

        if constraint_type == ConstraintType.GE:
            coeffs = {var: -val for var, val in coeffs.items()}

            rhs *= -1

            constraint_type = ConstraintType.LE
        return Constraint(coeffs=coeffs, constraint_type=constraint_type, right_hand_side=rhs)
    
    @staticmethod
    def _get_variable_names(variables: list[Variable]) -> list[str]:
        return [variable.name for variable in variables]
    
    @staticmethod
    def _build_c_vector(objective: Objective, variable_names: list[str]) -> list[float]:
        return [objective.coeffs.get(var, 0) for var in variable_names]
    
    @staticmethod
    def _build_A_matrix(constraints: list[Constraint], variable_names: list[str]) -> list[list[float]]:
        A = []

        for constraint in constraints:
            row = [constraint.coeffs.get(var, 0) for var in variable_names]
            A.append(row)
        return A
    
    @staticmethod
    def _build_b_vector(constraints: list[Constraint]) -> list[float]:
        return [constraint.right_hand_side for constraint in constraints]
