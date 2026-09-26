from .parser import (
    Program, VarDecl, IndexAssign, IfStmt, RepeatWhile, RepeatTimes, ForEach,
    FunctionDef, Return, Break, Continue, ExprStmt,
    Literal, ListLiteral, DictLiteral, Name, Index, Slice, Binary, Unary,
    Call, MethodCall,
)
from .runtime import (
    MlangRuntimeError, BreakSignal, ContinueSignal, ReturnSignal,
    BUILTIN_FUNCTIONS, BINARY_OPS, call_method, stringify, type_name,
)

MAX_LOOP_ITERATIONS = 1_000_000


class Scope:
    """A single namespace level. Reading a name walks up to the parent
    (enclosing) scope, but declaring/assigning a name always writes into
    *this* scope -- this is what makes a function's local variables not
    leak into (or clobber) the caller's variables, while still letting
    the function body read outer/global values and call other functions."""

    __slots__ = ("vars", "parent")

    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def get(self, name):
        scope = self
        while scope is not None:
            if name in scope.vars:
                return scope.vars[name]
            scope = scope.parent
        raise MlangRuntimeError(f"Unknown variable: {name}")

    def declare(self, name, value):
        self.vars[name] = value


class MlangFunction:
    def __init__(self, name, params, body, closure):
        self.name = name
        self.params = params
        self.body = body
        self.closure = closure


