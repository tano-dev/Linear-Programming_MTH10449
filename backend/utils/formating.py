def clean_number(x):
    if float(x).is_integer():
        return int(x)

    return round(x, 3)

def format_expression(coeffs: dict[str, float]) -> str:
    """
    Formating the expression
    Ex: 
        max z = 3x1 + 2x2
        # Formatting
        -x1 + x2 <= 4
        2x1 - x2 <= 5
        x1 >= 0
        x2 >= 0
    """
    result = []

    first = True
    
    for var, coeff in coeffs.items():
        if coeff == 0:
            continue
        sign = "+" if coeff > 0 else "-"

        coef_abs = clean_number(abs(coeff))

        if coef_abs == 1:
            term = f"{var}"
        else:
            term = f"{coef_abs}{var}"

        if first:
            if coeff < 0:
                result.append(f"-{term}")
            else:
                result.append(f"{term}")

            first = False
        
        else:
            result.append(f" {sign} {term}")
        
    return "".join(result)