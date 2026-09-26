import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "generate_branch_diff.py"
SPEC = importlib.util.spec_from_file_location("cd_alarm_branch_diff", MODULE_PATH)
module = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


class GenerateTest(unittest.TestCase):
    def test_discovers_nested_task_directories(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "one").mkdir()
            (root / "nested" / "two").mkdir(parents=True)
            (root / "one" / "scope.json").write_text("{}")
            (root / "nested" / "two" / "scope.json").write_text("{}")
            self.assertEqual(
                module.discover_tasks(root),
                [root / "nested" / "two", root / "one"],
            )

    def test_svg_marks_pending_pair_and_excluded_pilot(self):
        report = {
            "side": "BC",
            "unique_commit_count": 1,
            "analysis_order": [
                {
                    "rank": 1, "type": "commit", "key": "CAP:a", "repo": "CAP",
                    "short": "a", "subject": "pilot", "focal": True, "depth": 0,
                    "parent": None, "dfs_id": "1.0",
                    "annotation": {"tag": "excluded-pilot", "note": "excluded"},
                    "equivalent_pair": {"confirm": 0},
                }
            ],
        }
        svg = module.render_svg(report, "title")
        self.assertIn("PAIR confirm=0", svg)
        self.assertIn("excluded", svg)

    def test_external_dependency_is_rendered_as_leaf(self):
        report = {
            "side": "AC",
            "unique_commit_count": 0,
            "analysis_order": [
                {
                    "rank": 1, "type": "external", "key": "external:1",
                    "label": "PRODUCT contract", "depth": 0, "parent": None,
                    "dfs_id": "1.1",
                }
            ],
        }
        self.assertIn("PRODUCT contract", module.render_svg(report, "title"))

    def test_branch_topology_edge_is_rendered_separately(self):
        report = {
            "side": "AC",
            "unique_commit_count": 2,
            "branch_edges": [{"parent": "CAP:a", "child": "CAP:b"}],
            "analysis_order": [
                {
                    "rank": rank, "type": "commit", "key": f"CAP:{oid}",
                    "repo": "CAP", "short": oid, "subject": oid,
                    "focal": True, "depth": 0, "parent": None,
                    "dfs_id": f"{rank}.0",
                    "annotation": None, "equivalent_pair": None,
                }
                for rank, oid in enumerate(("a", "b"), 1)
            ],
        }
        svg = module.render_svg(report, "title")
        self.assertIn('class="branch"', svg)
        self.assertIn("蓝线=Git祖先拓扑", svg)

    def test_focal_dependency_keeps_dot_zero_number(self):
        focal = [
            module.Commit("CAP", "a", "2026-01-01", "first", "AC", True),
            module.Commit("CAP", "b", "2026-01-02", "second", "AC", True),
        ]
        dependencies = {
            "CAP:a": {
                "source_side": "AC", "target_side": "BC",
                "required_commits": [
                    {
                        "repo": "CAP", "commit": "b", "reason": "follow-up",
                        "relation_confirm": 0,
                    },
                ],
                "external_requirements": ["external contract"],
            }
        }
        confirmations = {
            "CAP:a": {
                "side": "AC", "source": "CAP:a", "related_chain": ["CAP:b"],
                "relation_confirm": 0,
            },
            "CAP:b": {
                "side": "AC", "source": "CAP:b", "related_chain": [],
                "relation_confirm": 0,
            },
        }
        report = module.side_report(
            "AC", focal, {}, dependencies, confirmations, {}, {}, "base", [],
        )
        commits = [x for x in report["analysis_order"] if x["type"] == "commit"]
        external = [x for x in report["analysis_order"] if x["type"] == "external"]
        self.assertEqual([x["dfs_id"] for x in commits], ["1.0", "2.0"])
        self.assertTrue(all(x["focal"] for x in commits))
        self.assertEqual([x["dfs_id"] for x in external], ["1.1"])
        self.assertEqual(commits[1]["relation_confirm"], 0)
        self.assertEqual(len(report["relation_confirmations"]), 2)
        self.assertEqual(
            report["dependency_relations"],
            [{
                "source": "CAP:a", "related": "CAP:b",
                "reason": "follow-up", "relation_confirm": 0,
            }],
        )


if __name__ == "__main__":
    unittest.main()
