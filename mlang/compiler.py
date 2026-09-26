from .lexer import tokenize
from .parser import parse
from .interpreter import Interpreter

def run_source(source):
    tokens = tokenize(source)
    program = parse(tokens)
    Interpreter().run(program)
