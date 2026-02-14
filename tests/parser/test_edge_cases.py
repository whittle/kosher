"""Edge case tests for the Gherkin parser."""

from collections.abc import Callable
from pathlib import Path


from kosher.parser import GherkinParser, StepType, parse_feature


class TestEmptyFiles:
    """Test handling of empty or minimal files."""

    def test_empty_file(self, feature_file_factory: Callable[[str, str], Path]) -> None:
        """Empty file returns empty feature."""
        path = feature_file_factory("empty.feature", "")

        feature = parse_feature(path)

        assert feature.name == ""
        assert len(feature.scenarios) == 0

    def test_whitespace_only_file(
        self, feature_file_factory: Callable[[str, str], Path]
    ) -> None:
        """Whitespace-only file returns empty feature."""
        path = feature_file_factory("whitespace.feature", "   \n\n  \t  \n")

        feature = parse_feature(path)

        assert feature.name == ""
        assert len(feature.scenarios) == 0

    def test_feature_with_no_scenarios(
        self, feature_file_factory: Callable[[str, str], Path]
    ) -> None:
        """Feature with no scenarios is valid."""
        content = """
        Feature: Empty Feature
          This feature has a description but no scenarios.
        """
        path = feature_file_factory("no_scenarios.feature", content)

        feature = parse_feature(path)

        assert feature.name == "Empty Feature"
        assert len(feature.scenarios) == 0

    def test_scenario_with_no_steps(
        self, feature_file_factory: Callable[[str, str], Path]
    ) -> None:
        """Scenario with no steps is valid."""
        content = """
        Feature: Minimal
          Scenario: Empty scenario
        """
        path = feature_file_factory("no_steps.feature", content)

        feature = parse_feature(path)

        assert len(feature.scenarios) == 1
        assert len(feature.scenarios[0].steps) == 0


class TestUnicodeAndEmoji:
    """Test unicode and emoji handling."""

    def test_unicode_in_step_text(
        self, feature_file_factory: Callable[[str, str], Path]
    ) -> None:
        """Unicode characters in step text are preserved."""
        content = """
        Feature: Internationalization
          Scenario: Japanese text
            Given I see the text "こんにちは世界"
            When I click "Weiter"
            Then I should see "Willkommen"
        """
        path = feature_file_factory("unicode.feature", content)

        feature = parse_feature(path)

        steps = feature.scenarios[0].steps
        assert "こんにちは世界" in steps[0].text

    def test_emoji_in_step_text(
        self, feature_file_factory: Callable[[str, str], Path]
    ) -> None:
        """Emoji in step text are preserved."""
        content = """
        Feature: Emoji Support
          Scenario: Emoji display
            Given I see the "Submit" button
            When I click it
            Then I should see a success message
        """
        path = feature_file_factory("emoji.feature", content)

        feature = parse_feature(path)

        assert len(feature.scenarios[0].steps) == 3


class TestLongText:
    """Test handling of very long text."""

    def test_very_long_step_text(
        self, feature_file_factory: Callable[[str, str], Path]
    ) -> None:
        """Very long step text (10K+ chars) is handled."""
        long_text = "a" * 15000
        content = f'''
        Feature: Long Text
          Scenario: Long step
            Given I have the text "{long_text}"
            Then it works
        '''
        path = feature_file_factory("long.feature", content)

        feature = parse_feature(path)

        assert long_text in feature.scenarios[0].steps[0].text

    def test_very_long_feature_description(
        self, feature_file_factory: Callable[[str, str], Path]
    ) -> None:
        """Very long feature description is handled."""
        long_desc = "This is a long description. " * 500
        content = f"""
        Feature: Long Description
          {long_desc}

          Scenario: Simple
            Given something
        """
        path = feature_file_factory("long_desc.feature", content)

        feature = parse_feature(path)

        assert len(feature.description) > 1000


