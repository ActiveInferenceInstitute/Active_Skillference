"""Unknown prose placeholders cannot silently become plausible manuscript text."""

from __future__ import annotations

import pytest

from scripts.z_generate_manuscript_variables import _render_markdown


def test_known_prose_variables_and_claims_resolve_to_the_supplied_value() -> None:
    assert (
        _render_markdown("Result {{value}} / {{claim:value}}.", {"value": "computed"})
        == "Result computed / computed."
    )


@pytest.mark.parametrize(
    "text", ["Result {{misspelled}}.", "Result {{claim:missing}}."]
)
def test_unknown_prose_placeholder_fails_instead_of_stripping_its_delimiters(
    text: str,
) -> None:
    with pytest.raises(KeyError):
        _render_markdown(text, {"value": "computed"})


def test_code_examples_normalize_locally_without_admitting_unknown_adjacent_prose() -> (
    None
):
    example = "Use `{{unknown}}` and:\n```text\n{{claim:missing}}\n```\n"
    assert (
        _render_markdown(example, {})
        == "Use `unknown` and:\n```text\nclaim:missing\n```\n"
    )
    with pytest.raises(KeyError):
        _render_markdown(example + "Prose {{unknown}}.", {})


@pytest.mark.parametrize(
    "text", ["Result {{missing token}}.", "Result {{ claim:value }}."]
)
def test_unrecognized_prose_token_shape_remains_an_error(text: str) -> None:
    with pytest.raises(ValueError, match="unresolved manuscript tokens"):
        _render_markdown(text, {"value": "computed"})
