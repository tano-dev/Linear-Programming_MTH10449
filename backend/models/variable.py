from enum import Enum

class VariableSign(Enum):
    """
    The sign of the variables: <= 0, >= 0, free -> str
    """
    NON_NEGATIVE = ">="
    NON_POSITIVE = "<="
    FREE = "free"

class Variable:
    """
    Variable: 
    - name: x1, x2, ... -> str
    - sign: VariableSign -> str
    """
    def __init__(self, name: str, sign=VariableSign.NON_NEGATIVE):
        self.name = name
        self.sign =sign

    def __str__(self):
        if self.sign.value == "free":
            return f"{self.name} free"
        return f"{self.name} {self.sign.value} 0"
