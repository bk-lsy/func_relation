#!/usr/bin/env python3
"""Source-only, configuration-aware function relation analyzer for C files.

This intentionally does not invoke a compiler, expand includes, or chase calls
outside the input translation unit.  It is a conservative review aid: UNKNOWN
means that the selected source-only model cannot make a trustworthy judgement.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from rules.api import (
    CallClassificationContext,
    CallClassificationRule,
    FunctionDiscoveryContext,
    FunctionDiscoveryRule,
    FunctionOrderRule,
    Rule,
    SemanticRule,
    SemanticRuleContext,
    SemanticRuleResult,
)


DIRECTIVE = re.compile(r"^\s*#\s*(\w+)(?:\s+(.*?))?\s*$")
IDENT = re.compile(r"\b[A-Za-z_]\w*\b")
TOKEN = re.compile(
    r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|'
    r"(?:0[xX][0-9a-fA-F]+|\d+)|(?:[A-Za-z_]\w*)|"
    r"(?:>>=|<<=|==|!=|<=|>=|&&|\|\||\+\+|--|->|\+=|-=|\*=|/=|%=|<<|>>)|[^\s]"
)
KEYWORDS = {
    "if", "else", "for", "while", "switch", "case", "return", "sizeof",
    "do", "goto", "break", "continue", "typedef", "struct", "union", "enum",
    "const", "volatile", "static", "extern", "unsigned", "signed", "void",
    "char", "short", "int", "long", "float", "double", "bool", "_Bool",
}
TYPE_WORDS = KEYWORDS | {"LOCAL", "BOOL", "S8", "U8", "S16", "U16", "S32", "U32", "S64", "U64", "time_t"}


@dataclass
class Branch:
    parent_active: bool
    active: bool
    taken: bool


@dataclass
class Function:
    name: str
    params: str
    body: str
    raw: str


def load_profile(path: Path) -> Dict[str, int]:
    """Read the deliberately small KEY: value profile format (also YAML subset)."""
    macros: Dict[str, int] = {}
    for number, line in enumerate(path.read_text().splitlines(), 1):
        text = line.split("#", 1)[0].strip()
        if not text:
            continue
        if ":" not in text:
            raise ValueError(f"{path}:{number}: expected KEY: value")
        key, value = (part.strip() for part in text.split(":", 1))
        if not re.fullmatch(r"[A-Za-z_]\w*", key):
            raise ValueError(f"{path}:{number}: invalid macro name {key!r}")
        lowered = value.lower()
        if lowered in {"true", "yes", "on"}:
            macros[key] = 1
        elif lowered in {"false", "no", "off"}:
            macros[key] = 0
        else:
            macros[key] = int(value, 0)
    return macros


CONFIG_FIELDS = {
    "base_dir", "source_path", "before", "after", "profile", "output_dir",
    "max_semantic_lines", "call_depth", "raw_hash", "structural_hash", "semantic_hash",
}
HASH_FIELDS = ("raw_hash", "structural_hash", "semantic_hash")
_RULES: List[Rule] | None = None


def load_config(path: Path) -> Dict[str, str]:
    """Read the flat YAML configuration used to run this analyzer.

    Keeping this parser intentionally small avoids making PyYAML a runtime
    dependency. Values may be quoted and comments may follow a value.
    """
    config: Dict[str, str] = {}
    for number, line in enumerate(path.read_text().splitlines(), 1):
        text = line.split("#", 1)[0].strip()
        if not text:
            continue
        if ":" not in text:
            raise ValueError(f"{path}:{number}: expected KEY: value")
        key, value = (part.strip() for part in text.split(":", 1))
        if key not in CONFIG_FIELDS:
            raise ValueError(f"{path}:{number}: unsupported setting {key!r}")
        if not value:
            raise ValueError(f"{path}:{number}: {key!r} must have a value")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"\"", "'"}:
            value = value[1:-1]
        config[key] = value
    required = {"base_dir", "source_path", "before", "after", "profile"}
    missing = sorted(required - config.keys())
    if missing:
        raise ValueError(f"{path}: missing required setting(s): {', '.join(missing)}")
    return config


def config_path(value: str, config_file: Path) -> Path:
    """Resolve a config-file path relative to the config file itself."""
    path = Path(value).expanduser()
    return (path if path.is_absolute() else config_file.parent / path).resolve()


def parse_bool(value: str, setting: str) -> bool:
    lowered = value.lower()
    if lowered in {"true", "yes", "on", "1"}:
        return True
    if lowered in {"false", "no", "off", "0"}:
        return False
    raise ValueError(f"{setting} must be true or false")


def hash_options(config: Dict[str, str]) -> Dict[str, bool]:
    """Return the optional report fields selected in config.yaml."""
    return {name: parse_bool(config.get(name, "true"), name) for name in HASH_FIELDS}


def load_rules() -> List[Rule]:
    """动态扫描 rules/*.py 并加载声明为 RULE 的规则。"""
    rules_dir = Path(__file__).with_name("rules")
    loaded: List[Rule] = []
    for path in sorted(rules_dir.glob("*.py")):
        if path.name in {"__init__.py", "api.py"}:
            continue
        module_name = f"func_relation_dynamic_rule_{path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ValueError(f"cannot load rule module: {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        rule = getattr(module, "RULE", None)
        if not isinstance(rule, (SemanticRule, FunctionDiscoveryRule, FunctionOrderRule, CallClassificationRule)):
            raise ValueError(f"{path}: RULE must implement a supported rule interface")
        if not rule.name or not rule.description_zh:
            raise ValueError(f"{path}: rule name and Chinese description are required")
        loaded.append(rule)
    names = [rule.name for rule in loaded]
    if len(names) != len(set(names)):
        raise ValueError("duplicate rule name")
    return loaded


def rules() -> List[Rule]:
    """每个进程动态加载一次，避免为每个函数重复执行插件文件。"""
    global _RULES
    if _RULES is None:
        _RULES = load_rules()
    return _RULES


def semantic_rules() -> List[SemanticRule]:
    return [rule for rule in rules() if isinstance(rule, SemanticRule)]


def single_rule(rule_type: type, label: str) -> Rule:
    selected = [rule for rule in rules() if isinstance(rule, rule_type)]
    if len(selected) != 1:
        raise ValueError(f"expected exactly one {label} rule, found {len(selected)}")
    return selected[0]


def function_discovery_rule() -> FunctionDiscoveryRule:
    return single_rule(FunctionDiscoveryRule, "function discovery")  # type: ignore[return-value]


def function_order_rule() -> FunctionOrderRule:
    return single_rule(FunctionOrderRule, "function order")  # type: ignore[return-value]


def call_classification_rule() -> CallClassificationRule:
    return single_rule(CallClassificationRule, "call classification")  # type: ignore[return-value]


def eval_condition(expression: str, macros: Dict[str, int]) -> bool:
    """Evaluate the common, integer-only #if subset; reject unknown syntax."""
    expression = re.sub(
        r"defined\s*(?:\(\s*([A-Za-z_]\w*)\s*\)|\s+([A-Za-z_]\w*))",
        lambda m: "1" if macros.get(m.group(1) or m.group(2), 0) else "0",
        expression,
    )

    def macro_value(match: re.Match[str]) -> str:
        word = match.group(0)
        return str(macros.get(word, 0))

    expression = IDENT.sub(macro_value, expression)
    expression = expression.replace("&&", " and ").replace("||", " or ")
    expression = re.sub(r"!(?!=)", " not ", expression)
    if not re.fullmatch(r"[\s\dxa-fA-F()+\-*/%<>=!&|~andornot]+", expression):
        raise ValueError(f"unsupported #if expression: {expression!r}")
    try:
        return bool(eval(expression, {"__builtins__": {}}, {}))
    except (SyntaxError, ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"cannot evaluate #if expression: {expression!r}") from exc


