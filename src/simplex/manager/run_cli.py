"""Subprocess entry point for manager jobs.

Running ``python -m simplex.cli.commands`` re-executes a module that
``simplex.cli`` imports from its package ``__init__``. This tiny wrapper keeps
manager command execution out of that import path.
"""

from simplex.cli.commands import app


def main() -> None:
    """Run the Simplex CLI app for a manager subprocess."""
    app(prog_name="simplex")


if __name__ == "__main__":
    main()
