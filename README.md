# Mlang

![Mlang logo](logo.png)

Mlang is an English-like programming language built with Python. Its
grammar is written in plain English words wherever possible, and its
feature set (functions, lists, dictionaries, loops, logical operators,
slicing, ...) mirrors what Python itself provides.

## Current version

Mlang 0.2.0

## Run a program

The requested CLI syntax is:

```bash
-m run hello.mlang
```

When running through Python directly:

```bash
python -m mlang run examples/hello.mlang
```

If Mlang is installed and the `mlang` command is available:

```bash
mlang run examples/hello.mlang
```

## A quick tour

```mlang
# Variables
var name is "Rey"
var age is 20

# Printing
show.log("Hello,", name)

# Conditionals
if age is greater than or equal to 18:
    show.log(name, "is an adult")
elif age greater than 12:
    show.log(name, "is a teenager")
else:
    show.log(name, "is a child")

# A counted loop
repeat 3 times:
    show.log("Hi!")

# A while loop (both spellings work)
var n is 0
while n less than 3:
    show.log("n =", n)
    n += 1

# A for-each loop, over a list literal
var fruits is ["apple", "banana", "cherry"]
for each fruit in fruits:
    show.log("I like", fruit)

# Functions, with return values and recursion
function factorial(x):
    if x less than or equal to 1:
        return 1
    return x * factorial(x - 1)

show.log("5! =", factorial(5))
```

## Language reference

### Values

| Kind        | Example                          |
|-------------|-----------------------------------|
| Number      | `42`, `3.14`, `-7`                 |
| Text        | `"hello"`, `'hello'`               |
| Boolean     | `true`, `false`                    |
| Nothing     | `nothing` (like Python's `None`)   |
| List        | `[1, 2, 3]`, `["a", "b"]`          |
| Dictionary  | `{"name": "Rey", "age": 20}`       |

### Variables

```mlang
var x is 5          # declare (or re-declare) x
x is 6               # plain reassignment also works
x += 1                # also -=, *=, /=
mylist[0] is 10      # assign into a list by index
mydict["key"] is 10  # assign into a dictionary by key
```

### Printing

```mlang
show.log("a value:", value)   # prints one or more values, space-separated
show(value)                    # a forgiving shorthand for show.log
```

### Comparisons

Both a symbol form and an English form are supported, and `is` before a
comparison word is optional:

```mlang
a is b          a == b
a isn't b       a != b
a is not b      a != b
a greater than b        a > b
a is greater than b      a > b
a greater than or equal to b   a >= b
a less than b            a < b
a less than or equal to b      a <= b
x in mylist               membership test
x not in mylist
```

### Logical operators

```mlang
a and b
a or b
not a
```

### Arithmetic

```mlang
a + b     a - b     a * b     a / b
a % b     (remainder)
a // b    (whole-number division)
a ** b    (power)
```

Text can be joined with `+` (`"a" + "b"` gives `"ab"`), and repeated with
`*` (`"ab" * 3` gives `"ababab"`), same as in Python.

### If / elif / else

```mlang
if condition:
    ...
elif other_condition:
    ...
else:
    ...
```

Blocks are defined by indentation (use spaces consistently), the same
way Python does it -- indent to open a block, and dedent back to close it.
Blocks can be nested as deeply as needed.

### Loops

```mlang
repeat 5 times:
    ...

repeat while condition:
    ...

while condition:          # same as "repeat while"
    ...

for each item in a_list:
    ...

for item in a_list:        # "each" is optional
    ...
```

`break` exits the closest loop immediately; `continue` skips to the next
iteration of the closest loop.

### Functions

```mlang
function add(a, b):
    return a + b

var total is add(2, 3)
```

`return` with no value returns `nothing`. A function's own variables are
local to it -- they don't affect variables with the same name outside
the function, but the function body can still read outer/global values.

### Lists

```mlang
var items is [10, 20, 30]
items[0]                 # 10
items[0:2]                # [10, 20] (a slice)
items[0] is 99            # replace an item
items.append(40)
items.remove(20)
items.pop()
items.sort()
items.reverse()
items.index(99)
items.count(10)
items.insert(0, 5)
items.clear()
items.extend([1, 2])
items.copy()
length(items)
```

### Dictionaries

```mlang
var person is {"name": "Rey", "age": 20}
person["name"]
person["age"] is 21
person.get("name")
person.keys()
person.values()
person.items()
person.update({"age": 22})
person.pop("age")

for each key in person:
    show.log(key, "->", person[key])
```

### Text

```mlang
"hello".upper()
"HELLO".lower()
"  hi  ".strip()
"a,b,c".split(",")
"hi there".replace("hi", "hey")
"hello".startswith("he")
"hello".endswith("lo")
"-".join(["a", "b", "c"])
```

### Built-in functions

```mlang
length(x)          # number of items/characters
range(5)            # [0, 1, 2, 3, 4]
range(2, 5)          # [2, 3, 4]
ask("Name? ")        # reads a line of input from the user, like Python's input()
to_number(x)          # convert text to a number
to_text(x)             # convert any value to text
to_list(x)              # convert to a list
type_of(x)               # "number" / "text" / "boolean" / "list" / "dictionary" / "nothing"
abs(x)  min(...)  max(...)  round(x)  sum(list)  sorted(list)
```

### Comments

```mlang
# a comment runs to the end of the line
```

## Example programs

See the `examples/` folder:

- `hello.mlang` -- the classic first program
- `conditions.mlang` -- if / elif / else
- `loops.mlang` -- a counted `repeat ... times` loop
- `while.mlang` -- a `repeat while` loop
- `functions.mlang` -- functions, `return`, and recursion
- `collections.mlang` -- lists, dictionaries, and `for each`

## Important note

Mlang is an interpreter written in Python. Python is the implementation
language; users write Mlang syntax. Its indentation rules, operator
precedence, and feature set are deliberately modelled closely on
Python's own, just spelled out in more English-like words -- so anyone
who already knows a bit of Python (or a bit of English) should feel at
home quickly.

Possible next steps for a future version: classes/objects, error
handling (`try`/`catch`), string formatting/interpolation, and a small
standard library (files, math, randomness).
