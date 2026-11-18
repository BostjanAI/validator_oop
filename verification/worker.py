"""Run trusted, archived Python code in a fresh interpreter, with synthetic inputs."""

import io
import json
import logging
import sys
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import asdict, fields, is_dataclass
from importlib import import_module
from pathlib import Path


def state(value):
    """Take a value snapshot; preserve dictionary keys, order and container types."""
    if is_dataclass(value):
        return {"dataclass": f"{type(value).__module__}.{type(value).__qualname__}",
                "fields": {f.name: state(getattr(value, f.name)) for f in fields(value)}}
    if isinstance(value, dict):
        return {"items": [[state(k), state(v)] for k, v in value.items()]}
    if isinstance(value, (set, frozenset)):
        return {type(value).__name__: sorted((state(v) for v in value), key=repr)}
    if isinstance(value, (list, tuple)):
        return {type(value).__name__: [state(v) for v in value]}
    if value is None or type(value) in (str, int, float, bool):
        return value
    raise TypeError(f"Unsupported observed state: {type(value).__qualname__}")


def observe(rule, method, rows, sheet, book):
    from validator_oop.core.shared_context import SharedContextBuilder
    from validator_oop.rules.base_rule import RuleContext

    columns = list(dict.fromkeys(k for row in rows for k in row))
    shared = SharedContextBuilder(row_offset=2).build(rows, columns)
    rule.set_shared_context(shared)
    row_rule = method == "evaluate"
    context = RuleContext(sheet=sheet, workbook=book, row_index=2 if row_rule else None, shared=shared)
    evaluate = getattr(rule, method)

    def snapshots():
        # Logger identity is infrastructure. Emitted records are observed below.
        attrs = {k: v for k, v in vars(rule).items() if k != "_logger"}
        return {"rows": state(rows), "context": state(context), "rule": state(attrs)}

    before = snapshots()
    log, stdout, stderr = io.StringIO(), io.StringIO(), io.StringIO()
    handler = logging.StreamHandler(log)
    handler.setFormatter(logging.Formatter("%(levelname)s %(name)s %(message)s"))
    logger = logging.getLogger()
    level = logger.level
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    findings = []
    exception = None
    try:
        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                result = (evaluate(rows[0], context) if row_rule
                          else evaluate(rows, context, row_offset=2))
                for finding in result:
                    findings.append(finding)
            except Exception as exc:
                exception = {"type": f"{type(exc).__module__}.{type(exc).__qualname__}",
                             "args": state(exc.args)}
    finally:
        logger.removeHandler(handler)
        logger.setLevel(level)
    after = snapshots()
    effects = {k: {"before": v, "after": after[k]} for k, v in before.items()
               if json.dumps(v, allow_nan=False) != json.dumps(after[k], allow_nan=False)}
    for name, stream in (("stdout", stdout), ("stderr", stderr), ("log", log)):
        if stream.getvalue():
            effects[name] = stream.getvalue()
    return {"findings": [asdict(f) for f in findings], "exception": exception, "effects": effects}


def execute(request):
    module, cls, method = request["function"].rsplit(".", 2)
    rule = getattr(import_module("validator_oop." + module), cls)()
    return observe(rule, method, request["rows"], request["sheet"], request["book"])


if __name__ == "__main__":
    # Only the selected Git archive supplies production code and its helpers.
    sys.path.insert(0, str(Path(sys.argv[1]).absolute()))
    from validator_oop.core import _version

    requests = json.load(sys.stdin)
    json.dump({"app_version": _version.__version__, "build": _version.BUILD,
               "observations": [execute(r) for r in requests]}, sys.stdout, allow_nan=False)