def flatten(source: str, profile: Dict[str, int]) -> Tuple[str, List[str]]:
    macros = dict(profile)
    stack: List[Branch] = []
    output: List[str] = []
    diagnostics: List[str] = []

    def active() -> bool:
        return all(item.active for item in stack)

    for line_no, line in enumerate(source.splitlines(keepends=True), 1):
        directive = DIRECTIVE.match(line)
        if not directive:
            output.append(line if active() else "\n")
            continue
        kind, argument = directive.group(1), (directive.group(2) or "").strip()
        try:
            if kind in {"if", "ifdef", "ifndef"}:
                parent = active()
                if kind == "ifdef":
                    selected = bool(macros.get(argument, 0))
                elif kind == "ifndef":
                    selected = not bool(macros.get(argument, 0))
                else:
                    selected = eval_condition(argument, macros)
                stack.append(Branch(parent, parent and selected, selected))
            elif kind == "elif":
                if not stack:
                    raise ValueError("#elif without #if")
                branch = stack[-1]
                selected = eval_condition(argument, macros)
                branch.active = branch.parent_active and not branch.taken and selected
                branch.taken = branch.taken or selected
            elif kind == "else":
                if not stack:
                    raise ValueError("#else without #if")
                branch = stack[-1]
                branch.active = branch.parent_active and not branch.taken
                branch.taken = True
            elif kind == "endif":
                if not stack:
                    raise ValueError("#endif without #if")
                stack.pop()
            elif kind == "define" and active():
                parts = argument.split(None, 1)
                if parts and re.fullmatch(r"[A-Za-z_]\w*", parts[0]):
                    if len(parts) == 1:
                        macros.setdefault(parts[0], 1)
                    elif re.fullmatch(r"[-+]?\d+", parts[1].strip()):
                        macros.setdefault(parts[0], int(parts[1].strip(), 0))
            # Directives deliberately become a blank line: includes stay unresolved.
        except ValueError as exc:
            diagnostics.append(f"line {line_no}: {exc}")
        output.append("\n")
    if stack:
        diagnostics.append("unterminated conditional directive")
    return "".join(output), diagnostics


