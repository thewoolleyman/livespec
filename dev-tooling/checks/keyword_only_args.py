"""keyword_only_args: enforce *-separator on every def + dataclass triple.

Per python-skill-script-style-requirements.md lines 1297-1357
(§"Keyword-only arguments"):

Rule 1 — `*`-separator on every def:
    Every `ast.FunctionDef` / `ast.AsyncFunctionDef` in scope MUST
    place a lone `*` as its first parameter (or, for methods,
    immediately after `self` / `cls`), so that every subsequent
    parameter is in `args.kwonlyargs`. Zero-parameter defs are
    trivially compliant.

Rule 2 — strict-dataclass triple:
    Every `@dataclass(...)` decorator MUST carry the keyword-arg
    triple `frozen=True, kw_only=True, slots=True`. Bare
    `@dataclass` (no Call) and `@dataclass(...)` missing any of
    the triple are violations.

Exemptions from Rule 1:

- Dunder methods (name matches `^__.+__$`): Python-mandated
  signatures (`__eq__`, `__hash__`, `__getitem__`, `__iter__`,
  `__next__`, `__init__` of Exception subclasses with single
  positional `msg`, `__post_init__`, etc.).
- ROP-chain DSL callbacks: a def whose name appears as a
  positional `ast.Name` argument to a `dry-python/returns` ROP
  chain method (`.bind`, `.map`, `.alt`, `.lash`, `.apply`,
  `.bind_result`, `.bind_ioresult`) within the same file. ROP
  composition is treated as a small DSL where each callback
  receives exactly one positional payload — positional-order
  ambiguity (the rule's stated motivation) does not arise.
- Protocol method definitions: methods inside a `class X(Protocol)`
  declare a structural type-system surface that mirrors a
  third-party API (e.g., `Logger` for structlog's `BoundLogger`).
  Forcing keyword-only on Protocol methods would either rename
  parameters away from the third-party convention (breaking
  runtime when callers pass kwargs that the implementor doesn't
  bind) or force livespec call-sites to call positional methods
  via kwarg. The exemption is per-method, scoped to direct
  children of a `Protocol`-based ClassDef.

Scope: `.claude-plugin/scripts/livespec/**`,
`.claude-plugin/scripts/bin/**`, `<repo-root>/dev-tooling/**`.
"""

from __future__ import annotations

import ast
import logging
import sys
from pathlib import Path

__all__: list[str] = [
    "check_file",
    "main",
]


log = logging.getLogger(__name__)

_SCOPE_DIRS: tuple[Path, ...] = (
    Path(".claude-plugin/scripts/livespec"),
    Path(".claude-plugin/scripts/bin"),
    Path("dev-tooling"),
)
_VENDOR_SUBSTR = "_vendor"
_PYCACHE_SUBSTR = "__pycache__"

_ROP_METHODS: frozenset[str] = frozenset(
    {
        "alt",
        "apply",
        "bind",
        "bind_ioresult",
        "bind_result",
        "lash",
        "map",
    }
)

_DATACLASS_TRIPLE: frozenset[str] = frozenset({"frozen", "kw_only", "slots"})


def main() -> int:
    """Walk scoped trees; return 0 on pass, 1 on any violation."""
    repo_root = Path.cwd()
    failures: list[str] = []
    for scope in _SCOPE_DIRS:
        scope_dir = repo_root / scope
        if not scope_dir.is_dir():
            continue
        for path in sorted(scope_dir.rglob("*.py")):
            if _VENDOR_SUBSTR in path.parts or _PYCACHE_SUBSTR in path.parts:
                continue
            for v in check_file(path=path):
                failures.append(f"{path}: {v}")
    for failure in failures:
        log.error("%s", failure)
    if failures:
        log.error("keyword_only_args: %d violation(s)", len(failures))
        return 1
    return 0


def check_file(*, path: Path) -> list[str]:
    """Return violation messages for `path`. Empty = pass."""
    text = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as e:
        return [f"syntax error: {e.msg}"]
    rop_names = _rop_callback_names(tree=tree)
    protocol_method_ids = _protocol_method_ids(tree=tree)
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            if id(node) in protocol_method_ids:
                continue
            _check_function(node=node, rop_names=rop_names, violations=violations)
        elif isinstance(node, ast.ClassDef):
            _check_class_decorators(node=node, violations=violations)
    return violations