class Interpreter:
    def __init__(self):
        self.global_scope = Scope()
        self.scope = self.global_scope

    def run(self, program: Program):
        for stmt in program.statements:
            self.exec_stmt(stmt)

    def exec_block(self, body):
        for stmt in body:
            self.exec_stmt(stmt)

    # -- statements ---------------------------------------------------

    def exec_stmt(self, stmt):
        if isinstance(stmt, VarDecl):
            self.scope.declare(stmt.name, self.eval_expr(stmt.expr))

        elif isinstance(stmt, IndexAssign):
            base = self.eval_expr(stmt.base)
            index = self.eval_expr(stmt.index)
            value = self.eval_expr(stmt.value)
            try:
                base[index] = value
            except TypeError:
                raise MlangRuntimeError(f"Cannot assign into a value of type '{type_name(base)}'.")
            except IndexError:
                raise MlangRuntimeError(f"Index {index} is out of range.")

        elif isinstance(stmt, ExprStmt):
            self.eval_expr(stmt.expr)

        elif isinstance(stmt, IfStmt):
            for cond, body in stmt.branches:
                if self.truthy(self.eval_expr(cond)):
                    self.exec_block(body)
                    return
            if stmt.else_body is not None:
                self.exec_block(stmt.else_body)

        elif isinstance(stmt, RepeatWhile):
            guard = 0
            while self.truthy(self.eval_expr(stmt.condition)):
                try:
                    self.exec_block(stmt.body)
                except BreakSignal:
                    break
                except ContinueSignal:
                    pass
                guard += 1
                if guard > MAX_LOOP_ITERATIONS:
                    raise MlangRuntimeError(f"Loop exceeded {MAX_LOOP_ITERATIONS:,} iterations.")

        elif isinstance(stmt, RepeatTimes):
            count = self.eval_expr(stmt.count)
            if not isinstance(count, (int, float)):
                raise MlangRuntimeError("The 'repeat ... times' count must be a number.")
            for _ in range(int(count)):
                try:
                    self.exec_block(stmt.body)
                except BreakSignal:
                    break
                except ContinueSignal:
                    continue

        elif isinstance(stmt, ForEach):
            iterable = self.eval_expr(stmt.iterable)
            try:
                items = iter(iterable)
            except TypeError:
                raise MlangRuntimeError(f"Cannot loop over a value of type '{type_name(iterable)}'.")
            for item in items:
                self.scope.declare(stmt.var_name, item)
                try:
                    self.exec_block(stmt.body)
                except BreakSignal:
                    break
                except ContinueSignal:
                    continue

        elif isinstance(stmt, FunctionDef):
            self.scope.declare(stmt.name, MlangFunction(stmt.name, stmt.params, stmt.body, self.scope))

        elif isinstance(stmt, Return):
            value = self.eval_expr(stmt.expr) if stmt.expr is not None else None
            raise ReturnSignal(value)

        elif isinstance(stmt, Break):
            raise BreakSignal()

        elif isinstance(stmt, Continue):
            raise ContinueSignal()

        else:
            raise MlangRuntimeError(f"Unsupported statement: {type(stmt).__name__}")

    # -- expressions ----------------------------------------------------

    def eval_expr(self, expr):
        if isinstance(expr, Literal):
            return expr.value

        if isinstance(expr, Name):
            return self.scope.get(expr.value)

        if isinstance(expr, ListLiteral):
            return [self.eval_expr(e) for e in expr.items]

        if isinstance(expr, DictLiteral):
            return {self.eval_expr(k): self.eval_expr(v) for k, v in expr.pairs}

        if isinstance(expr, Index):
            base = self.eval_expr(expr.base)
            index = self.eval_expr(expr.index)
            try:
                return base[index]
            except IndexError:
                raise MlangRuntimeError(f"Index {index} is out of range.")
            except KeyError:
                raise MlangRuntimeError(f"Key {index!r} was not found.")
            except TypeError:
                raise MlangRuntimeError(f"Cannot index into a value of type '{type_name(base)}'.")

        if isinstance(expr, Slice):
            base = self.eval_expr(expr.base)
            start = self.eval_expr(expr.start) if expr.start is not None else None
            stop = self.eval_expr(expr.stop) if expr.stop is not None else None
            try:
                return base[start:stop]
            except TypeError:
                raise MlangRuntimeError(f"Cannot slice a value of type '{type_name(base)}'.")

        if isinstance(expr, Unary):
            if expr.op == "not":
                return not self.truthy(self.eval_expr(expr.expr))
            if expr.op == "-":
                value = self.eval_expr(expr.expr)
                try:
                    return -value
                except TypeError:
                    raise MlangRuntimeError(f"Cannot negate a value of type '{type_name(value)}'.")

        if isinstance(expr, Binary):
            return self.eval_binary(expr)

        if isinstance(expr, MethodCall):
            return self.eval_method_call(expr)

        if isinstance(expr, Call):
            args = [self.eval_expr(a) for a in expr.args]
            return self.call_named(expr.name, args)

        raise MlangRuntimeError(f"Unsupported expression: {type(expr).__name__}")

    def eval_binary(self, expr: Binary):
        if expr.op == "and":
            left = self.eval_expr(expr.left)
            if not self.truthy(left):
                return left
            return self.eval_expr(expr.right)

        if expr.op == "or":
            left = self.eval_expr(expr.left)
            if self.truthy(left):
                return left
            return self.eval_expr(expr.right)

        a = self.eval_expr(expr.left)
        b = self.eval_expr(expr.right)
        try:
            return BINARY_OPS[expr.op](a, b)
        except ZeroDivisionError:
            raise MlangRuntimeError("Division by zero.")
        except TypeError:
            raise MlangRuntimeError(
                f"Cannot use '{expr.op}' between a {type_name(a)} and a {type_name(b)}."
            )

    def eval_method_call(self, expr: MethodCall):
        # `show.log(...)` is Mlang's print statement: `show` is not a
        # real value, it is only meaningful together with `.log(...)`.
        if isinstance(expr.base, Name) and expr.base.value == "show" and expr.name == "log":
            args = [self.eval_expr(a) for a in expr.args]
            print(*(stringify(a) for a in args))
            return None

        base = self.eval_expr(expr.base)
        args = [self.eval_expr(a) for a in expr.args]
        return call_method(base, expr.name, args)

    def call_named(self, name, args):
        try:
            target = self.scope.get(name)
        except MlangRuntimeError:
            target = None

        if isinstance(target, MlangFunction):
            return self.call_function(target, args)

        if name in BUILTIN_FUNCTIONS:
            try:
                return BUILTIN_FUNCTIONS[name](*args)
            except MlangRuntimeError:
                raise
            except TypeError as e:
                raise MlangRuntimeError(f"Wrong number/type of arguments for '{name}()': {e}")

        if name == "show":
            # Bare show(...) is accepted as a forgiving alias of show.log(...).
            print(*(stringify(a) for a in args))
            return None

        raise MlangRuntimeError(f"Unknown function: {name}")

    def call_function(self, func: MlangFunction, args):
        if len(args) != len(func.params):
            raise MlangRuntimeError(
                f"Function '{func.name}' expects {len(func.params)} argument(s), got {len(args)}."
            )
        call_scope = Scope(parent=func.closure)
        for pname, avalue in zip(func.params, args):
            call_scope.declare(pname, avalue)

        prev_scope = self.scope
        self.scope = call_scope
        try:
            self.exec_block(func.body)
            return None
        except ReturnSignal as r:
            return r.value
        finally:
            self.scope = prev_scope

    @staticmethod
    def truthy(value):
        return bool(value)
