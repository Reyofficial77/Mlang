# Mlang

Mlang is an English-like programming language built with Python.

## Current version

Mlang 0.1.0

## Run a program

The requested CLI syntax is:

```bash
-m run hello.mlang
```

When running through Python directly:

```bash
python -m mlang -m run examples/hello.mlang
```

## Example

```mlang
var name is "rey"

if name is "rey":
    show.log("Hello rey!")
elif name is "Rey":
    show.log("Hello Rey!")
else:
    show.log("Hello Anonymous!")
```

## Current features

- `var name is value`
- `show.log(...)`
- `if / elif / else`
- `repeat while condition`
- `repeat condition times`
- English-like comparisons such as `is`, `isn't`, `greater than`, and `less than`
- Basic arithmetic
- `true`, `false`, and `nothing`
- `.mlang` source files

## Important note

Mlang 0.1 is an interpreter written in Python. Python is the implementation language; users write Mlang syntax.

The indentation parser in this first version is intentionally simple. The next major milestone should be a proper indentation-aware lexer/parser, followed by functions, lists, objects, imports, and a package system.
