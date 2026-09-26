import re
from dataclasses import dataclass

@dataclass
class Token:
    kind: str
    value: str
    line: int
    column: int

TOKEN_RE = re.compile(
    r'(?P<STRING>"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')'
    r'|(?P<NUMBER>\d+(?:\.\d+)?)'
    r'|(?P<OP>==|!=|>=|<=|[+\-*/%=<>])'
    r'|(?P<IDENT>[A-Za-z_][A-Za-z0-9_]*)'
    r'|(?P<PUNCT>[():,\.\[\]])'
    r'|(?P<NEWLINE>\n)'
    r'|(?P<SKIP>[ \t]+)'
    r'|(?P<COMMENT>#[^\n]*)'
)

def tokenize(source):
    tokens = []
    lines = source.splitlines(True)
    for line_no, line in enumerate(lines, 1):
        pos = 0
        while pos < len(line):
            m = TOKEN_RE.match(line, pos)
            if not m:
                raise SyntaxError(f"Unexpected character {line[pos]!r} at line {line_no}, column {pos+1}")
            kind = m.lastgroup
            value = m.group()
            pos = m.end()
            if kind in ("SKIP", "COMMENT"):
                continue
            if kind == "NEWLINE":
                tokens.append(Token("NEWLINE", "\n", line_no, pos))
            else:
                tokens.append(Token(kind, value, line_no, m.start()+1))
    tokens.append(Token("EOF", "", len(lines) + 1, 1))
    return tokens
