from dataclasses import dataclass

@dataclass
class Program:
    statements: list

@dataclass
class VarDecl:
    name: str
    expr: object

@dataclass
class ShowLog:
    exprs: list

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
class ExprStmt:
    expr: object

@dataclass
class Literal:
    value: object

@dataclass
class Name:
    value: str

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

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.i = 0

    def cur(self):
        return self.tokens[self.i]

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
            raise SyntaxError(f"Expected {wanted} at line {t.line}, column {t.column}")
        return self.advance()

    def skip_newlines(self):
        while self.at("NEWLINE"):
            self.advance()

    def parse(self):
        statements = []
        self.skip_newlines()
        while not self.at("EOF"):
            statements.append(self.statement())
            self.skip_newlines()
        return Program(statements)

    def statement(self):
        if self.at("IDENT", "var"):
            return self.var_decl()
        if self.at("IDENT", "show"):
            return self.show_log()
        if self.at("IDENT", "if"):
            return self.if_stmt()
        if self.at("IDENT", "repeat"):
            return self.repeat_stmt()
        return ExprStmt(self.expression())

    def var_decl(self):
        self.expect("IDENT", "var")
        name = self.expect("IDENT").value
        self.expect("IDENT", "is")
        return VarDecl(name, self.expression())

    def show_log(self):
        self.expect("IDENT", "show")
        self.expect("PUNCT", ".")
        self.expect("IDENT", "log")
        self.expect("PUNCT", "(")
        args = []
        if not self.at("PUNCT", ")"):
            args.append(self.expression())
            while self.at("PUNCT", ","):
                self.advance()
                args.append(self.expression())
        self.expect("PUNCT", ")")
        return ShowLog(args)

    def if_stmt(self):
        branches = []
        self.expect("IDENT", "if")
        cond = self.expression()
        self.expect("PUNCT", ":")
        body = self.parse_indented_like_block()
        branches.append((cond, body))

        while self.at("IDENT", "elif"):
            self.advance()
            cond = self.expression()
            self.expect("PUNCT", ":")
            body = self.parse_indented_like_block()
            branches.append((cond, body))

        else_body = None
        if self.at("IDENT", "else"):
            self.advance()
            self.expect("PUNCT", ":")
            else_body = self.parse_indented_like_block()

        return IfStmt(branches, else_body)

    def repeat_stmt(self):
        self.expect("IDENT", "repeat")
        if self.at("IDENT", "while"):
            self.advance()
            condition = self.expression()
            self.expect("PUNCT", ":")
            return RepeatWhile(condition, self.parse_indented_like_block())

        if self.at("IDENT", "is"):
            self.advance()
            condition = self.expression()
            self.expect("PUNCT", ":")
            return RepeatWhile(condition, self.parse_indented_like_block())

        count = self.expression()
        self.expect("IDENT", "times")
        self.expect("PUNCT", ":")
        return RepeatTimes(count, self.parse_indented_like_block())

    def parse_indented_like_block(self):
        # Mlang 0.1 uses indentation through source preprocessing.
        self.skip_newlines()
        body = []
        while not self.at("EOF"):
            if self.at("IDENT", "elif") or self.at("IDENT", "else"):
                break
            body.append(self.statement())
            if self.at("NEWLINE"):
                self.skip_newlines()
            else:
                break
        return body

    def expression(self):
        return self.equality()

    def equality(self):
        node = self.comparison()
        while True:
            if self.at("IDENT", "is"):
                self.advance()
                if self.at("IDENT", "not"):
                    self.advance()
                    self.expect("IDENT", "equal")
                    if self.at("IDENT", "to"):
                        self.advance()
                    node = Binary(node, "!=", self.comparison())
                else:
                    if self.at("IDENT", "equal"):
                        self.advance()
                        if self.at("IDENT", "to"):
                            self.advance()
                    node = Binary(node, "==", self.comparison())
            elif self.at("IDENT", "isn't"):
                self.advance()
                node = Binary(node, "!=", self.comparison())
            elif self.at("OP", "==") or self.at("OP", "!="):
                op = self.advance().value
                node = Binary(node, op, self.comparison())
            else:
                break
        return node

    def comparison(self):
        node = self.term()
        while True:
            if self.at("IDENT", "greater"):
                self.advance()
                self.expect("IDENT", "than")
                node = Binary(node, ">", self.term())
            elif self.at("IDENT", "less"):
                self.advance()
                self.expect("IDENT", "than")
                node = Binary(node, "<", self.term())
            elif self.at("OP") and self.cur().value in (">", "<", ">=", "<="):
                op = self.advance().value
                node = Binary(node, op, self.term())
            else:
                break
        return node

    def term(self):
        node = self.factor()
        while self.at("OP") and self.cur().value in ("+", "-"):
            op = self.advance().value
            node = Binary(node, op, self.factor())
        return node

    def factor(self):
        node = self.unary()
        while self.at("OP") and self.cur().value in ("*", "/", "%"):
            op = self.advance().value
            node = Binary(node, op, self.unary())
        return node

    def unary(self):
        if self.at("IDENT", "not"):
            self.advance()
            return Unary("not", self.unary())
        if self.at("OP", "-"):
            self.advance()
            return Unary("-", self.unary())
        return self.primary()

    def primary(self):
        t = self.cur()
        if t.kind == "STRING":
            self.advance()
            raw = t.value
            try:
                value = bytes(raw[1:-1], "utf-8").decode("unicode_escape")
            except Exception:
                value = raw[1:-1]
            return Literal(value)
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
                args = []
                if not self.at("PUNCT", ")"):
                    args.append(self.expression())
                    while self.at("PUNCT", ","):
                        self.advance()
                        args.append(self.expression())
                self.expect("PUNCT", ")")
                return Call(t.value, args)
            return Name(t.value)
        if t.kind == "PUNCT" and t.value == "(":
            self.advance()
            node = self.expression()
            self.expect("PUNCT", ")")
            return node
        raise SyntaxError(f"Unexpected token {t.value!r} at line {t.line}, column {t.column}")

def parse(tokens):
    return Parser(tokens).parse()
