from dataclasses import dataclass, field


# ------------------------------- AST -------------------------------

@dataclass
class Program:
    statements: list


@dataclass
class VarDecl:
    name: str
    expr: object


@dataclass
class IndexAssign:
    base: object
    index: object
    value: object


@dataclass
class IfStmt:
    branches: list
    else_body: list | None


@dataclass
class RepeatWhile:
    condition: object
    body: list


@dataclass
class RepeatTimes:
    count: object
    body: list


@dataclass
class ForEach:
    var_name: str
    iterable: object
    body: list


@dataclass
class FunctionDef:
    name: str
    params: list
    body: list


@dataclass
class Return:
    expr: object


@dataclass
class Break:
    pass


@dataclass
class Continue:
    pass


@dataclass
class ExprStmt:
    expr: object


@dataclass
class Literal:
    value: object


@dataclass
class ListLiteral:
    items: list


@dataclass
class DictLiteral:
    pairs: list  # list[(key_expr, value_expr)]


@dataclass
class Name:
    value: str


@dataclass
class Index:
    base: object
    index: object


@dataclass
class Slice:
    base: object
    start: object
    stop: object


@dataclass
class Binary:
    left: object
    op: str
    right: object


@dataclass
class Unary:
    op: str
    expr: object


@dataclass
class Call:
    name: str
    args: list


@dataclass
class MethodCall:
    base: object
    name: str
    args: list


# Words that mean something to the grammar and therefore can never be
# used as a plain variable/assignment target.
KEYWORDS = {
    "var", "is", "isn't", "not", "and", "or", "in",
    "if", "elif", "else",
    "repeat", "while", "times", "for", "each",
    "function", "return", "break", "continue",
    "true", "false", "nothing",
    "equal", "to", "than", "greater", "less",
}

