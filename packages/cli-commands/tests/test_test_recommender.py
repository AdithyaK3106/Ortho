"""Test Intelligence: recommend_tests must only report real, discovered
test files -- never invent a name, matching the roadmap's 'never fabricate'
principle applied to test recommendations."""

from cli_commands.test_recommender import recommend_tests


def test_finds_matching_test_module():
    file_to_module = {
        "/repo/src/formatting.py": "src.formatting",
        "/repo/tests/test_formatting.py": "tests.test_formatting",
    }
    result = recommend_tests(["src.formatting"], file_to_module)

    assert len(result) == 1
    assert result[0].has_coverage is True
    assert result[0].test_modules == ["tests.test_formatting"]


def test_reports_coverage_gap_when_no_test_exists():
    file_to_module = {
        "/repo/src/core.py": "src.core",
    }
    result = recommend_tests(["src.core"], file_to_module)

    assert len(result) == 1
    assert result[0].has_coverage is False
    assert result[0].test_modules == []


def test_resolves_raw_file_path_to_module_name():
    """Upstream callers (ChangePredictor) sometimes pass raw file paths
    instead of module names in affected_modules -- must resolve through
    file_to_module before matching, not treat the path itself as a stem."""
    file_to_module = {
        "/repo/src/testing.py": "src.testing",
        "/repo/tests/test_testing.py": "tests.test_testing",
    }
    result = recommend_tests(["/repo/src/testing.py"], file_to_module)

    assert result[0].affected_module == "src.testing"
    assert result[0].has_coverage is True
    assert result[0].test_modules == ["tests.test_testing"]


def test_module_does_not_recommend_itself_as_its_own_test():
    file_to_module = {
        "/repo/tests/test_foo.py": "tests.test_foo",
    }
    result = recommend_tests(["tests.test_foo"], file_to_module)

    assert result[0].has_coverage is False


def test_matches_suffix_style_test_naming():
    file_to_module = {
        "/repo/src/parser.py": "src.parser",
        "/repo/tests/parser_test.py": "tests.parser_test",
    }
    result = recommend_tests(["src.parser"], file_to_module)

    assert result[0].has_coverage is True
    assert result[0].test_modules == ["tests.parser_test"]


def test_empty_affected_modules_returns_empty_list():
    result = recommend_tests([], {"/repo/a.py": "a"})
    assert result == []


def test_similar_but_not_matching_names_not_confused():
    """test_formatter must not match module 'formatting' -- exact stem
    match only, not a substring/prefix match that could mislead a
    reviewer into thinking coverage exists when it doesn't."""
    file_to_module = {
        "/repo/src/formatting.py": "src.formatting",
        "/repo/tests/test_formatter.py": "tests.test_formatter",
    }
    result = recommend_tests(["src.formatting"], file_to_module)

    assert result[0].has_coverage is False


def test_multiple_affected_modules_each_evaluated_independently():
    file_to_module = {
        "/repo/src/a.py": "src.a",
        "/repo/src/b.py": "src.b",
        "/repo/tests/test_a.py": "tests.test_a",
    }
    result = recommend_tests(["src.a", "src.b"], file_to_module)

    by_module = {r.affected_module: r for r in result}
    assert by_module["src.a"].has_coverage is True
    assert by_module["src.b"].has_coverage is False
