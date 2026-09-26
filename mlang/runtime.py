class MlangRuntimeError(Exception):
    pass

def show_log(*args):
    print(*args)

def mlang_equals(a, b):
    return a == b

def mlang_not_equals(a, b):
    return a != b
