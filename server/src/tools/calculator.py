from langchain.tools import tool

@tool
def calculator(expression: str) -> str:
    """
    Evaluate a mathematical expression.
    Example: '2 + 3 * 4'
    """

    try:
        # safe eval (basic protection)
        allowed_chars = "0123456789+-*/(). "
        if not all(c in allowed_chars for c in expression):
            return "Error: Invalid characters"

        result = eval(expression)
        return str(result)

    except Exception as e:
        return f"Error: {str(e)}"