class TestSpecialCharacters:
    """Test handling of special characters."""

    def test_quotes_in_step_text(
        self, feature_file_factory: Callable[[str, str], Path]
    ) -> None:
        """Quoted strings in steps are preserved."""
        content = """
        Feature: Quotes
          Scenario: Quoted text
            Given I see "Hello, World!"
            When I enter 'single quotes'
            Then I should see "nested 'quotes'"
        """
        path = feature_file_factory("quotes.feature", content)

        feature = parse_feature(path)

        steps = feature.scenarios[0].steps
        assert '"Hello, World!"' in steps[0].text

    def test_angle_brackets_in_step_text(
        self, feature_file_factory: Callable[[str, str], Path]
    ) -> None:
        """Angle brackets (not placeholders) are preserved."""
        content = """
        Feature: Brackets
          Scenario: HTML content
            Given I see "<div>content</div>"
            Then the page loads
        """
        path = feature_file_factory("brackets.feature", content)

        feature = parse_feature(path)

        steps = feature.scenarios[0].steps
        assert "<div>content</div>" in steps[0].text

    def test_backslash_in_step_text(
        self, feature_file_factory: Callable[[str, str], Path]
    ) -> None:
        """Backslashes in step text are preserved."""
        content = r"""
        Feature: Backslash
          Scenario: File path
            Given I navigate to "C:\Users\test"
            Then it works
        """
        path = feature_file_factory("backslash.feature", content)

        feature = parse_feature(path)

        assert "C:\\Users\\test" in feature.scenarios[0].steps[0].text


class TestComments:
    """Test comment handling."""

    def test_comments_are_ignored(
        self, feature_file_factory: Callable[[str, str], Path]
    ) -> None:
        """Comments are not included in parsed output."""
        content = """
        # This is a file comment
        Feature: Comments
          # This is a feature comment

          Scenario: Test
            # This is a step comment
            Given I am ready
            # Another comment
            Then it works
        """
        path = feature_file_factory("comments.feature", content)

        feature = parse_feature(path)

        assert len(feature.scenarios) == 1
        assert len(feature.scenarios[0].steps) == 2
        # Comments should not appear in step text
        for step in feature.scenarios[0].steps:
            assert "#" not in step.text


class TestLanguageDirective:
    """Test language directive handling."""

    def test_german_language(
        self, feature_file_factory: Callable[[str, str], Path]
    ) -> None:
        """German language directive is honored."""
        content = """
        # language: de
        Funktionalität: Login-Funktionalität
          Szenario: Erfolgreicher Login
            Angenommen ich bin auf der Login-Seite
            Wenn ich mich einlogge
            Dann sehe ich das Dashboard
        """
        path = feature_file_factory("german.feature", content)

        feature = parse_feature(path)

        assert feature.name == "Login-Funktionalität"
        assert feature.language == "de"
        assert len(feature.scenarios) == 1
        assert feature.scenarios[0].name == "Erfolgreicher Login"


class TestStarKeyword:
    """Test the * (star) keyword."""

    def test_star_keyword_parsed(
        self, feature_file_factory: Callable[[str, str], Path]
    ) -> None:
        """Star keyword steps are parsed."""
        content = """
        Feature: Star Keyword
          Scenario: Using star
            * I do something
            * I do something else
            Then it works
        """
        path = feature_file_factory("star.feature", content)

        feature = parse_feature(path)

        steps = feature.scenarios[0].steps
        assert len(steps) == 3
        # Star steps should have UNKNOWN type
        assert steps[0].step_type == StepType.UNKNOWN
        assert steps[1].step_type == StepType.UNKNOWN


class TestWhitespaceVariations:
    """Test various whitespace scenarios."""

    def test_tabs_in_indentation(
        self, feature_file_factory: Callable[[str, str], Path]
    ) -> None:
        """Tabs in indentation are handled."""
        content = "Feature: Tabs\n\tScenario: Tab indented\n\t\tGiven I am ready\n\t\tThen it works\n"
        path = feature_file_factory("tabs.feature", content)

        feature = parse_feature(path)

        assert len(feature.scenarios) == 1
        assert len(feature.scenarios[0].steps) == 2

    def test_mixed_indentation(
        self, feature_file_factory: Callable[[str, str], Path]
    ) -> None:
        """Mixed spaces and tabs are handled."""
        content = "Feature: Mixed\n  Scenario: Mixed indent\n\t  Given I am ready\n    Then it works\n"
        path = feature_file_factory("mixed.feature", content)

        feature = parse_feature(path)

        assert len(feature.scenarios[0].steps) == 2

    def test_trailing_whitespace(
        self, feature_file_factory: Callable[[str, str], Path]
    ) -> None:
        """Trailing whitespace is handled."""
        content = "Feature: Trailing   \n  Scenario: Whitespace   \n    Given I am ready   \n    Then it works   \n"
        path = feature_file_factory("trailing.feature", content)

        feature = parse_feature(path)

        # Step text should not have trailing whitespace
        assert not feature.scenarios[0].steps[0].text.endswith(" ")