def _protocol_method_ids(*, tree: ast.Module) -> set[int]:
    """Collect FunctionDef ids that are direct methods of a Protocol class."""
    ids: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        if not _has_protocol_base(class_def=node):
            continue
        for child in node.body:
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                ids.add(id(child))
    return ids


def _has_protocol_base(*, class_def: ast.ClassDef) -> bool:
    """True iff the class has `Protocol` as a direct base.

    Recognizes bare `class X(Protocol):` and `class X(Protocol[T]):`
    (the parametric form, where the base is an `ast.Subscript`
    whose value is `Protocol`).
    """
    for base in class_def.bases:
        if isinstance(base, ast.Name) and base.id == "Protocol":
            return True
        if (
            isinstance(base, ast.Subscript)
            and isinstance(base.value, ast.Name)
            and base.value.id == "Protocol"
        ):
            return True
    return False


def _rop_callback_names(*, tree: ast.Module) -> frozenset[str]:
    """Collect names referenced positionally to ROP-chain methods in this file.

    Recognizes both bare-name callbacks (`.bind(_orchestrate)`) and
    bound-method callbacks (`.bind(self._orchestrate)`). The latter
    is the canonical form inside `@rop_pipeline`-decorated classes,
    where chain steps are private methods on the pipeline class.
    """
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in _ROP_METHODS:
            continue
        for arg in node.args:
            if isinstance(arg, ast.Name):
                names.add(arg.id)
            elif isinstance(arg, ast.Attribute):
                names.add(arg.attr)
    return frozenset(names)


def _check_function(
    *,
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    rop_names: frozenset[str],
    violations: list[str],
) -> None:
    if _is_dunder(name=node.name):
        return
    if node.name in rop_names:
        return
    declared = list(node.args.posonlyargs) + list(node.args.args)
    if declared and declared[0].arg in {"self", "cls"}:
        declared = declared[1:]
    if declared:
        names = ", ".join(arg.arg for arg in declared)
        violations.append(
            f"line {node.lineno}: def `{node.name}({names}, ...)` lacks `*` "
            f"separator (every parameter must be keyword-only)",
        )


def _check_class_decorators(
    *,
    node: ast.ClassDef,
    violations: list[str],
) -> None:
    for decorator in node.decorator_list:
        if _is_bare_dataclass(decorator=decorator):
            violations.append(
                f"line {node.lineno}: class `{node.name}` uses bare `@dataclass`; "
                f"must declare frozen=True, kw_only=True, slots=True",
            )
            continue
        if not _is_dataclass_call(decorator=decorator):
            continue
        triple_ok = _has_strict_triple(call=decorator)
        if not triple_ok:
            violations.append(
                f"line {node.lineno}: class `{node.name}` @dataclass missing "
                f"strict triple (frozen=True, kw_only=True, slots=True)",
            )


_DUNDER_MIN_LEN = 4


def _is_dunder(*, name: str) -> bool:
    return len(name) >= _DUNDER_MIN_LEN and name.startswith("__") and name.endswith("__")


def _is_bare_dataclass(*, decorator: ast.expr) -> bool:
    if isinstance(decorator, ast.Name) and decorator.id == "dataclass":
        return True
    return isinstance(decorator, ast.Attribute) and decorator.attr == "dataclass"


def _is_dataclass_call(*, decorator: ast.expr) -> bool:
    if not isinstance(decorator, ast.Call):
        return False
    func = decorator.func
    if isinstance(func, ast.Name) and func.id == "dataclass":
        return True
    return isinstance(func, ast.Attribute) and func.attr == "dataclass"


def _has_strict_triple(*, call: ast.Call) -> bool:
    """True iff every member of {frozen, kw_only, slots} is set to True."""
    found_true: set[str] = set()
    for kw in call.keywords:
        if kw.arg in _DATACLASS_TRIPLE and _is_constant_true(value=kw.value):
            found_true.add(kw.arg)
    return found_true == _DATACLASS_TRIPLE


def _is_constant_true(*, value: ast.expr) -> bool:
    return isinstance(value, ast.Constant) and value.value is True


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR, format="%(message)s", stream=sys.stderr)
    sys.exit(main())
