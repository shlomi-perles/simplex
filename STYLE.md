# Simplex coding style

This codebase targets Python **3.14+** and enforces the rules below via ruff,
basedpyright `--strict`, and the `tools/check_readmes.py` pre-commit hook.

## Typing

- PEP 695 generics only -- `class Box[T]: ...`, `type Vec = list[float]`. **Never** `TypeVar()`.
- Built-in generics: `list[int]`, `dict[str, int]`, `X | None`. **Never** `typing.Optional` or `typing.List`.
- No `from __future__` imports.
- Pydantic v2 at every IO boundary. **No** bare `dict[str, Any]` for config.
- `basedpyright --strict` clean. `# type: ignore` requires an issue link in the comment.

## Idioms

- Paths: `pathlib.Path` everywhere. Ruff bans `os.path`.
- Strings: f-strings for interpolation; **t-strings** (PEP 750) for any user-influenced string that flows to subprocess args, HTML, or shells.
- Pattern matching: prefer `match`/`case` over discriminating `if/elif` chains.
- Dataclasses: `@dataclass(frozen=True, slots=True)` **only** for pure value objects with no validation. Anything validated -> Pydantic.

## Imports

- Absolute imports only inside `simplex.*`.
- One symbol per logical responsibility per module -- split modules instead of letting them grow.

## Subprocess

- Always pass arg lists (`subprocess.run(["manim-slides", "render", ...])`).
- **Never** `os.system`, never `shell=True`, never f-string command construction.

## File budget

- Files longer than **300 lines** need a top-of-file justification comment.
- Every directory under `src/simplex/`, `decks/`, `tests/` ships a `README.md` <= **50 lines** answering: *scope*, *public surface*, *don't*. Enforced by `tools/check_readmes.py`.

## Manim integration

- No anti-corruption wall. Authors and the framework `from manim import ...` directly.
- Don't wrap Manim constructors. Augment via `Mobject.set_default(...)` in `engine/defaults.py`.
- Don't ship layout helpers that Manim already provides (`VGroup(...).arrange(RIGHT)` stays a one-liner).
- Don't ship a custom quality enum. Use `manim.constants.QUALITIES` keys verbatim.

## Pydantic patterns

- Theme tokens: `model_config = ConfigDict(frozen=True)`.
- Mutable runtime objects (e.g. `Region`): plain `BaseModel`.
- Validators only on values that **need** them. Cross-field validation via `model_validator(mode="after")`.

## Tests

- `pytest -n auto` with `pytest-xdist`.
- Snapshots via `syrupy`. Commit the `.ambr` files alongside the test.
