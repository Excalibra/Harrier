from app.utils import get_logger
from pyparsing import CaselessLiteral, Word, alphas,\
    nums, QuotedString, Group,ParserElement, infixNotation, opAssoc, ParseException

ParserElement.enablePackrat()


logger = get_logger()

# define operators
equals = CaselessLiteral("=")
contains = CaselessLiteral("==")
not_contains = CaselessLiteral("!=")
and_op = CaselessLiteral("&&")
or_op = CaselessLiteral("||")
not_op = CaselessLiteral("!")

# grammar for variables and values
variable = Word(alphas + "_")

integer = Word(nums)

escape_char = "\\"
quoted_string = QuotedString('"', escChar=escape_char, unquoteResults=False)


value = quoted_string | integer


# grammar for expressions
bool_expr = infixNotation(
    Group(variable + equals + value) |
    Group(variable + contains + value) |
    Group(variable + not_contains + value) |
    Group(not_op + variable),
    [
        (not_op, 1, opAssoc.RIGHT),
        (and_op, 2, opAssoc.LEFT),
        (or_op, 2, opAssoc.LEFT),
    ]
)


# operator implementations
operators = {
    '==': lambda x, y: x == y,
    '!=': lambda x, y: x not in y,
    '=': lambda x, y: x in y,
    '!': lambda x: not x,
    '&&': lambda x, y: x and y,
    '||': lambda x, y: x or y
}


# unquote a double-quoted string
def unquote_string(s):
    # strip the quotes
    s = s[1:-1]

    # handle escape characters
    s = s.replace('\\\\', '\\')
    s = s.replace('\\n', '\n')
    s = s.replace('\\t', '\t')
    s = s.replace('\\r', '\r')
    s = s.replace('\\"', '"')

    return s


# parse an expression
def parse_expression(expression):
    result = bool_expr.parseString(expression, parseAll=True)
    return result.as_list()


#  evaluate recursively
def evaluate_expression(parsed, variables):
    if isinstance(parsed, str):
        if parsed in variables:
            return variables[parsed]
        elif parsed.startswith('"'):
            return unquote_string(parsed)
        else:
            raise ValueError(f"Unknown variable: {parsed}")

    elif len(parsed) == 1:
        return evaluate_expression(parsed[0], variables)
    elif len(parsed) == 2:
        return operators[parsed[0]](evaluate_expression(parsed[1], variables))
    elif len(parsed) == 3:
        return operators[parsed[1]](evaluate_expression(parsed[2], variables), evaluate_expression(parsed[0], variables))


def evaluate(expression, variables):
    parsed = parse_expression(expression)
    return evaluate_expression(parsed, variables)


def _check_expression(expression):
    variables = {
        'body': "",
        'header': "",
        'title': "",
        'icon_hash': ""
    }
    try:
        return evaluate(expression, variables)
    except ParseException as e:
        raise ValueError(f"Invalid expression: {expression}  exception: {e}")
    except Exception as e:
        raise ValueError(f"Error evaluating expression: {expression} exception: {e}")


def check_expression(expression):
    try:
        _check_expression(expression)
        return True
    except ValueError as e:
        logger.error(e)
        # import traceback
        # traceback.print_exception(type(e), e, e.__traceback__)
        return False


def check_expression_with_error(expression):
    try:
        _check_expression(expression)
        return True, None,
    except ValueError as e:
        return False, e

