import sys
from . import __version__
from .compiler import run_source

def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print("Mlang - English-like programming language")
        print()
        print("Usage:")
        print("  python -m mlang -m run <file.mlang>")
        print("  python -m mlang --version")
        return 0

    if args[0] in ("--version", "-v"):
        print(f"Mlang {__version__}")
        return 0

    if len(args) == 3 and args[0] == "-m" and args[1] == "run":
        path = args[2]
        try:
            with open(path, "r", encoding="utf-8") as f:
                run_source(f.read())
            return 0
        except FileNotFoundError:
            print(f"Mlang error: file not found: {path}", file=sys.stderr)
            return 1
        except (SyntaxError, RuntimeError, Exception) as e:
            print(f"Mlang error: {e}", file=sys.stderr)
            return 1

    print("Mlang error: invalid command.")
    print("Usage: python -m mlang -m run <file.mlang>")
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
