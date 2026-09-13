import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "func_relation.py"
SPEC = importlib.util.spec_from_file_location("func_relation", MODULE_PATH)
func_relation = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = func_relation
SPEC.loader.exec_module(func_relation)


class FuncRelationTest(unittest.TestCase):
    def test_semantic_rules_are_dynamically_loaded(self):
        self.assertEqual(
            ["dead_initializer", "immediate_condition_alias", "static_pure_constant", "unobservable_pure_initializer"],
            [rule.name for rule in func_relation.semantic_rules()],
        )

    def test_all_rules_are_dynamically_loaded(self):
        self.assertEqual(
            [
                "call_classification", "dead_initializer", "function_discovery",
                "function_order", "immediate_condition_alias", "static_pure_constant",
                "unobservable_pure_initializer",
            ],
            [rule.name for rule in func_relation.rules()],
        )

    def test_load_config_and_resolve_its_relative_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            config_file = Path(directory) / "config.yaml"
            config_file.write_text("base_dir: ../repo\nsource_path: old\nbefore: abc123\nafter: def456\nprofile: profiles/test.yaml\n")
            config = func_relation.load_config(config_file)
            self.assertEqual("abc123", config["before"])
            self.assertEqual("old", config["source_path"])
            self.assertEqual(Path(directory).parent / "repo", func_relation.config_path(config["base_dir"], config_file))

    def test_worktree_revision_uses_the_ordinary_source_path(self):
        self.assertEqual("src/module", func_relation.revision_location("WORKTREE", "src/module"))
        self.assertEqual("git:abc123:src/module", func_relation.revision_location("abc123", "src/module"))

    def test_disabled_hashes_are_omitted_from_function_summary(self):
        function = func_relation.extract_functions("int f(void) { return 1; }")["f"]
        summary = func_relation.function_summary(
            function, {"f": function}, 0, 20,
            {"raw_hash": False, "structural_hash": True, "semantic_hash": False},
        )
        self.assertNotIn("raw_hash", summary)
        self.assertIn("structural_hash", summary)
        self.assertNotIn("semantic_hash", summary)

    def test_provably_unread_parameter_initializer_is_omitted(self):
        function = func_relation.extract_functions("""
            int f(int type, int channel) {
                int status = type;
                if (channel) return 0;
                status = type + channel;
                return status;
            }
        """)["f"]
        semantic = func_relation.semantic_lines(function, {"f": function}, 0, 40)
        temporal = "\n".join(semantic["temporal"])
        self.assertNotIn("SET_LOCAL int v2 = v0", temporal)
        self.assertIn("SET_LOCAL v2 = v0 + v1", temporal)

    def test_initializer_is_retained_when_it_is_read_before_overwrite(self):
        function = func_relation.extract_functions("""
            int f(int type) {
                int status = type;
                log_value(status);
                status = 1;
                return status;
            }
        """)["f"]
        semantic = func_relation.semantic_lines(function, {"f": function}, 0, 40)
        self.assertIn("SET_LOCAL int v1 = v0", "\n".join(semantic["temporal"]))

    def test_reassigned_constant_is_neither_static_nor_temporal_noise(self):
        function = func_relation.extract_functions("""
            int f(int type) {
                int status = 0;
                status = type;
                return status;
            }
        """)["f"]
        semantic = func_relation.semantic_lines(function, {"f": function}, 0, 40)
        combined = "\n".join(semantic["static"] + semantic["temporal"])
        self.assertNotIn("status [v1] = 0", combined)
        self.assertIn("SET_LOCAL v1 = v0", combined)

    def test_reassigned_constant_is_not_classified_as_static(self):
        function = func_relation.extract_functions("""
            int f(void) { int state = MODE_IDLE; state = MODE_ACTIVE; return state; }
        """)["f"]
        semantic = func_relation.semantic_lines(function, {"f": function}, 0, 40)
        self.assertEqual([], semantic["static"])

    def test_unobservable_pure_initializer_is_omitted_across_a_return_guard(self):
        function = func_relation.extract_functions("""
            int f(int input) {
                int status = MODE_IDLE;
                if (input) { return 1; }
                status = compute_status();
                return status;
            }
        """)["f"]
        temporal = "\n".join(func_relation.semantic_lines(function, {"f": function}, 0, 40)["temporal"])
        self.assertNotIn("MODE_IDLE", temporal)
        self.assertIn("SET_LOCAL v1 = compute_status ( )", temporal)

    def test_pure_initializer_is_retained_without_an_unconditional_overwrite(self):
        function = func_relation.extract_functions("""
            int f(int input) {
                int status = MODE_IDLE;
                if (input) { status = MODE_ACTIVE; }
                return status;
            }
        """)["f"]
        temporal = "\n".join(func_relation.semantic_lines(function, {"f": function}, 0, 40)["temporal"])
        self.assertIn("SET_LOCAL int v1 = MODE_IDLE", temporal)

    def test_deferred_declaration_uses_the_first_effective_write(self):
        function = func_relation.extract_functions("""
            int f(int input) {
                int status = input;
                if (input) { return 1; }
                status = input + 1;
                return status;
            }
        """)["f"]
        temporal = "\n".join(func_relation.semantic_lines(function, {"f": function}, 0, 40)["temporal"])
        self.assertNotIn("SET_LOCAL int v1 = v0", temporal)
        self.assertIn("SET_LOCAL int v1 = v0 + 1", temporal)

    def test_immediate_condition_alias_is_folded(self):
        function = func_relation.extract_functions("""
            int f(int input) {
                int should_stop = 0;
                should_stop = check_input(input);
                if (should_stop) { return 1; }
                return 0;
            }
        """)["f"]
        temporal = "\n".join(func_relation.semantic_lines(function, {"f": function}, 0, 40)["temporal"])
        self.assertNotIn("should_stop", temporal)
        self.assertIn("IF check_input ( v0 )", temporal)

    def test_flatten_selects_profile_branch(self):
        source = """\
#ifdef ENABLE
int selected(void) { return 1; }
#else
int selected(void) { return 2; }
#endif
"""
        flat, diagnostics = func_relation.flatten(source, {"ENABLE": 1})
        self.assertEqual([], diagnostics)
        self.assertIn("return 1", flat)
        self.assertNotIn("return 2", flat)

    def test_local_rename_is_structurally_equivalent(self):
        before = "int f(int input) { int total = input + 1; return total; }"
        after = "int f(int value) { int result = value + 1; return result; }"
        left = func_relation.extract_functions(before)["f"]
        right = func_relation.extract_functions(after)["f"]
        result = func_relation.relation(left, right)
        self.assertEqual("STRUCTURALLY_EQUIVALENT", result["relation"])

    def test_call_change_is_not_identical(self):
        before = "int f(void) { return old_effect(); }"
        after = "int f(void) { return new_effect(); }"
        left = func_relation.extract_functions(before)["f"]
        right = func_relation.extract_functions(after)["f"]
        result = func_relation.relation(left, right)
        self.assertNotEqual("IDENTICAL", result["relation"])
        self.assertEqual(["old_effect"], result["before_effects"])
        self.assertEqual(["new_effect"], result["after_effects"])

    def test_comparison_includes_human_readable_diffs(self):
        before = func_relation.extract_functions("int f(int a) { return old_effect(a); }")["f"]
        after = func_relation.extract_functions("int f(int a) { return new_effect(a); }")["f"]
        result = func_relation.compare_functions(before, after, {"f": before}, {"f": after}, 20, 1)
        self.assertEqual("CHANGED", result["relation"])
        self.assertIn("old_effect", "\n".join(result["semantic_a"]["temporal"]))
        self.assertEqual(["new_effect"], result["direct_effects"]["added"])

    def test_declaration_after_control_block_is_a_local(self):
        source = "int f(int input) { if (input) { return 1; } int later = 0; return later; }"
        function = func_relation.extract_functions(source)["f"]
        semantic = func_relation.semantic_lines(function, {"f": function}, 0, 40)
        bindings = semantic["bindings"]
        self.assertIn("later", bindings)
        self.assertEqual({"input": "v0"}, semantic["binding_groups"]["parameters"])
        self.assertEqual({"later": "v1"}, semantic["binding_groups"]["locals"])

    def test_bindings_keep_source_groups_and_static_locals(self):
        source = "int f(int first, int second) { int local = 0; static int cached = 1; return local + cached; }"
        function = func_relation.extract_functions(source)["f"]
        semantic = func_relation.semantic_lines(function, {"f": function}, 0, 40)
        self.assertEqual(
            ["first", "second", "local", "cached"],
            list(semantic["bindings"]),
        )
        self.assertEqual({"first": "v0", "second": "v1"}, semantic["binding_groups"]["parameters"])
        self.assertEqual({"local": "v2"}, semantic["binding_groups"]["locals"])
        self.assertEqual({"cached": "v3"}, semantic["binding_groups"]["static_locals"])
        self.assertEqual({}, semantic["binding_groups"]["globals"])

    def test_pure_constant_declaration_is_static_not_temporal(self):
        source = "int f(int input) { int mode = MODE_DEFAULT; if (input) return 1; return mode; }"
        function = func_relation.extract_functions(source)["f"]
        semantic = func_relation.semantic_lines(function, {"f": function}, 0, 40)
        self.assertEqual(["STATIC_LOCAL mode [v1] = MODE_DEFAULT"], semantic["static"])
        self.assertNotIn("MODE_DEFAULT", "\n".join(semantic["temporal"]))

    def test_reachable_functions_are_flat_and_sorted(self):
        functions = func_relation.extract_functions("""
            int helper(void) { return 1; }
            int root(void) { helper(); helper(); return helper(); }
        """)
        semantic = func_relation.semantic_lines(functions["root"], functions, 2, 80)
        function_lines = [line for line in semantic["temporal"] if line.startswith("FUNCTION ")]
        self.assertEqual(["FUNCTION helper", "FUNCTION root"], function_lines)
        self.assertEqual(1, function_lines.count("FUNCTION helper"))
        self.assertEqual(0, sum(line.strip() == "EXPAND helper" for line in semantic["temporal"]))


if __name__ == "__main__":
    unittest.main()