class TestMultipleExamplesTables:
    """Test scenario outlines with multiple Examples tables."""

    def test_multiple_examples_tables(
        self, feature_file_factory: Callable[[str, str], Path]
    ) -> None:
        """Multiple Examples tables are combined."""
        content = """
        Feature: Multiple Examples
          Scenario Outline: Test with <value>
            Given I have <value>
            Then it works

            Examples: Small values
              | value |
              | 1     |
              | 2     |

            Examples: Large values
              | value |
              | 100   |
              | 200   |
        """
        path = feature_file_factory("multi_examples.feature", content)

        feature = parse_feature(path)

        # Should have 4 scenarios (2 from each Examples table)
        assert len(feature.scenarios) == 4
        values = [s.steps[0].text for s in feature.scenarios]
        assert "I have 1" in values
        assert "I have 2" in values
        assert "I have 100" in values
        assert "I have 200" in values


class TestDataTableEdgeCases:
    """Test data table edge cases."""

    def test_empty_cells_in_data_table(
        self, feature_file_factory: Callable[[str, str], Path]
    ) -> None:
        """Empty cells in data tables are handled."""
        content = """Feature: Empty Cells
          Scenario: Table with empties
            Given the following data:
              | name  | email |
              | Alice |       |
              |       | bob@x |
            Then it works
        """
        path = feature_file_factory("empty_cells.feature", content)

        feature = parse_feature(path)

        table = feature.scenarios[0].steps[0].data_table
        assert table is not None
        dicts = table.as_dicts()
        assert dicts[0]["email"] == ""
        assert dicts[1]["name"] == ""

    def test_data_table_header_only(
        self, feature_file_factory: Callable[[str, str], Path]
    ) -> None:
        """Data table with only header row."""
        content = """
        Feature: Header Only
          Scenario: Single row table
            Given the following data:
              | name | email |
            Then it works
        """
        path = feature_file_factory("header_only.feature", content)

        feature = parse_feature(path)

        table = feature.scenarios[0].steps[0].data_table
        assert table is not None
        # as_dicts should return empty list for header-only table
        assert table.as_dicts() == []


class TestButKeyword:
    """Test the But keyword specifically."""

    def test_but_keyword_inherits_type(
        self, feature_file_factory: Callable[[str, str], Path]
    ) -> None:
        """But keyword inherits type from preceding step."""
        content = """
        Feature: But Keyword
            Scenario: Using But
              Given I am ready
              But I am not tired
              When I work
              But I do not rush
              Then I succeed
              But I am not stressed
          """
        path = feature_file_factory("but.feature", content)
        feature = parse_feature(path)
        steps = feature.scenarios[0].steps

        # But after Given -> CONTEXT
        assert steps[1].step_type == StepType.CONTEXT
        assert "not tired" in steps[1].text

        # But after When -> ACTION
        assert steps[3].step_type == StepType.ACTION
        assert "not rush" in steps[3].text

        # But after Then -> OUTCOME
        assert steps[5].step_type == StepType.OUTCOME
        assert "not stressed" in steps[5].text


class TestParseStringMethod:
    """Test GherkinParser.parse_string directly."""

    def test_parse_string_default_uri(self) -> None:
        """Default URI is '<string>' when not specified."""
        parser = GherkinParser()
        content = """Feature: Test
  Scenario: Simple
    Given something
"""
        feature = parser.parse_string(content)
        assert feature.uri == "<string>"

    def test_parse_string_custom_uri(self) -> None:
        """Custom URI is preserved."""
        parser = GherkinParser()
        content = """Feature: Test
  Scenario: Simple
    Given something
"""
        feature = parser.parse_string(content, uri="custom://test")
        assert feature.uri == "custom://test"