AUGMENTED_OPS = {"+=": "+", "-=": "-", "*=": "*", "/=": "/"}


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.i = 0

    # -- low-level helpers -------------------------------------------------

    def cur(self):
        return self.tokens[self.i]

    def peek(self, offset=1):
        idx = self.i + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1]

    def at(self, kind, value=None):
        t = self.cur()
        return t.kind == kind and (value is None or t.value == value)

    def advance(self):
        t = self.cur()
        self.i += 1
        return t

    def expect(self, kind, value=None):
        if not self.at(kind, value):
            t = self.cur()
            wanted = value or kind
            raise SyntaxError(f"Expected {wanted!r} at line {t.line}, column {t.column}, got {t.value!r}")
        return self.advance()

    # -- top level / blocks --------------------------------------------

    def parse(self):
        statements = []
        while not self.at("EOF"):
            statements.append(self.statement())
        return Program(statements)

    def parse_block(self):
        """Parse an indented block: NEWLINE INDENT stmt* DEDENT."""
        self.expect("NEWLINE")
        self.expect("INDENT")
        statements = []
        while not self.at("DEDENT"):
            statements.append(self.statement())
        self.expect("DEDENT")
        return statements

    # -- statements -------------------------------------------------------

    def statement(self):
        if self.at("IDENT", "if"):
            return self.if_stmt()
        if self.at("IDENT", "repeat"):
            return self.repeat_stmt()
        if self.at("IDENT", "while"):
            return self.while_stmt()
        if self.at("IDENT", "for"):
            return self.for_stmt()
        if self.at("IDENT", "function"):
            return self.function_def()
        # Everything else is a single-line ("simple") statement, and is
        # responsible for exactly one trailing NEWLINE.
        node = self.simple_statement()
        self.expect("NEWLINE")
        return node

    def simple_statement(self):
        if self.at("IDENT", "var"):
            return self.var_decl()
        if self.at("IDENT", "return"):
            return self.return_stmt()
        if self.at("IDENT", "break"):
            self.advance()
            return Break()
        if self.at("IDENT", "continue"):
            self.advance()
            return Continue()
        node = self.try_parse_assignment()
        if node is not None:
            return node
        return ExprStmt(self.expression())

    def var_decl(self):
        self.expect("IDENT", "var")
        name = self.expect("IDENT").value
        self.expect("IDENT", "is")
        return VarDecl(name, self.expression())

    def try_parse_assignment(self):
        """Try to parse `target is expr` / `target += expr` etc.
        Returns None (and rewinds) if this doesn't turn out to be an
        assignment, so the caller can fall back to a plain expression."""
        if not self.at("IDENT") or self.cur().value in KEYWORDS:
            return None
        start = self.i
        target = self.postfix()
        assignable = isinstance(target, (Name, Index))

        if assignable and self.at("OP") and self.cur().value in AUGMENTED_OPS:
            op = AUGMENTED_OPS[self.advance().value]
            value = self.expression()
            return self.make_assign(target, Binary(target, op, value))

        if assignable and self.at("IDENT", "is"):
            self.advance()
            value = self.expression()
            return self.make_assign(target, value)

        self.i = start
        return None

    def make_assign(self, target, value_expr):
        if isinstance(target, Name):
            return VarDecl(target.value, value_expr)
        if isinstance(target, Index):
            return IndexAssign(target.base, target.index, value_expr)
        raise SyntaxError("Invalid assignment target.")

    def return_stmt(self):
        self.expect("IDENT", "return")
        if self.at("NEWLINE"):
            return Return(None)
        return Return(self.expression())

    def if_stmt(self):
        self.expect("IDENT", "if")
        cond = self.expression()
        self.expect("PUNCT", ":")
        branches = [(cond, self.parse_block())]

        while self.at("IDENT", "elif"):
            self.advance()
            cond = self.expression()
            self.expect("PUNCT", ":")
            branches.append((cond, self.parse_block()))

        else_body = None
        if self.at("IDENT", "else"):
            self.advance()
            self.expect("PUNCT", ":")
            else_body = self.parse_block()

        return IfStmt(branches, else_body)

    def while_stmt(self):
        self.expect("IDENT", "while")
        cond = self.expression()
        self.expect("PUNCT", ":")
        return RepeatWhile(cond, self.parse_block())

    def repeat_stmt(self):
        self.expect("IDENT", "repeat")
        if self.at("IDENT", "while") or self.at("IDENT", "is"):
            self.advance()
            condition = self.expression()
            self.expect("PUNCT", ":")
            return RepeatWhile(condition, self.parse_block())

        count = self.expression()
        self.expect("IDENT", "times")
        self.expect("PUNCT", ":")
        return RepeatTimes(count, self.parse_block())

    def for_stmt(self):
        self.expect("IDENT", "for")
        if self.at("IDENT", "each"):
            self.advance()
        name = self.expect("IDENT").value
        self.expect("IDENT", "in")
        iterable = self.expression()
        self.expect("PUNCT", ":")
        return ForEach(name, iterable, self.parse_block())

    def function_def(self):
        self.expect("IDENT", "function")
        name = self.expect("IDENT").value
        self.expect("PUNCT", "(")
        params = []
        if not self.at("PUNCT", ")"):
            params.append(self.expect("IDENT").value)
            while self.at("PUNCT", ","):
                self.advance()
                params.append(self.expect("IDENT").value)
        self.expect("PUNCT", ")")
        self.expect("PUNCT", ":")
        return FunctionDef(name, params, self.parse_block())

    # -- expressions --------------------------------------------------
    #
    # Precedence, loosest to tightest:
    #   or  <  and  <  not  <  equality/in  <  comparison
    #   <  term (+ -)  <  factor (* / % //)  <  power (**)
    #   <  unary (-)  <  postfix (. [] ())  <  primary

    def expression(self):
        return self.or_expr()

    def or_expr(self):
        node = self.and_expr()
        while self.at("IDENT", "or"):
            self.advance()
            node = Binary(node, "or", self.and_expr())
        return node

    def and_expr(self):
        node = self.not_expr()
        while self.at("IDENT", "and"):
            self.advance()
            node = Binary(node, "and", self.not_expr())
        return node

    def not_expr(self):
        if self.at("IDENT", "not"):
            self.advance()
            return Unary("not", self.not_expr())
        return self.equality()

    def equality(self):
        # Comparison and equality share one precedence level (just like
        # Python's ==, !=, <, >, in, ... all chain at the same level).
        # Both "x is greater than y" and the bare "x greater than y"
        # are accepted, so English phrasing stays flexible either way.
        node = self.term()
        while True:
            if self.at("IDENT", "is"):
                self.advance()
                negate = False
                if self.at("IDENT", "not"):
                    self.advance()
                    negate = True

                if self.at("IDENT", "greater") or self.at("IDENT", "less"):
                    node = Binary(node, self.comparison_op(negate), self.term())
                else:
                    if self.at("IDENT", "equal"):
                        self.advance()
                        if self.at("IDENT", "to"):
                            self.advance()
                    node = Binary(node, "!=" if negate else "==", self.term())

            elif self.at("IDENT", "isn't"):
                self.advance()
                node = Binary(node, "!=", self.term())

            elif self.at("IDENT", "greater") or self.at("IDENT", "less"):
                node = Binary(node, self.comparison_op(False), self.term())

            elif self.at("IDENT", "in"):
                self.advance()
                node = Binary(node, "in", self.term())

            elif self.at("IDENT", "not") and self.peek().kind == "IDENT" and self.peek().value == "in":
                self.advance()
                self.advance()
                node = Binary(node, "not in", self.term())

            elif self.at("OP") and self.cur().value in ("==", "!=", ">", "<", ">=", "<="):
                op = self.advance().value
                node = Binary(node, op, self.term())

            else:
                break
        return node

    def comparison_op(self, negate):
        """Consume `greater than [or equal to]` / `less than [or equal to]`
        (the "greater"/"less" token itself must already be current) and
        return the matching operator, flipped if `negate` is set (for
        the "is not greater/less than" phrasing)."""
        if self.at("IDENT", "greater"):
            self.advance()
            self.expect("IDENT", "than")
            or_equal = self._consume_or_equal_to()
            if or_equal:
                return "<" if negate else ">="
            return "<=" if negate else ">"

        self.expect("IDENT", "less")
        self.expect("IDENT", "than")
        or_equal = self._consume_or_equal_to()
        if or_equal:
            return ">" if negate else "<="
        return ">=" if negate else "<"

    def _consume_or_equal_to(self):
        if self.at("IDENT", "or"):
            self.advance()
            self.expect("IDENT", "equal")
            self.expect("IDENT", "to")
            return True
        return False

    def term(self):
        node = self.factor()
        while self.at("OP") and self.cur().value in ("+", "-"):
            op = self.advance().value
            node = Binary(node, op, self.factor())
        return node

    def factor(self):
        node = self.power()
        while self.at("OP") and self.cur().value in ("*", "/", "%", "//"):
            op = self.advance().value
            node = Binary(node, op, self.power())
        return node

    def power(self):
        node = self.unary()
        if self.at("OP", "**"):
            self.advance()
            return Binary(node, "**", self.power())  # right-associative
        return node

    def unary(self):
        if self.at("OP", "-"):
            self.advance()
            return Unary("-", self.unary())
        return self.postfix()

    def postfix(self):
        node = self.primary()
        while True:
            if self.at("PUNCT", "."):
                self.advance()
                attr = self.expect("IDENT").value
                self.expect("PUNCT", "(")
                args = self.parse_args()
                self.expect("PUNCT", ")")
                node = MethodCall(node, attr, args)
            elif self.at("PUNCT", "["):
                self.advance()
                node = self.index_or_slice(node)
            else:
                break
        return node

    def index_or_slice(self, base):
        if self.at("PUNCT", ":"):
            self.advance()
            stop = None if self.at("PUNCT", "]") else self.expression()
            self.expect("PUNCT", "]")
            return Slice(base, None, stop)

        first = self.expression()
        if self.at("PUNCT", ":"):
            self.advance()
            stop = None if self.at("PUNCT", "]") else self.expression()
            self.expect("PUNCT", "]")
            return Slice(base, first, stop)

        self.expect("PUNCT", "]")
        return Index(base, first)

    def parse_args(self):
        args = []
        if not self.at("PUNCT", ")"):
            args.append(self.expression())
            while self.at("PUNCT", ","):
                self.advance()
                args.append(self.expression())
        return args

    def primary(self):
        t = self.cur()

        if t.kind == "STRING":
            self.advance()
            return Literal(self.parse_string_literal(t.value))

        if t.kind == "NUMBER":
            self.advance()
            return Literal(float(t.value) if "." in t.value else int(t.value))

        if t.kind == "IDENT":
            self.advance()
            if t.value == "true":
                return Literal(True)
            if t.value == "false":
                return Literal(False)
            if t.value == "nothing":
                return Literal(None)
            if self.at("PUNCT", "("):
                self.advance()
                args = self.parse_args()
                self.expect("PUNCT", ")")
                return Call(t.value, args)
            return Name(t.value)

        if t.kind == "PUNCT" and t.value == "(":
            self.advance()
            node = self.expression()
            self.expect("PUNCT", ")")
            return node

        if t.kind == "PUNCT" and t.value == "[":
            self.advance()
            items = []
            if not self.at("PUNCT", "]"):
                items.append(self.expression())
                while self.at("PUNCT", ","):
                    self.advance()
                    items.append(self.expression())
            self.expect("PUNCT", "]")
            return ListLiteral(items)

        if t.kind == "PUNCT" and t.value == "{":
            self.advance()
            pairs = []
            if not self.at("PUNCT", "}"):
                pairs.append(self.dict_pair())
                while self.at("PUNCT", ","):
                    self.advance()
                    pairs.append(self.dict_pair())
            self.expect("PUNCT", "}")
            return DictLiteral(pairs)

        raise SyntaxError(f"Unexpected token {t.value!r} at line {t.line}, column {t.column}")

    def dict_pair(self):
        key = self.expression()
        self.expect("PUNCT", ":")
        value = self.expression()
        return (key, value)

    @staticmethod
    def parse_string_literal(raw):
        try:
            return bytes(raw[1:-1], "utf-8").decode("unicode_escape")
        except Exception:
            return raw[1:-1]


def parse(tokens):
    return Parser(tokens).parse()
