"""Runtime support for Mlang: errors, control-flow signals, builtin
functions, and the whitelist of built-in methods that can be called on
text, list, and dictionary values (e.g. `mylist.append(1)`)."""


class MlangRuntimeError(Exception):
    """Raised for any error that happens while a Mlang program runs
    (as opposed to a SyntaxError, which happens while parsing it)."""
    pass


class BreakSignal(Exception):
    """Internal signal used to implement the `break` statement."""
    pass


class ContinueSignal(Exception):
    """Internal signal used to implement the `continue` statement."""
    pass


class ReturnSignal(Exception):
    """Internal signal used to implement the `return` statement."""

    def __init__(self, value=None):
        super().__init__()
        self.value = value


def _display(value):
    """Render a value the way Mlang source code would write it back,
    used for items nested inside a list/dictionary -- strings get
    quotes here so `["a", "b"]` doesn't print as indistinguishable
    from a list of bare words."""
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "nothing"
    if isinstance(value, str):
        return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'
    if isinstance(value, list):
        return "[" + ", ".join(_display(v) for v in value) + "]"
    if isinstance(value, dict):
        return "{" + ", ".join(f"{_display(k)}: {_display(v)}" for k, v in value.items()) + "}"
    return str(value)


def stringify(value):
    """Render a Mlang value for show.log(): a bare string prints as
    plain text (like Python's print), but true/false/nothing/lists/
    dictionaries print the way Mlang source code would write them."""
    if isinstance(value, str):
        return value
    return _display(value)


def type_name(value):
    """Human (English) name for a value's type, used in error messages
    and by the `type_of` builtin."""
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "text"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "dictionary"
    if value is None:
        return "nothing"
    return type(value).__name__


# ---------------------------------------------------------------------
# Builtin (global) functions, callable as plain_name(args) from Mlang.
# ---------------------------------------------------------------------

def _length(x):
    try:
        return len(x)
    except TypeError:
        raise MlangRuntimeError(f"length() needs text, a list, or a dictionary, not {type_name(x)}.")


def _range(*args):
    try:
        int_args = [int(a) for a in args]
    except (TypeError, ValueError):
        raise MlangRuntimeError("range() needs number arguments.")
    return list(range(*int_args))


def _ask(prompt=""):
    return input(stringify(prompt) if not isinstance(prompt, str) else prompt)


def _to_number(x):
    if isinstance(x, bool):
        raise MlangRuntimeError("Cannot convert a boolean to a number.")
    if isinstance(x, (int, float)):
        return x
    if isinstance(x, str):
        text = x.strip()
        try:
            if "." in text:
                return float(text)
            return int(text)
        except ValueError:
            try:
                return float(text)
            except ValueError:
                raise MlangRuntimeError(f"Cannot convert {x!r} to a number.")
    raise MlangRuntimeError(f"Cannot convert {type_name(x)} to a number.")


def _to_text(x):
    return stringify(x)


def _to_list(x):
    try:
        return list(x)
    except TypeError:
        raise MlangRuntimeError(f"Cannot convert {type_name(x)} to a list.")


def _type_of(x):
    return type_name(x)


def _round(x, digits=None):
    return round(x) if digits is None else round(x, int(digits))


BUILTIN_FUNCTIONS = {
    "length": _length,
    "range": _range,
    "ask": _ask,
    "to_number": _to_number,
    "to_text": _to_text,
    "to_list": _to_list,
    "type_of": _type_of,
    "abs": abs,
    "min": min,
    "max": max,
    "round": _round,
    "sum": sum,
    "sorted": lambda x: sorted(x),
}


# ---------------------------------------------------------------------
# Methods callable on values with the `.` syntax, e.g. text.upper() or
# mylist.append(1). Only names in this whitelist are reachable, so a
# Mlang program can never call arbitrary/dangerous Python methods.
# ---------------------------------------------------------------------

ALLOWED_METHODS = {
    str: {
        "upper", "lower", "strip", "lstrip", "rstrip", "split", "replace",
        "startswith", "endswith", "find", "count", "title", "capitalize",
        "join",
    },
    list: {
        "append", "remove", "pop", "sort", "reverse", "index", "count",
        "insert", "clear", "extend", "copy",
    },
    dict: {
        "get", "keys", "values", "items", "pop", "update", "clear",
        "copy", "setdefault",
    },
}

# These methods return a Python view/iterator that should be flattened
# to a plain list so it prints and behaves the way Mlang values do.
_METHODS_RETURNING_VIEWS = {"keys", "values", "items"}


def call_method(base, name, args):
    method_set = ALLOWED_METHODS.get(type(base))
    if method_set is None or name not in method_set:
        raise MlangRuntimeError(f"A value of type '{type_name(base)}' has no method '{name}'.")
    method = getattr(base, name)
    try:
        result = method(*args)
    except MlangRuntimeError:
        raise
    except Exception as e:
        raise MlangRuntimeError(f"Error calling '.{name}()': {e}")
    if name in _METHODS_RETURNING_VIEWS:
        result = list(result)
    return result


BINARY_OPS = {
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    ">": lambda a, b: a > b,
    "<": lambda a, b: a < b,
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b,
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "*": lambda a, b: a * b,
    "/": lambda a, b: a / b,
    "%": lambda a, b: a % b,
    "//": lambda a, b: a // b,
    "**": lambda a, b: a ** b,
    "in": lambda a, b: a in b,
    "not in": lambda a, b: a not in b,
}
