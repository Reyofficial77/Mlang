import re
from dataclasses import dataclass


@dataclass
class Token:
    kind: str
    value: str
    line: int
    column: int


# Order matters inside each alternation group: longer/more specific
# operators must be listed before shorter ones they overlap with
# (e.g. "**" before "*", "+=" before "+"), otherwise the shorter
# token would always win the match.
TOKEN_RE = re.compile(
    r'(?P<STRING>"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')'
    r'|(?P<NUMBER>\d+(?:\.\d+)?)'
    r'|(?P<OP>\*\*|//|==|!=|>=|<=|\+=|-=|\*=|/=|[+\-*/%=<>])'
    r"|(?P<IDENT>[A-Za-z_][A-Za-z0-9_]*(?:'[A-Za-z]+)?)"
    r'|(?P<PUNCT>[():,\.\[\]\{\}])'
    r'|(?P<SKIP>[ \t]+)'
    r'|(?P<COMMENT>#[^\n]*)'
)


def tokenize(source):
    """Tokenize Mlang source into a flat token stream.

    Indentation is tracked the same way Python does it: each logical
    (non-blank, non-comment-only) line's leading whitespace is compared
    against an indent stack, producing INDENT / DEDENT tokens whenever
    it grows or shrinks. This lets the parser treat nested blocks
    (if inside while inside function, etc.) correctly no matter how
    deep they go, instead of guessing where a block ends.
    """
    tokens = []
    lines = source.splitlines()
    indent_stack = [0]
    line_no = 0

    for raw_line in lines:
        line_no += 1

        stripped = raw_line.lstrip(' \t')
        indent_str = raw_line[: len(raw_line) - len(stripped)]
        indent_width = len(indent_str.expandtabs(4))

        # A line that is blank, or only whitespace + a comment, carries
        # no tokens and must not affect indentation tracking at all.
        content_only = stripped.split('#', 1)[0].strip()
        if content_only == '':
            continue

        if indent_width > indent_stack[-1]:
            indent_stack.append(indent_width)
            tokens.append(Token("INDENT", "", line_no, 1))
        while indent_width < indent_stack[-1]:
            indent_stack.pop()
            tokens.append(Token("DEDENT", "", line_no, 1))
        if indent_width != indent_stack[-1]:
            raise SyntaxError(
                f"Inconsistent indentation at line {line_no}: it doesn't "
                "match any previous indentation level."
            )

        pos = len(indent_str)
        while pos < len(raw_line):
            m = TOKEN_RE.match(raw_line, pos)
            if not m:
                raise SyntaxError(
                    f"Unexpected character {raw_line[pos]!r} at line {line_no}, "
                    f"column {pos + 1}"
                )
            kind = m.lastgroup
            value = m.group()
            pos = m.end()
            if kind in ("SKIP", "COMMENT"):
                continue
            tokens.append(Token(kind, value, line_no, m.start() + 1))

        tokens.append(Token("NEWLINE", "\n", line_no, len(raw_line) + 1))

    while len(indent_stack) > 1:
        indent_stack.pop()
        tokens.append(Token("DEDENT", "", line_no + 1, 1))

    tokens.append(Token("EOF", "", line_no + 1, 1))
    return tokens
