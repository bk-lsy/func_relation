#!/usr/bin/env python3
"""Generate AC/BC commit graphs for every task under branch_diff/.

Each directory containing scope.json is one task. Git refs and the focal path
come from that task's scope.json. Physically unique focal commits are discovered
from the opposite tip with full path history on every run. dependencies.json contains manually
reviewed merge dependencies (information 1), while equivalent_pairs.json
contains candidate AC/BC pairs and many-to-many final-behavior equivalence groups
(information 2). relation_confirms.json
stores the confirmation state of each directed commit dependency.
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
    opposite = repo.bc_ref if side == "AC" else repo.ac_ref
    base = git(repo.path, ["merge-base", repo.ac_ref, repo.bc_ref]).strip()
    oids = git(
        repo.path,
        ["rev-list", "--full-history", "--reverse", "--topo-order", "--no-merges", f"{opposite}..{ref}", "--", *paths],
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


def load_equivalence_groups(data: dict, repos: dict[str, Repo]) -> tuple[list[dict], dict[str, list[dict]]]:
    """One or more physical commits on each side may implement one final behavior."""
    groups: list[dict] = []
    by_key: dict[str, list[dict]] = {}
    for index, item in enumerate(data.get("groups", []), 1):
        if item.get("confirm") not in (0, 1):
            raise ValueError(f"equivalence group {index}: confirm must be 0 or 1")
        if item["confirm"] == 1 and not all(
            item.get(field) for field in ("scope", "conditions", "final_state_evidence")
        ):
            raise ValueError(
                f"equivalence group {index}: confirmed groups require scope, conditions, and final_state_evidence"
            )
        members = {}
        for side in ("ac", "bc"):
            refs = item.get(f"{side}_commits", [])
            if not refs:
                raise ValueError(f"equivalence group {index}: {side}_commits must be nonempty")
            resolved = [{"repo": ref["repo"], "commit": resolve(repos, ref)} for ref in refs]
            keys = [f"{ref['repo']}:{ref['commit']}" for ref in resolved]
            if len(keys) != len(set(keys)):
                raise ValueError(f"equivalence group {index}: duplicate {side} member")
            members[side] = resolved
        group = {
            "id": f"group-{index}",
            "ac_commits": members["ac"],
            "bc_commits": members["bc"],
            "scope": item.get("scope", []),
            "conditions": item.get("conditions", []),
            "basis": item.get("basis", ""),
            "final_state_evidence": item.get("final_state_evidence", []),
            "open_questions": item.get("open_questions", []),
            "confirm": item["confirm"],
        }
        groups.append(group)
        for side in ("ac", "bc"):
            for ref in members[side]:
                by_key.setdefault(f"{ref['repo']}:{ref['commit']}", []).append(group)
    return groups, by_key


def load_relation_confirms(data: dict, repos: dict[str, Repo]) -> dict[str, dict]:
    confirmations: dict[str, dict] = {}
    for section in ("ac", "bc"):
        side = section.upper()
        for index, item in enumerate(data.get(section, []), 1):
            confirm = item.get("relation_confirm")
            if confirm not in (0, 1):
                raise ValueError(
                    f"{section} relation {index}: relation_confirm must be 0 or 1"
                )
            source_oid = resolve(repos, item["source"])
            source_key = f"{item['source']['repo']}:{source_oid}"
            if source_key in confirmations:
                raise ValueError(f"duplicate relation confirmation source: {source_key}")
            related_chain = []
            for related in item.get("related_chain", []):
                related_oid = resolve(repos, related)
                related_chain.append(f"{related['repo']}:{related_oid}")
            confirmations[source_key] = {
                "side": side,
                "source": source_key,
                "related_chain": related_chain,
                "relation_confirm": confirm,
            }
    return confirmations


def load_dependencies(
    data: dict,
    repos: dict[str, Repo],
    relation_confirms: dict[str, dict],
) -> dict[str, dict]:
    dependencies: dict[str, dict] = {}
    for index, item in enumerate(data.get("dependencies", []), 1):
        side = item["source"]["side"]
        if side not in ("AC", "BC") or item["target_side"] == side:
            raise ValueError(f"dependency {index}: invalid source/target side")
        source_oid = resolve(repos, item["source"])
        source_key = f"{item['source']['repo']}:{source_oid}"
        if source_key in dependencies:
            raise ValueError(f"duplicate dependency source: {source_key}")
        confirmation = relation_confirms.get(source_key)
        if not confirmation or confirmation["side"] != side:
            raise ValueError(f"missing {side} relation confirmation: {source_key}")
        required = []
        related_chain = []
        for dependency in item.get("required_commits", []):
            related_oid = resolve(repos, dependency)
            related_chain.append(f"{dependency['repo']}:{related_oid}")
            required.append({
                "repo": dependency["repo"],
                "commit": related_oid,
                "reason": dependency.get("reason", ""),
            })
        if related_chain != confirmation["related_chain"]:
            raise ValueError(f"related chain mismatch: {source_key}")
        dependencies[source_key] = {
            "source_side": side,
            "target_side": item["target_side"],
            "required_commits": required,
            "external_requirements": item.get("external_requirements", []),
        }
    for source_key, confirmation in relation_confirms.items():
        if source_key not in dependencies and confirmation["related_chain"]:
            raise ValueError(f"related chain has no dependency definition: {source_key}")
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
    relation_confirms: dict[str, dict],
    pair_by_key: dict[str, dict],
    annotations: dict[str, dict],
    merge_base: str,
    branch_edges: list[dict],
    equivalence_groups: list[dict] | None = None,
    group_by_key: dict[str, list[dict]] | None = None,
) -> dict:
    equivalence_groups = equivalence_groups or []
    group_by_key = group_by_key or {}
    focal_by_key = {commit.key: commit for commit in focal}
    selected: dict[str, Commit] = dict(focal_by_key)
    adjacency: dict[str, list[tuple[str, str, str, int | None]]] = {}
    external_labels: dict[str, str] = {}
    dependency_relations: list[dict] = []

    for source_key, relation in dependencies.items():
        if relation["source_side"] != side or source_key not in focal_by_key:
            continue
        children = []
        for dependency in relation["required_commits"]:
            dependency_key = f"{dependency['repo']}:{dependency['commit']}"
            if dependency_key in selected:
                commit = selected[dependency_key]
            else:
                repo = repos[dependency["repo"]]
                commit = commit_info(repo, dependency["commit"], side, focal=False)
                selected[commit.key] = commit
            children.append((
                commit.key, "commit", dependency["reason"],
                None,
            ))
            confirmation = relation_confirms[source_key]
            dependency_relations.append({
                "source": source_key, "related": commit.key,
                "reason": dependency["reason"],
                "relation_confirm": confirmation["relation_confirm"],
            })
        for index, requirement in enumerate(relation["external_requirements"], 1):
            key = f"external:{source_key}:{index}"
            external_labels[key] = requirement
            children.append((key, "external", requirement, None))
        adjacency[source_key] = children

    traversal: list[dict] = []
    visited: set[str] = set()
    focal_numbers = {commit.key: index for index, commit in enumerate(focal, 1)}
    dependency_numbers = {index: 0 for index in focal_numbers.values()}

    def next_dependency_id(group: int) -> str:
        dependency_numbers[group] += 1
        return f"{group}.{dependency_numbers[group]}"

    def visit(
        key: str,
        depth: int,
        parent: str | None,
        reason: str,
        group: int,
        dfs_id: str,
        relation_confirm: int | None,
    ) -> None:
        if key in visited:
            return
        visited.add(key)
        if key.startswith("external:"):
            traversal.append({
                "rank": len(traversal) + 1, "type": "external", "key": key,
                "label": external_labels[key], "depth": depth, "parent": parent,
                "reason": reason, "dfs_id": dfs_id,
                "relation_confirm": relation_confirm,
            })
            return
        commit = selected[key]
        relation_confirmation = relation_confirms.get(key) if commit.focal else None
        pair = pair_by_key.get(key)
        counterpart = None
        if pair:
            counterpart = pair["bc"] if side == "AC" else pair["ac"]
        groups_for_commit = []
        for group in group_by_key.get(key, []):
            groups_for_commit.append({
                "id": group["id"], "confirm": group["confirm"],
                "counterparts": group["bc_commits"] if side == "AC" else group["ac_commits"],
                "scope": group["scope"], "conditions": group["conditions"],
                "basis": group["basis"],
            })
        equivalent_counterparts = []
        if pair:
            equivalent_counterparts.append({
                "relation": pair["id"], "confirm": pair["confirm"],
                "side": "BC" if side == "AC" else "AC", **counterpart,
            })
        for group in groups_for_commit:
            for member in group["counterparts"]:
                equivalent_counterparts.append({
                    "relation": group["id"], "confirm": group["confirm"],
                    "side": "BC" if side == "AC" else "AC", **member,
                })
        traversal.append({
            "rank": len(traversal) + 1, "type": "commit", "key": key,
            "repo": commit.repo, "commit": commit.oid, "short": commit.short,
            "date": commit.date, "subject": commit.subject, "side": side,
            "focal": commit.focal, "depth": depth, "parent": parent,
            "reason": reason, "dfs_id": dfs_id,
            "relation_confirm": (
                relation_confirmation["relation_confirm"]
                if relation_confirmation else relation_confirm
            ),
            "annotation": annotations.get(key),
            "equivalent_pair": None if not pair else {
                "id": pair["id"], "confirm": pair["confirm"],
                "basis": pair["basis"], "counterpart": counterpart,
            },
            "equivalence_groups": groups_for_commit,
            "equivalent_counterparts": equivalent_counterparts,
        })
        for child, _, child_reason, child_confirm in adjacency.get(key, []):
            if child in focal_numbers:
                child_group = focal_numbers[child]
                visit(
                    child, 0, key, child_reason, child_group,
                    f"{child_group}.0", child_confirm,
                )
            else:
                visit(
                    child, depth + 1, key, child_reason, group,
                    next_dependency_id(group), child_confirm,
                )

    for commit in focal:
        group = focal_numbers[commit.key]
        visit(
            commit.key, 0, None, "branch-unique focal commit",
            group, f"{group}.0", None,
        )

    return {
        "side": side,
        "merge_base": merge_base,
        "unique_commit_count": len(focal),
        "strategy": "dynamic branch difference, then depth-first dependencies",
        "branch_edges": branch_edges,
        "dependency_relations": dependency_relations,
        "equivalence_groups": equivalence_groups,
        "relation_confirmations": [
            relation_confirms[commit.key] for commit in focal
        ],
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
    width = 1540
    row_heights = [
        max(92, 48 + 18 * len(item.get("equivalent_counterparts", [])))
        for item in steps
    ]
    height = 140 + sum(row_heights)
    side_color = "#dbeafe" if report["side"] == "AC" else "#ffedd5"
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<style>text{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;fill:#111827}.title{font-size:22px;font-weight:700}.meta{font-size:11px;fill:#374151}.subject{font-size:12px}.branch{stroke:#2563eb;stroke-width:1.8;fill:none}.dep{stroke:#dc2626;stroke-width:1.8;fill:none}.node{stroke:#9ca3af;stroke-width:1}</style>',
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0L10 5L0 10z" fill="#dc2626"/></marker></defs>',
        f'<text x="24" y="34" class="title">{html.escape(title)} · {report["side"]} 独有提交图</text>',
        f'<text x="24" y="58" class="meta">动态独有提交 {report["unique_commit_count"]} 个；N.0=焦点提交，N.x=关联依赖；蓝线=Git祖先拓扑，红线=信息1。</text>',
    ]
    positions: dict[str, tuple[int, int]] = {}
    y = 82
    for index, item in enumerate(steps):
        x = 40 + item["depth"] * 300
        positions[item["key"]] = (x, y)
        if item["parent"] and item["parent"] in positions:
            px, py = positions[item["parent"]]
            out.append(f'<path class="dep" marker-end="url(#arrow)" d="M {px+270} {py+34} C {px+285} {py+34}, {x-15} {y+34}, {x} {y+34}"/>')
        if item["type"] == "external":
            fill, stroke_dash = "#f3f4f6", ' stroke-dasharray="5 4"'
            heading, subject = f"DFS #{item['dfs_id']} · EXTERNAL", item["label"]
        else:
            annotation = item.get("annotation")
            fill = "#e5e7eb" if annotation and annotation["tag"] == "excluded-pilot" else side_color if item["focal"] else "#dcfce7"
            stroke_dash = ' stroke-dasharray="5 4"' if annotation else ""
            pair = item.get("equivalent_pair")
            pair_text = f" · PAIR confirm={pair['confirm']}" if pair else ""
            group_text = "".join(
                f" · EQUIV {group['id']} confirm={group['confirm']}"
                for group in item.get("equivalence_groups", [])
            )
            relation = item.get("relation_confirm")
            relation_text = f" · RELATION confirm={relation}" if relation is not None else ""
            heading = f"DFS #{item['dfs_id']} · {item['repo']} · {item['short']}{pair_text}{group_text}{relation_text}"
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
            note_x = x + (1080 if item.get("equivalent_counterparts") else 285)
            out.append(f'<text x="{note_x}" y="{y+36}" class="meta">{html.escape(note)}</text>')
        counterparts = item.get("equivalent_counterparts", [])
        if counterparts:
            panel_x = x + 300
            panel_h = max(68, 25 + 18 * len(counterparts))
            out.append(
                f'<rect x="{panel_x}" y="{y}" width="760" height="{panel_h}" rx="8" '
                'fill="#f5f3ff" stroke="#7c3aed" stroke-dasharray="5 4"/>'
            )
            opposite = "BC" if report["side"] == "AC" else "AC"
            out.append(
                f'<text x="{panel_x+10}" y="{y+17}" class="meta">'
                f'{opposite} 等价提交（逐条标记确认状态，非依赖边）</text>'
            )
            for offset, link in enumerate(counterparts):
                status = "已确认" if link["confirm"] == 1 else "候选"
                label = (
                    f'{link["side"]} {status} confirm={link["confirm"]} · '
                    f'{link["repo"]} {link["commit"]} · {link["relation"]}'
                )
                out.append(
                    f'<text x="{panel_x+10}" y="{y+36+offset*18}" '
                    f'class="meta">{html.escape(label)}</text>'
                )
        y += row_heights[index]
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
        lines.append(f"{item['dfs_id']:>6} {indent}{label}")
        for link in item.get("equivalent_counterparts", []):
            status = "已确认" if link["confirm"] == 1 else "候选"
            lines.append(
                f"       {indent}↔ {link['side']} 等价{status} confirm={link['confirm']}: "
                f"{link['repo']} {link['commit']} ({link['relation']})"
            )
    (output_dir / f"{prefix}-order.txt").write_text("\n".join(lines) + "\n")


def generate_task(task_root: Path, output_dir: Path) -> tuple[dict, dict]:
    scope = read_json(task_root / "scope.json")
    repos = load_repos(scope, task_root)
    relation_confirms = load_relation_confirms(
        read_json(task_root / "relation_confirms.json"), repos,
    )
    dependencies = load_dependencies(
        read_json(task_root / "dependencies.json"), repos, relation_confirms,
    )
    pairs, pair_by_key = load_pairs(read_json(task_root / "equivalent_pairs.json"), repos)
    equivalence_groups, group_by_key = load_equivalence_groups(
        read_json(task_root / "equivalent_pairs.json"), repos,
    )
    annotations = load_annotations(scope, repos)
    anchor = scope["anchor"]
    anchor_repo = repos[anchor["repository"]]
    ac_base, ac = unique_commits(anchor_repo, "AC", anchor["paths"])
    bc_base, bc = unique_commits(anchor_repo, "BC", anchor["paths"])
    if ac_base != bc_base:
        raise ValueError("AC and BC merge-base mismatch")
    ac_keys, bc_keys = {item.key for item in ac}, {item.key for item in bc}
    expected_confirmations = ac_keys | bc_keys
    actual_confirmations = set(relation_confirms)
    if actual_confirmations != expected_confirmations:
        missing = sorted(expected_confirmations - actual_confirmations)
        extra = sorted(actual_confirmations - expected_confirmations)
        raise ValueError(f"relation confirmations mismatch: missing={missing}, extra={extra}")
    for key in ac_keys:
        if relation_confirms[key]["side"] != "AC":
            raise ValueError(f"relation confirmation is in wrong section: {key}")
    for key in bc_keys:
        if relation_confirms[key]["side"] != "BC":
            raise ValueError(f"relation confirmation is in wrong section: {key}")
    for source_key, relation in dependencies.items():
        expected = ac_keys if relation["source_side"] == "AC" else bc_keys
        if source_key not in expected:
            raise ValueError(f"dependency source is not a dynamic focal unique commit: {source_key}")
    for pair in pairs:
        ac_key = f"{pair['ac']['repo']}:{pair['ac']['commit']}"
        bc_key = f"{pair['bc']['repo']}:{pair['bc']['commit']}"
        if ac_key not in ac_keys or bc_key not in bc_keys:
            raise ValueError(f"{pair['id']}: pair members must be dynamic focal unique commits")
    for group in equivalence_groups:
        for side, members in (("AC", group["ac_commits"]), ("BC", group["bc_commits"])):
            for member in members:
                repo = repos[member["repo"]]
                tip = repo.ac_ref if side == "AC" else repo.bc_ref
                git(repo.path, ["merge-base", "--is-ancestor", member["commit"], tip])
        member_keys = {
            f"{member['repo']}:{member['commit']}"
            for member in group["ac_commits"] + group["bc_commits"]
        }
        if not member_keys.intersection(ac_keys | bc_keys):
            raise ValueError(f"{group['id']}: at least one member must be a focal commit")
    ac_edges = projected_branch_edges(anchor_repo, "AC", ac_base, ac)
    bc_edges = projected_branch_edges(anchor_repo, "BC", bc_base, bc)
    ac_report = side_report(
        "AC", ac, repos, dependencies, relation_confirms,
        pair_by_key, annotations, ac_base, ac_edges, equivalence_groups, group_by_key,
    )
    bc_report = side_report(
        "BC", bc, repos, dependencies, relation_confirms,
        pair_by_key, annotations, bc_base, bc_edges, equivalence_groups, group_by_key,
    )
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
