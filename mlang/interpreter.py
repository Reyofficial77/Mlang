from .parser import *
from .runtime import MlangRuntimeError

class ReturnSignal(Exception):
    pass

class Interpreter:
    def __init__(self):
        self.env = {}

    def run(self, program):
        for stmt in program.statements:
            self.exec_stmt(stmt)

    def exec_block(self, body):
        for stmt in body:
            self.exec_stmt(stmt)

    def exec_stmt(self, stmt):
        if isinstance(stmt, VarDecl):
            self.env[stmt.name] = self.eval_expr(stmt.expr)
        elif isinstance(stmt, ShowLog):
            print(*(self.eval_expr(x) for x in stmt.exprs))
        elif isinstance(stmt, ExprStmt):
            self.eval_expr(stmt.expr)
        elif isinstance(stmt, IfStmt):
            for cond, body in stmt.branches:
                if self.eval_expr(cond):
                    self.exec_block(body)
                    return
            if stmt.else_body is not None:
                self.exec_block(stmt.else_body)
        elif isinstance(stmt, RepeatWhile):
            guard = 0
            while self.eval_expr(stmt.condition):
                self.exec_block(stmt.body)
                guard += 1
                if guard > 100000:
                    raise MlangRuntimeError("Loop exceeded 100000 iterations.")
        elif isinstance(stmt, RepeatTimes):
            count = int(self.eval_expr(stmt.count))
            for _ in range(count):
                self.exec_block(stmt.body)
        else:
            raise MlangRuntimeError(f"Unsupported statement: {type(stmt).__name__}")

    def eval_expr(self, expr):
        if isinstance(expr, Literal):
            return expr.value
        if isinstance(expr, Name):
            if expr.value not in self.env:
                raise MlangRuntimeError(f"Unknown variable: {expr.value}")
            return self.env[expr.value]
        if isinstance(expr, Unary):
            value = self.eval_expr(expr.expr)
            if expr.op == "not":
                return not value
            if expr.op == "-":
                return -value
        if isinstance(expr, Binary):
            a = self.eval_expr(expr.left)
            b = self.eval_expr(expr.right)
            return {
                "==": lambda: a == b,
                "!=": lambda: a != b,
                ">": lambda: a > b,
                "<": lambda: a < b,
                ">=": lambda: a >= b,
                "<=": lambda: a <= b,
                "+": lambda: a + b,
                "-": lambda: a - b,
                "*": lambda: a * b,
                "/": lambda: a / b,
                "%": lambda: a % b,
            }[expr.op]()
        if isinstance(expr, Call):
            if expr.name == "show":
                args = [self.eval_expr(x) for x in expr.args]
                print(*args)
                return None
            raise MlangRuntimeError(f"Unknown function: {expr.name}")
        raise MlangRuntimeError(f"Unsupported expression: {type(expr).__name__}")
