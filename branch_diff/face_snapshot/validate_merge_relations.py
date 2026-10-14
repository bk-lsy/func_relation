#!/usr/bin/env python3
"""Validate the face_snapshot local-commit/source-commit relation graph."""

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CAP = ROOT.parents[2] / "NVMP/nvmp/tp_package/cap"


def read_json(name):
    return json.loads((ROOT / name).read_text())


def git(*args):
    return subprocess.check_output(["git", *args], cwd=CAP, text=True).strip()


def main():
    graph = read_json("merge_relations.json")
    status = read_json("merge_status.json")
    sources = {entry["id"]: entry for entry in status["entries"]}
    assert len(sources) == len(status["entries"])
    expected_sources = [{"id": entry["id"], "commit": entry["source_commit"], "title": entry["source_title"]}
                        for entry in status["entries"]]
    assert graph["source_nodes"] == expected_sources, "source nodes differ from merge_status.json"
    assert graph["target_head"] == git("rev-parse", "HEAD"), "CAP HEAD changed; refresh the relation graph"
    commits = git("rev-list", "--reverse", f"{graph['local_base']}..{graph['target_head']}").splitlines()
    nodes = graph["local_nodes"]
    assert [node["commit"] for node in nodes] == commits, "local commit inventory differs from CAP history"

    roles = set(graph["relation_definitions"])
    degree = {commit: 0 for commit in commits}
    unique_edges = set()
    linked_sources = set()
    for edge in graph["edges"]:
        local = edge["local_commit"]
        source_id = edge["source_id"]
        role = edge["relation"]
        assert local in degree
        assert source_id in sources
        assert edge["source_commit"] == sources[source_id]["source_commit"]
        assert role in roles
        key = (local, source_id, role)
        assert key not in unique_edges, f"duplicate edge: {key}"
        unique_edges.add(key)
        degree[local] += 1
        linked_sources.add(source_id)

        evidence = edge["evidence"]
        if evidence["kind"] == "cap_commit_message":
            message = git("show", "-s", "--format=%B", local)
            assert edge["source_commit"][:8] in message, f"untraced source edge: {key}"
        elif evidence["kind"] == "batch_record":
            record = CAP / evidence["detail"]
            assert record.is_file()
            assert edge["source_commit"][:8] in record.read_text(), f"untraced batch edge: {key}"
        else:
            assert evidence["kind"] == "review_record"
            files = evidence["files"]
            assert files
            assert all(((ROOT.parents[1] / name) if name.startswith("merge_work/") else (CAP / name)).is_file()
                       for name in files)

    assert all(degree.values()), "every local commit needs at least one explained edge"
    expected_unlinked = [entry["id"] for entry in status["entries"] if entry["id"] not in linked_sources]
    assert graph["unlinked_source_ids"] == expected_unlinked
    print(f"valid: {len(nodes)} local commits, {len(graph['edges'])} edges, "
          f"{len(linked_sources)} linked and {len(expected_unlinked)} unlinked source nodes")


if __name__ == "__main__":
    main()
