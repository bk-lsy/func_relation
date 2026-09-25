#!/usr/bin/env python3
"""Generate AC/BC commit graphs for every task under branch_diff/.

Each directory containing scope.json is one task. Git refs and the focal path
come from that task's scope.json. Unique commits are discovered from each
repository's merge base on every run. dependencies.json contains manually
reviewed merge dependencies (information 1), while equivalent_pairs.json
contains candidate AC/BC equivalents (information 2).
"""

from __future__ import annotations

import argparse
import html
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Repo:
    name: str
    path: Path
    ac_ref: str
    bc_ref: str


@dataclass
class Commit:
    repo: str
    oid: str
    date: str
    subject: str
    side: str
    focal: bool = False

    @property
    def key(self) -> str:
        return f"{self.repo}:{self.oid}"

    @property
    def short(self) -> str:
        return self.oid[:10]


def git(repo: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if result.returncode:
        raise ValueError(f"git -C {repo} {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def load_repos(scope: dict, root: Path) -> dict[str, Repo]:
    repos: dict[str, Repo] = {}
    for item in scope["repositories"]:
        path = Path(item["path"])
        if not path.is_absolute():
            path = (root / path).resolve()
        repo = Repo(item["name"], path, item["ac_ref"], item["bc_ref"])
        git(path, ["rev-parse", "--git-dir"])
        repos[repo.name] = repo
    return repos


def resolve(repos: dict[str, Repo], ref: dict) -> str:
    return git(repos[ref["repo"]].path, ["rev-parse", ref["commit"]]).strip()


def commit_info(repo: Repo, oid: str, side: str, focal: bool = False) -> Commit:
    raw = git(repo.path, ["show", "-s", "--format=%H%x1f%aI%x1f%s", oid]).strip()
    full, date, subject = raw.split("\x1f", 2)
    return Commit(repo.name, full, date[:10], subject, side, focal)


def unique_commits(repo: Repo, side: str, paths: list[str]) -> tuple[str, list[Commit]]:
    ref = repo.ac_ref if side == "AC" else repo.bc_ref
    base = git(repo.path, ["merge-base", repo.ac_ref, repo.bc_ref]).strip()
    oids = git(
        repo.path,
        ["rev-list", "--reverse", "--topo-order", "--no-merges", f"{base}..{ref}", "--", *paths],
    ).splitlines()
    return base, [commit_info(repo, oid, side, focal=True) for oid in oids]


def projected_branch_edges(repo: Repo, side: str, base: str, commits: list[Commit]) -> list[dict]:
    """Collapse the full Git DAG to edges between the nearest focal commits."""
    ref = repo.ac_ref if side == "AC" else repo.bc_ref
    parent_map: dict[str, list[str]] = {}
    for line in git(repo.path, ["rev-list", "--parents", f"{base}..{ref}"]).splitlines():
        fields = line.split()
        parent_map[fields[0]] = fields[1:]
    selected = {commit.oid for commit in commits}
    edges: set[tuple[str, str]] = set()
    for child in selected:
        pending = list(parent_map.get(child, []))
        seen: set[str] = set()
        while pending:
            candidate = pending.pop()
            if candidate in seen or candidate == base:
                continue
            seen.add(candidate)
            if candidate in selected:
                edges.add((candidate, child))
                continue
            pending.extend(parent_map.get(candidate, []))
    order = {commit.oid: index for index, commit in enumerate(commits)}
    return [
        {"parent": f"{repo.name}:{parent}", "child": f"{repo.name}:{child}"}
        for parent, child in sorted(edges, key=lambda edge: (order[edge[1]], order[edge[0]]))
    ]


def load_pairs(data: dict, repos: dict[str, Repo]) -> tuple[list[dict], dict[str, dict]]:
    pairs: list[dict] = []
    by_key: dict[str, dict] = {}
    for index, pair in enumerate(data.get("pairs", []), 1):
        confirm = pair.get("confirm")
        if confirm not in (0, 1):
            raise ValueError(f"equivalent pair {index}: confirm must be 0 or 1")
        ac_oid, bc_oid = resolve(repos, pair["ac"]), resolve(repos, pair["bc"])
        normalized = {
            "id": f"pair-{index}",
            "ac": {"repo": pair["ac"]["repo"], "commit": ac_oid},
            "bc": {"repo": pair["bc"]["repo"], "commit": bc_oid},
            "basis": pair.get("basis", ""),
            "confirm": confirm,
        }
        pairs.append(normalized)
        by_key[f"{normalized['ac']['repo']}:{ac_oid}"] = normalized
        by_key[f"{normalized['bc']['repo']}:{bc_oid}"] = normalized
    return pairs, by_key


def load_dependencies(data: dict, repos: dict[str, Repo]) -> dict[str, dict]:
    dependencies: dict[str, dict] = {}
    for index, item in enumerate(data.get("dependencies", []), 1):
        side = item["source"]["side"]
        if side not in ("AC", "BC") or item["target_side"] == side:
            raise ValueError(f"dependency {index}: invalid source/target side")
        source_oid = resolve(repos, item["source"])
        source_key = f"{item['source']['repo']}:{source_oid}"
        if source_key in dependencies:
            raise ValueError(f"duplicate dependency source: {source_key}")
        required = []
        for dependency in item.get("required_commits", []):
            required.append({
                "repo": dependency["repo"],
                "commit": resolve(repos, dependency),
                "reason": dependency.get("reason", ""),
            })
        dependencies[source_key] = {
            "source_side": side,
            "target_side": item["target_side"],
            "required_commits": required,
            "external_requirements": item.get("external_requirements", []),
        }
    return dependencies


def load_annotations(scope: dict, repos: dict[str, Repo]) -> dict[str, dict]:
    annotations = {}
    for item in scope.get("annotations", []):
        oid = resolve(repos, item)
        annotations[f"{item['repo']}:{oid}"] = {"tag": item["tag"], "note": item.get("note", "")}
    return annotations


def side_report(
    side: str,
    focal: list[Commit],
    repos: dict[str, Repo],
    dependencies: dict[str, dict],
    pair_by_key: dict[str, dict],
    annotations: dict[str, dict],
    merge_base: str,
    branch_edges: list[dict],
) -> dict:
    focal_by_key = {commit.key: commit for commit in focal}
    selected: dict[str, Commit] = dict(focal_by_key)
    adjacency: dict[str, list[tuple[str, str, str]]] = {}
    external_labels: dict[str, str] = {}

    for source_key, relation in dependencies.items():
        if relation["source_side"] != side or source_key not in focal_by_key:
            continue
        children = []
        for dependency in relation["required_commits"]:
            repo = repos[dependency["repo"]]
            commit = commit_info(repo, dependency["commit"], side, focal=False)
            selected[commit.key] = commit
            children.append((commit.key, "commit", dependency["reason"]))
        for index, requirement in enumerate(relation["external_requirements"], 1):
            key = f"external:{source_key}:{index}"
            external_labels[key] = requirement
            children.append((key, "external", requirement))
        adjacency[source_key] = children

    traversal: list[dict] = []
    visited: set[str] = set()

    def visit(key: str, depth: int, parent: str | None, reason: str) -> None:
        if key in visited:
            return
        visited.add(key)
        if key.startswith("external:"):
            traversal.append({
                "rank": len(traversal) + 1, "type": "external", "key": key,
                "label": external_labels[key], "depth": depth, "parent": parent,
                "reason": reason,
            })
            return
        commit = selected[key]
        pair = pair_by_key.get(key)
        counterpart = None
        if pair:
            counterpart = pair["bc"] if side == "AC" else pair["ac"]
        traversal.append({
            "rank": len(traversal) + 1, "type": "commit", "key": key,
            "repo": commit.repo, "commit": commit.oid, "short": commit.short,
            "date": commit.date, "subject": commit.subject, "side": side,
            "focal": commit.focal, "depth": depth, "parent": parent,
            "reason": reason, "annotation": annotations.get(key),
            "equivalent_pair": None if not pair else {
                "id": pair["id"], "confirm": pair["confirm"],
                "basis": pair["basis"], "counterpart": counterpart,
            },
        })
        for child, _, child_reason in adjacency.get(key, []):
            visit(child, depth + 1, key, child_reason)

    for commit in focal:
        visit(commit.key, 0, None, "branch-unique focal commit")

    return {
        "side": side,
        "merge_base": merge_base,
        "unique_commit_count": len(focal),
        "strategy": "dynamic branch difference, then depth-first dependencies",
        "branch_edges": branch_edges,
        "commits": [
            {
                "key": commit.key, "repo": commit.repo, "commit": commit.oid,
                "short": commit.short, "date": commit.date,
                "subject": commit.subject, "focal": commit.focal,
            }
            for commit in selected.values()
        ],
        "analysis_order": traversal,
    }


def render_svg(report: dict, title: str) -> str:
    steps = report["analysis_order"]
    width, row_h = 1540, 92
    height = 100 + len(steps) * row_h + 40
    side_color = "#dbeafe" if report["side"] == "AC" else "#ffedd5"
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<style>text{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;fill:#111827}.title{font-size:22px;font-weight:700}.meta{font-size:11px;fill:#374151}.subject{font-size:12px}.branch{stroke:#2563eb;stroke-width:1.8;fill:none}.dep{stroke:#dc2626;stroke-width:1.8;fill:none}.node{stroke:#9ca3af;stroke-width:1}</style>',
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0L10 5L0 10z" fill="#dc2626"/></marker></defs>',
        f'<text x="24" y="34" class="title">{html.escape(title)} · {report["side"]} 独有提交图</text>',
        f'<text x="24" y="58" class="meta">动态独有提交 {report["unique_commit_count"]} 个；蓝线=Git祖先拓扑，红线=信息1依赖；PAIR confirm=0 为待人工确认。</text>',
    ]
    positions: dict[str, tuple[int, int]] = {}
    for index, item in enumerate(steps):
        y = 82 + index * row_h
        x = 40 + item["depth"] * 300
        positions[item["key"]] = (x, y)
        if item["parent"] and item["parent"] in positions:
            px, py = positions[item["parent"]]
            out.append(f'<path class="dep" marker-end="url(#arrow)" d="M {px+270} {py+34} C {px+285} {py+34}, {x-15} {y+34}, {x} {y+34}"/>')
        if item["type"] == "external":
            fill, stroke_dash = "#f3f4f6", ' stroke-dasharray="5 4"'
            heading, subject = "EXTERNAL", item["label"]
        else:
            annotation = item.get("annotation")
            fill = "#e5e7eb" if annotation and annotation["tag"] == "excluded-pilot" else side_color if item["focal"] else "#dcfce7"
            stroke_dash = ' stroke-dasharray="5 4"' if annotation else ""
            pair = item.get("equivalent_pair")
            pair_text = f" · PAIR confirm={pair['confirm']}" if pair else ""
            heading = f"DFS #{item['rank']} · {item['repo']} · {item['short']}{pair_text}"
            subject = item["subject"]
        out.append(f'<rect class="node" x="{x}" y="{y}" width="270" height="68" rx="8" fill="{fill}"{stroke_dash}/>')
        out.append(f'<text x="{x+10}" y="{y+18}" class="meta">{html.escape(heading)}</text>')
        first = subject[:40] + ("…" if len(subject) > 40 else "")
        second = subject[40:80] + ("…" if len(subject) > 80 else "")
        out.append(f'<text x="{x+10}" y="{y+39}" class="subject">{html.escape(first)}</text>')
        if second:
            out.append(f'<text x="{x+10}" y="{y+56}" class="subject">{html.escape(second)}</text>')
        if item["type"] == "commit" and item.get("annotation"):
            note = item["annotation"]["note"][:54]
            out.append(f'<text x="{x+285}" y="{y+36}" class="meta">{html.escape(note)}</text>')
    for edge in report.get("branch_edges", []):
        if edge["parent"] not in positions or edge["child"] not in positions:
            continue
        _, py = positions[edge["parent"]]
        _, cy = positions[edge["child"]]
        out.insert(5, f'<path class="branch" d="M 40 {py+34} C 18 {py+34}, 18 {cy+34}, 40 {cy+34}"/>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def write_side(report: dict, title: str, output_dir: Path) -> None:
    prefix = report["side"].lower() + "-unique"
    (output_dir / f"{prefix}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    (output_dir / f"{prefix}.svg").write_text(render_svg(report, title))
    lines = []
    for item in report["analysis_order"]:
        indent = "  " * item["depth"]
        label = f"{item['repo']} {item['short']} {item['subject']}" if item["type"] == "commit" else f"EXTERNAL {item['label']}"
        lines.append(f"{item['rank']:03d} {indent}{label}")
    (output_dir / f"{prefix}-order.txt").write_text("\n".join(lines) + "\n")


def generate_task(task_root: Path, output_dir: Path) -> tuple[dict, dict]:
    scope = read_json(task_root / "scope.json")
    repos = load_repos(scope, task_root)
    dependencies = load_dependencies(read_json(task_root / "dependencies.json"), repos)
    pairs, pair_by_key = load_pairs(read_json(task_root / "equivalent_pairs.json"), repos)
    annotations = load_annotations(scope, repos)
    anchor = scope["anchor"]
    anchor_repo = repos[anchor["repository"]]
    ac_base, ac = unique_commits(anchor_repo, "AC", anchor["paths"])
    bc_base, bc = unique_commits(anchor_repo, "BC", anchor["paths"])
    if ac_base != bc_base:
        raise ValueError("AC and BC merge-base mismatch")
    ac_keys, bc_keys = {item.key for item in ac}, {item.key for item in bc}
    for source_key, relation in dependencies.items():
        expected = ac_keys if relation["source_side"] == "AC" else bc_keys
        if source_key not in expected:
            raise ValueError(f"dependency source is not a dynamic focal unique commit: {source_key}")
    for pair in pairs:
        ac_key = f"{pair['ac']['repo']}:{pair['ac']['commit']}"
        bc_key = f"{pair['bc']['repo']}:{pair['bc']['commit']}"
        if ac_key not in ac_keys or bc_key not in bc_keys:
            raise ValueError(f"{pair['id']}: pair members must be dynamic focal unique commits")
    ac_edges = projected_branch_edges(anchor_repo, "AC", ac_base, ac)
    bc_edges = projected_branch_edges(anchor_repo, "BC", bc_base, bc)
    ac_report = side_report("AC", ac, repos, dependencies, pair_by_key, annotations, ac_base, ac_edges)
    bc_report = side_report("BC", bc, repos, dependencies, pair_by_key, annotations, bc_base, bc_edges)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_side(ac_report, scope["title"], output_dir)
    write_side(bc_report, scope["title"], output_dir)
    return ac_report, bc_report


def discover_tasks(branch_diff_root: Path) -> list[Path]:
    return sorted(path.parent for path in branch_diff_root.rglob("scope.json"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    script_root = Path(__file__).resolve().parent
    parser.add_argument("--branch-diff-root", type=Path, default=script_root / "branch_diff")
    parser.add_argument("--output-root", type=Path, default=script_root / "outputs" / "branch_diff")
    args = parser.parse_args()
    branch_diff_root = args.branch_diff_root.expanduser().resolve()
    output_root = args.output_root.expanduser().resolve()
    tasks = discover_tasks(branch_diff_root)
    if not tasks:
        raise ValueError(f"no branch-diff tasks found under {branch_diff_root}")
    for task_root in tasks:
        relative = task_root.relative_to(branch_diff_root)
        output_dir = output_root / relative
        ac, bc = generate_task(task_root, output_dir)
        print(f"[{relative}] AC SVG: {output_dir / 'ac-unique.svg'} ({ac['unique_commit_count']} unique commits)")
        print(f"[{relative}] BC SVG: {output_dir / 'bc-unique.svg'} ({bc['unique_commit_count']} unique commits)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