def strip_comments(text: str) -> str:
    return re.sub(r"/\*.*?\*/|//[^\n]*", " ", text, flags=re.S)


def matching_open(text: str, close_index: int, opening: str = "(", closing: str = ")") -> int:
    depth = 0
    for index in range(close_index, -1, -1):
        if text[index] == closing:
            depth += 1
        elif text[index] == opening:
            depth -= 1
            if depth == 0:
                return index
    return -1


def matching_close(text: str, open_index: int) -> int:
    depth = 0
    for index in range(open_index, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return index
    return -1


def extract_functions(text: str) -> Dict[str, Function]:
    clean = strip_comments(text)
    functions: Dict[str, Function] = {}
    depth = 0
    index = 0
    while index < len(clean):
        char = clean[index]
        if char == "{":
            if depth == 0:
                before = clean[:index].rstrip()
                close = len(before) - 1
                if close >= 0 and before[close] == ")":
                    open_paren = matching_open(before, close)
                    name_match = re.search(r"([A-Za-z_]\w*)\s*$", before[:open_paren]) if open_paren >= 0 else None
                    name = name_match.group(1) if name_match else ""
                    header = before[(max(before.rfind(";"), before.rfind("}")) + 1):]
                    if name and name not in KEYWORDS and "=" not in header and "#" not in header:
                        end = matching_close(clean, index)
                        if end >= 0:
                            params = clean[open_paren + 1:close]
                            raw = header + clean[index:end + 1]
                            functions[name] = Function(name, params, clean[index + 1:end], raw)
                            # The complete top-level function has been consumed.  Do
                            # not adjust `depth`: it was never entered by this scan.
                            index = end + 1
                            continue
            depth += 1
        elif char == "}":
            depth = max(0, depth - 1)
        index += 1
    return functions


def declared_names(params: str, body: str) -> Dict[str, str]:
    names: List[str] = []
    for part in params.split(","):
        candidates = IDENT.findall(part)
        if candidates:
            name = candidates[-1]
            if name not in TYPE_WORDS and name != "void":
                names.append(name)
    # A declaration can legally follow the closing brace of an if/while block;
    # treating only `;` and `{` as boundaries loses exactly that common shape.
    declaration = re.compile(r"(?:^|[;{}])\s*(?:[A-Za-z_]\w*\s+|\*\s*)+([A-Za-z_]\w*)\s*(?=[=;,\[])" )
    for match in declaration.finditer(body):
        if re.search(r"\b(return|goto|break|continue)\b", match.group(0)):
            continue
        name = match.group(1)
        if name not in TYPE_WORDS:
            names.append(name)
    result: Dict[str, str] = {}
    for name in names:
        result.setdefault(name, f"v{len(result)}")
    return result


def canonical(function: Function) -> str:
    rename = declared_names(function.params, function.body)
    tokens = TOKEN.findall(function.params + " { " + function.body + " }")
    canonical_tokens = [rename.get(token, token) for token in tokens]
    return " ".join(canonical_tokens)


def effects(function: Function) -> List[str]:
    tokens = TOKEN.findall(function.body)
    result: List[str] = []
    for index, token in enumerate(tokens[:-1]):
        if re.fullmatch(r"[A-Za-z_]\w*", token) and tokens[index + 1] == "(" and token not in KEYWORDS:
            result.append(token)
    return result


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:16]


def relation(before: Function, after: Function) -> Dict[str, object]:
    raw_before = " ".join(TOKEN.findall(before.raw))
    raw_after = " ".join(TOKEN.findall(after.raw))
    canon_before, canon_after = canonical(before), canonical(after)
    calls_before, calls_after = effects(before), effects(after)
    if raw_before == raw_after:
        kind, score = "IDENTICAL", 1.0
    elif canon_before == canon_after:
        kind, score = "STRUCTURALLY_EQUIVALENT", 1.0
    else:
        token_score = difflib.SequenceMatcher(None, canon_before.split(), canon_after.split(), autojunk=False).ratio()
        left, right = set(calls_before), set(calls_after)
        call_score = 1.0 if not left and not right else len(left & right) / len(left | right)
        score = round(0.75 * token_score + 0.25 * call_score, 3)
        kind = "LIKELY_EQUIVALENT" if score >= 0.90 else "SIMILAR" if score >= 0.55 else "DIFFERENT"
    return {
        "relation": kind, "score": score,
        "before_hash": digest(canon_before), "after_hash": digest(canon_after),
        "before_effects": calls_before, "after_effects": calls_after,
    }


def git_command(base_dir: Path, arguments: List[str]) -> str:
    result = subprocess.run(
        ["git", "-C", str(base_dir), *arguments], text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode:
        raise ValueError(result.stderr.strip() or "git command failed")
    return result.stdout


def split_git_location(location: str) -> Tuple[str, str]:
    try:
        return location[4:].split(":", 1)
    except ValueError as exc:
        raise ValueError("git input must be git:REVISION:path/to/file-or-directory") from exc


def source_files(location: str, base_dir: Path) -> List[Tuple[str, str]]:
    """Return local C files, or C blobs from a Git tree, without building anything."""
    if location.startswith("git:"):
        revision, path = split_git_location(location)
        names = git_command(base_dir, ["ls-tree", "-r", "--name-only", revision, "--", path]).splitlines()
        names = [name for name in names if name.endswith(".c")]
        if not names:
            raise ValueError(f"no C source files found in {location}")
        return [
            (name, git_command(base_dir, ["show", f"{revision}:{name}"]))
            for name in sorted(names)
        ]

    root = Path(location).expanduser()
    if not root.is_absolute():
        root = base_dir / root
    if root.is_file():
        files = [root]
    elif root.is_dir():
        files = sorted(root.rglob("*.c"))
    else:
        raise ValueError(f"source path does not exist: {root}")
    if not files:
        raise ValueError(f"no C source files found in {root}")
    return [(str(file.relative_to(base_dir)), file.read_text()) for file in files]


def function_summary(function: Function, local_functions: Dict[str, Function], call_depth: int, line_limit: int, enabled_hashes: Dict[str, bool] | None = None) -> Dict[str, object]:
    enabled_hashes = enabled_hashes or {name: True for name in HASH_FIELDS}
    raw = " ".join(TOKEN.findall(function.raw))
    normalized = canonical(function)
    semantic = semantic_lines(function, local_functions, call_depth, line_limit)
    semantic_fingerprint = {
        "bindings": semantic["bindings"],
        "static": semantic["static"],
        "temporal": semantic["temporal"],
        "truncated": semantic["truncated"],
    }
    result: Dict[str, object] = {
        "direct_effects": effects(function),
        "token_count": len(normalized.split()),
        "semantic": semantic,
    }
    if enabled_hashes["raw_hash"]:
        result["raw_hash"] = digest(raw)
    if enabled_hashes["structural_hash"]:
        result["structural_hash"] = digest(normalized)
    if enabled_hashes["semantic_hash"]:
        result["semantic_hash"] = digest(json.dumps(semantic_fingerprint, sort_keys=True, separators=(",", ":")))
    return result


def collect_functions(location: str, base_dir: Path, profile: Dict[str, int]) -> Dict[str, Tuple[Dict[str, Function], List[str]]]:
    collected: Dict[str, Tuple[Dict[str, Function], List[str]]] = {}
    for relative_path, source in source_files(location, base_dir):
        flattened, diagnostics = flatten(source, profile)
        collected[relative_path] = (extract_functions(flattened), diagnostics)
    return collected


def analyze_source(location: str, base_dir: Path, profile: Dict[str, int], call_depth: int, line_limit: int, enabled_hashes: Dict[str, bool] | None = None) -> Dict[str, object]:
    files: Dict[str, object] = {}
    collected = collect_functions(location, base_dir, profile)
    local_functions = function_index(collected)
    for relative_path, (functions, diagnostics) in collected.items():
        files[relative_path] = {
            "diagnostics": diagnostics,
            "functions": {
                name: function_summary(function, local_functions, call_depth, line_limit, enabled_hashes)
                for name, function in sorted(functions.items())
            },
        }
    return {
        "source": location,
        "base_dir": str(base_dir),
        "profile": profile,
        "scope": "source-only; includes and callees are intentionally opaque",
        "files": files,
    }


def source_label(location: str) -> str:
    path = split_git_location(location)[1] if location.startswith("git:") else location
    label = path.strip("/").replace("\\", "/").replace("/", "-")
    return label.removesuffix(".c") or "source"


def revision_location(revision: str, source_path: str) -> str:
    """Map a configured revision to a Git input or the current worktree."""
    return source_path if revision == "WORKTREE" else f"git:{revision}:{source_path}"


def unique_in_order(values: Iterable[str]) -> List[str]:
    return list(dict.fromkeys(values))


def clipped_diff(before: List[str], after: List[str], from_name: str, to_name: str, limit: int) -> Dict[str, object]:
    lines = list(difflib.unified_diff(before, after, fromfile=from_name, tofile=to_name, lineterm="", n=3))
    if len(lines) <= limit:
        return {"lines": lines, "truncated": False}
    return {
        "lines": lines[:limit] + [f"... {len(lines) - limit} more diff lines omitted; raise --max-diff-lines to see them"],
        "truncated": True,
    }


def token_close(tokens: List[str], index: int, opening: str, closing: str) -> int:
    depth = 0
    for position in range(index, len(tokens)):
        if tokens[position] == opening:
            depth += 1
        elif tokens[position] == closing:
            depth -= 1
            if depth == 0:
                return position
    return len(tokens) - 1


def canonical_body(function: Function) -> Tuple[List[str], set[str], Dict[str, str]]:
    rename = declared_names(function.params, function.body)
    bindings = {canonical: original for original, canonical in rename.items()}
    return [rename.get(token, token) for token in TOKEN.findall(function.body)], set(rename.values()), bindings


def expression_text(tokens: List[str]) -> str:
    """A stable, compact presentation of an expression; it is not a C pretty-printer."""
    return " ".join(tokens).strip()


def statement_end(tokens: List[str], start: int, end: int) -> int:
    parens = brackets = 0
    for position in range(start, end):
        token = tokens[position]
        parens += token == "("
        parens -= token == ")"
        brackets += token == "["
        brackets -= token == "]"
        if token == ";" and not parens and not brackets:
            return position + 1
    return end


def local_write_counts(tokens: List[str], local_names: set[str]) -> Dict[str, int]:
    """Count direct assignments so mutable locals are never folded as aliases."""
    counts: Dict[str, int] = {name: 0 for name in local_names}
    for index, token in enumerate(tokens):
        if token not in {"=", "+=", "-=", "*=", "/=", "%="}:
            continue
        for candidate in reversed(tokens[max(0, index - 12):index]):
            if candidate in local_names:
                counts[candidate] += 1
                break
    return counts


def parameter_aliases(function: Function) -> set[str]:
    """Return non-volatile parameter names after local-name normalization."""
    rename = declared_names(function.params, function.body)
    result: set[str] = set()
    for part in function.params.split(","):
        if "volatile" in IDENT.findall(part):
            continue
        candidates = IDENT.findall(part)
        if candidates:
            name = candidates[-1]
            if name not in TYPE_WORDS and name != "void":
                result.add(rename[name])
    return result


def apply_semantic_rules(function: Function, tokens: List[str], local_names: set[str], write_counts: Dict[str, int]) -> SemanticRuleResult:
    """合并动态规则的结果；冲突时由 dead 初始化过滤优先。"""
    context = SemanticRuleContext(
        function_params=function.params,
        tokens=tokens,
        local_names=local_names,
        parameter_names=parameter_aliases(function),
        write_counts=write_counts,
    )
    combined = SemanticRuleResult()
    for rule in semantic_rules():
        result = rule.apply(context)
        if not isinstance(result, SemanticRuleResult):
            raise ValueError(f"rule {rule.name} must return SemanticRuleResult")
        combined.dead_initializers.update(result.dead_initializers)
        combined.static_initializers.update(result.static_initializers)
        combined.condition_aliases.update(result.condition_aliases)
    return combined


def semantic_lines(function: Function, local_functions: Dict[str, Function], call_depth: int, line_limit: int) -> Dict[str, object]:
    """Build a flat, alphabetically ordered view of reachable local functions."""
    tokens, local_names, bindings = canonical_body(function)
    lines: List[str] = []
    static_entries: List[Tuple[str, str]] = []
    truncated = False

    def reachable_functions() -> List[str]:
        """Delegate reachability and display order to dynamically loaded rules."""
        discovered = function_discovery_rule().discover(FunctionDiscoveryContext(
            root_name=function.name,
            call_depth=call_depth,
            local_function_names=set(local_functions),
            direct_effects=lambda name: unique_in_order(effects(local_functions[name])),
        ))
        return function_order_rule().order(discovered)

    def emit(indent: int, text: str) -> None:
        nonlocal truncated
        if len(lines) >= line_limit:
            truncated = True
            return
        lines.append("  " * indent + text)

    def render(items: List[str], aliases: Dict[str, List[str]]) -> str:
        rendered: List[str] = []
        for item in items:
            rendered.extend(aliases.get(item, [item]))
        return expression_text(rendered)

    def simple_statement(part: List[str], indent: int, remaining_depth: int, active_local_names: set[str], aliasable: set[str], aliases: Dict[str, List[str]], dead_initializers: set[str], static_initializers: Dict[str, str], condition_aliases: Dict[str, List[str]], deferred_types: Dict[str, str], collect_static: bool) -> None:
        if not part:
            return
        if part[0] == "return":
            emit(indent, f"RETURN {render(part[1:], aliases) or 'void'}")
        assignment = next((i for i, token in enumerate(part) if token in {"=", "+=", "-=", "*=", "/=", "%="}), None)
        if assignment is not None:
            left = expression_text(part[:assignment])
            left_names = [token for token in part[:assignment] if re.fullmatch(r"[A-Za-z_]\w*", token)]
            local_targets = [name for name in left_names if name in active_local_names]
            kind = "SET_LOCAL" if local_targets else "WRITE_STATE"
            right = part[assignment + 1:]
            target = local_targets[-1] if local_targets else ""
            is_declaration = bool(target and part[:assignment] and part[assignment - 1] == target and len(part[:assignment]) > 1)
            if kind == "SET_LOCAL" and is_declaration and target in dead_initializers:
                dead_initializers.remove(target)
                deferred_types[target] = left[:left.rfind(target)].rstrip()
                return
            if kind == "SET_LOCAL" and is_declaration and target in static_initializers:
                if collect_static:
                    static_entries.append((bindings.get(target, target), f"STATIC_LOCAL {bindings.get(target, target)} [{target}] = {static_initializers[target]}"))
                return
            if kind == "SET_LOCAL" and not is_declaration and target in condition_aliases:
                return
            if kind == "SET_LOCAL" and not is_declaration and target in deferred_types:
                left = f"{deferred_types.pop(target)} {target}"
            if kind == "SET_LOCAL" and is_declaration and target in aliasable and len(right) == 1:
                aliases[target] = aliases.get(right[0], [right[0]])
                alias_kind = "CONST" if re.fullmatch(r"(?:0[xX][0-9a-fA-F]+|\d+)", right[0]) else "ALIAS"
                emit(indent, f"{alias_kind} {target} := {render(right, aliases)}")
            else:
                emit(indent, f"{kind} {left} {part[assignment]} {render(right, aliases)}")
        position = 0
        while position < len(part) - 1:
            name = part[position]
            if re.fullmatch(r"[A-Za-z_]\w*", name) and part[position + 1] == "(" and name not in KEYWORDS:
                close = token_close(part, position + 1, "(", ")")
                arguments = render(part[position + 2:close], aliases)
                classification = call_classification_rule().classify(CallClassificationContext(
                    call_name=name,
                    local_function_names=set(local_functions),
                ))
                if classification == "LOCAL":
                    emit(indent, f"CALL_LOCAL {name}({arguments})")
                elif classification == "EXTERNAL":
                    emit(indent, f"CALL_EXTERNAL {name}({arguments})")
                else:
                    raise ValueError(f"call classification rule returned unsupported value: {classification!r}")
                position = close
            position += 1

    def walk_range(items: List[str], start: int, end: int, indent: int, remaining_depth: int, active_local_names: set[str], aliasable: set[str], aliases: Dict[str, List[str]], dead_initializers: set[str], static_initializers: Dict[str, str], condition_aliases: Dict[str, List[str]], deferred_types: Dict[str, str], collect_static: bool) -> None:
        position = start
        while position < end and not truncated:
            token = items[position]
            if token in {";", "{" , "}"}:
                position += 1
                continue
            if token in {"if", "while", "for", "switch"} and position + 1 < end and items[position + 1] == "(":
                close = token_close(items, position + 1, "(", ")")
                condition = items[position + 2:close]
                if token == "if" and len(condition) == 1 and condition[0] in condition_aliases:
                    condition = condition_aliases.pop(condition[0])
                emit(indent, f"{token.upper()} {render(condition, aliases)}")
                body_start = close + 1
                if body_start < end and items[body_start] == "{":
                    body_end = token_close(items, body_start, "{", "}")
                    walk_range(items, body_start + 1, min(body_end, end), indent + 1, remaining_depth, active_local_names, aliasable, aliases, dead_initializers, static_initializers, condition_aliases, deferred_types, collect_static)
                    position = body_end + 1
                else:
                    body_end = statement_end(items, body_start, end)
                    walk_range(items, body_start, body_end, indent + 1, remaining_depth, active_local_names, aliasable, aliases, dead_initializers, static_initializers, condition_aliases, deferred_types, collect_static)
                    position = body_end
                continue
            if token == "else":
                emit(indent, "ELSE")
                position += 1
                continue
            finish = statement_end(items, position, end)
            simple_statement(items[position:finish - 1] if finish > position and items[finish - 1] == ";" else items[position:finish], indent, remaining_depth, active_local_names, aliasable, aliases, dead_initializers, static_initializers, condition_aliases, deferred_types, collect_static)
            position = max(finish, position + 1)

    def walk_function(target: Function, indent: int, remaining_depth: int, collect_static: bool) -> None:
        target_tokens, target_local_names, _ = canonical_body(target)
        writes = local_write_counts(target_tokens, target_local_names)
        aliasable = {name for name, count in writes.items() if count == 1}
        rule_result = apply_semantic_rules(target, target_tokens, target_local_names, writes)
        unused_initializers = rule_result.dead_initializers
        static_initializers = rule_result.static_initializers if collect_static else {}
        condition_aliases = dict(rule_result.condition_aliases)
        deferred_types: Dict[str, str] = {}
        walk_range(target_tokens, 0, len(target_tokens), indent, remaining_depth, target_local_names, aliasable, {}, unused_initializers, static_initializers, condition_aliases, deferred_types, collect_static)

    for name in reachable_functions():
        emit(0, f"FUNCTION {name}")
        # Each function is analyzed independently. Only the root function's
        # static bindings are exported because they define this report's
        # top-level binding map.
        walk_function(local_functions[name], 1, call_depth, name == function.name)
    if truncated:
        lines.append(f"... semantic expansion truncated at {line_limit} lines")
    display_bindings = {name: identifier for identifier, name in bindings.items()}
    return {
        "bindings": dict(sorted(display_bindings.items())),
        "static": [entry for _, entry in sorted(static_entries)],
        "temporal": lines,
        "truncated": truncated,
    }


def compare_functions(before: Function, after: Function, before_local: Dict[str, Function], after_local: Dict[str, Function], limit: int, call_depth: int, enabled_hashes: Dict[str, bool] | None = None) -> Dict[str, object]:
    enabled_hashes = enabled_hashes or {name: True for name in HASH_FIELDS}
    raw_before = " ".join(TOKEN.findall(before.raw))
    raw_after = " ".join(TOKEN.findall(after.raw))
    structural_before, structural_after = canonical(before), canonical(after)
    raw_equal = raw_before == raw_after
    structural_equal = structural_before == structural_after
    if raw_equal:
        kind = "IDENTICAL"
    elif structural_equal:
        kind = "STRUCTURALLY_EQUIVALENT"
    else:
        kind = "CHANGED"
    result: Dict[str, object] = {"relation": kind}
    if enabled_hashes["raw_hash"]:
        result["raw_hash"] = {"before": digest(raw_before), "after": digest(raw_after), "equal": raw_equal}
    if enabled_hashes["structural_hash"]:
        result["structural_hash"] = {"before": digest(structural_before), "after": digest(structural_after), "equal": structural_equal}
    if kind != "IDENTICAL":
        before_effects, after_effects = effects(before), effects(after)
        result["direct_effects"] = {
            "before": before_effects,
            "after": after_effects,
            "added": [item for item in unique_in_order(after_effects) if item not in set(before_effects)],
            "removed": [item for item in unique_in_order(before_effects) if item not in set(after_effects)],
        }
        semantic_before = semantic_lines(before, before_local, call_depth, limit)
        semantic_after = semantic_lines(after, after_local, call_depth, limit)
        result["semantic_a"] = semantic_before
        result["semantic_b"] = semantic_after
        result["semantic_diff"] = clipped_diff(
            semantic_before["static"] + semantic_before["temporal"],
            semantic_after["static"] + semantic_after["temporal"], "A/behavior", "B/behavior", limit
        )
    return result


def function_index(collected: Dict[str, Tuple[Dict[str, Function], List[str]]]) -> Dict[str, Function]:
    index: Dict[str, Function] = {}
    for functions, _ in collected.values():
        for name, function in functions.items():
            index.setdefault(name, function)
    return index


def compare_sources(before_location: str, after_location: str, base_dir: Path, profile: Dict[str, int], limit: int, call_depth: int, enabled_hashes: Dict[str, bool] | None = None) -> Dict[str, object]:
    before = collect_functions(before_location, base_dir, profile)
    after = collect_functions(after_location, base_dir, profile)
    before_local, after_local = function_index(before), function_index(after)
    keys = sorted({(path, name) for path, item in before.items() for name in item[0]} |
                  {(path, name) for path, item in after.items() for name in item[0]})
    functions: Dict[str, object] = {}
    counts: Dict[str, int] = {}
    for path, name in keys:
        before_function = before.get(path, ({}, []))[0].get(name)
        after_function = after.get(path, ({}, []))[0].get(name)
        function_key = f"{path}:{name}"
        if before_function is None:
            item: Dict[str, object] = {"relation": "ADDED", "after_source": after_function.raw}
        elif after_function is None:
            item = {"relation": "REMOVED", "before_source": before_function.raw}
        else:
            item = compare_functions(before_function, after_function, before_local, after_local, limit, call_depth, enabled_hashes)
        functions[function_key] = item
        counts[item["relation"]] = counts.get(item["relation"], 0) + 1
    diagnostics = {
        "before": {path: item[1] for path, item in before.items() if item[1]},
        "after": {path: item[1] for path, item in after.items() if item[1]},
    }
    return {
        "before": before_location,
        "after": after_location,
        "base_dir": str(base_dir),
        "profile": profile,
        "scope": "source-only; includes and callees are intentionally opaque",
        "summary": counts,
        "diagnostics": diagnostics,
        "functions": functions,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    default_config = Path(__file__).with_name("config.yaml")
    parser.add_argument("--config", type=Path, default=default_config, help="default: config.yaml next to this script")
    args = parser.parse_args()
    try:
        config_file = args.config.expanduser().resolve()
        config = load_config(config_file)
        base_dir = config_path(config["base_dir"], config_file).resolve()
        profile_file = config_path(config["profile"], config_file).resolve()
        output_dir = config_path(config.get("output_dir", "outputs"), config_file)
        before_location = revision_location(config["before"], config["source_path"])
        after_location = revision_location(config["after"], config["source_path"])
        call_depth = int(config.get("call_depth", "2"))
        max_semantic_lines = int(config.get("max_semantic_lines", "160"))
        enabled_hashes = hash_options(config)
        if call_depth < 0 or max_semantic_lines < 1:
            raise ValueError("call_depth must be >= 0 and max_semantic_lines must be >= 1")
        profile = load_profile(profile_file)
        before = analyze_source(before_location, base_dir, profile, call_depth, max_semantic_lines, enabled_hashes)
        after = analyze_source(after_location, base_dir, profile, call_depth, max_semantic_lines, enabled_hashes)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    output_dir.mkdir(parents=True, exist_ok=True)
    before_output = output_dir / "before.json"
    after_output = output_dir / "after.json"
    before_output.write_text(json.dumps(before, indent=2, sort_keys=True) + "\n")
    after_output.write_text(json.dumps(after, indent=2, sort_keys=True) + "\n")
    print(f"before: {before_output}")
    print(f"after:  {after_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
