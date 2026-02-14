"""Core unit tests for the Gherkin parser."""

from collections.abc import Callable
from pathlib import Path

import pytest

from kosher.parser import (
    FeatureFileNotFoundError,
    GherkinParseError,
    GherkinParser,
    StepType,
    parse_feature,
)


class TestBasicParsing:
    """Test basic feature parsing functionality."""

    @property
    def simple_feature_content(self) -> str:
        """Basic feature with one scenario."""
        return """
        Feature: User Login
          Scenario: Successful login
            Given I am on the login page
            When I enter "user@example.com"
            Then I should see "Welcome"
        """

    def test_parse_feature_name(
        self,
        feature_file_factory: Callable[[str, str], Path],
    ) -> None:
        """Feature name is extracted correctly."""
        path = feature_file_factory("login.feature", self.simple_feature_content)

        feature = parse_feature(path)

        assert feature.name == "User Login"

    def test_parse_feature_uri(
        self,
        feature_file_factory: Callable[[str, str], Path],
    ) -> None:
        """Feature uri matches the file path."""
        path = feature_file_factory("login.feature", self.simple_feature_content)

        feature = parse_feature(path)

        assert feature.uri == str(path)

    def test_parse_scenario_name(
        self,
        feature_file_factory: Callable[[str, str], Path],
    ) -> None:
        """Scenario name is extracted correctly."""
        path = feature_file_factory("login.feature", self.simple_feature_content)

        feature = parse_feature(path)

        assert len(feature.scenarios) == 1
        assert feature.scenarios[0].name == "Successful login"

    def test_parse_step_text(
        self,
        feature_file_factory: Callable[[str, str], Path],
    ) -> None:
        """Step text is extracted without keyword."""
        path = feature_file_factory("login.feature", self.simple_feature_content)

        feature = parse_feature(path)

        steps = feature.scenarios[0].steps
        assert steps[0].text == "I am on the login page"
        assert steps[1].text == 'I enter "user@example.com"'
        assert steps[2].text == 'I should see "Welcome"'

    def test_parse_step_keywords(
        self,
        feature_file_factory: Callable[[str, str], Path],
    ) -> None:
        """Step keywords are preserved."""
        path = feature_file_factory("login.feature", self.simple_feature_content)

        feature = parse_feature(path)

        steps = feature.scenarios[0].steps
        assert steps[0].keyword == "Given "
        assert steps[1].keyword == "When "
        assert steps[2].keyword == "Then "

    def test_parse_step_types(
        self,
        feature_file_factory: Callable[[str, str], Path],
    ) -> None:
        """Step types are mapped correctly."""
        path = feature_file_factory("login.feature", self.simple_feature_content)

        feature = parse_feature(path)

        steps = feature.scenarios[0].steps
        assert steps[0].step_type == StepType.CONTEXT
        assert steps[1].step_type == StepType.ACTION
        assert steps[2].step_type == StepType.OUTCOME

    def test_step_full_text_format(
        self,
        feature_file_factory: Callable[[str, str], Path],
    ) -> None:
        """Step.full_text matches expected LLM format."""
        path = feature_file_factory("login.feature", self.simple_feature_content)

        feature = parse_feature(path)

        steps = feature.scenarios[0].steps
        assert steps[0].full_text == "Given I am on the login page"
        assert steps[1].full_text == 'When I enter "user@example.com"'
        assert steps[2].full_text == 'Then I should see "Welcome"'


class TestScenarioOutlines:
    """Test scenario outline expansion."""

    @property
    def feature_with_scenario_outline(self) -> str:
        """Feature with scenario outline and examples."""
        return """
        Feature: Login Validation
          Scenario Outline: Login with various credentials
            Given I am on the login page
            When I enter "<email>" and "<password>"
            Then I should see "<message>"

            Examples:
              | email            | password | message       |
              | user@example.com | secret   | Welcome       |
              | bad@example.com  | wrong    | Invalid login |
        """

    def test_outline_expands_to_multiple_scenarios(
        self,
        feature_file_factory: Callable[[str, str], Path],
    ) -> None:
        """Scenario outline creates one scenario per example row."""
        path = feature_file_factory(
            "outline.feature", self.feature_with_scenario_outline
        )

        feature = parse_feature(path)

        assert len(feature.scenarios) == 2

    def test_outline_substitutes_placeholders(
        self,
        feature_file_factory: Callable[[str, str], Path],
    ) -> None:
        """Placeholders are replaced with example values."""
        path = feature_file_factory(
            "outline.feature", self.feature_with_scenario_outline
        )

        feature = parse_feature(path)

        # First scenario from first example row
        scenario1 = feature.scenarios[0]
        assert "user@example.com" in scenario1.steps[1].text
        assert "secret" in scenario1.steps[1].text
        assert "Welcome" in scenario1.steps[2].text
        # Second scenario from second example row
        scenario2 = feature.scenarios[1]
        assert "bad@example.com" in scenario2.steps[1].text
        assert "wrong" in scenario2.steps[1].text
        assert "Invalid login" in scenario2.steps[2].text


class TestDataTables:
    """Test data table parsing."""

    @property
    def feature_with_data_table(self) -> str:
        """Feature with a step containing a data table."""
        return """
        Feature: User Registration
          Scenario: Register new user
            Given the following users exist:
              | name  | email            |
              | Alice | alice@test.com   |
              | Bob   | bob@test.com     |
            When I submit the registration form
            Then the user should be created
        """

    def test_step_has_data_table(
        self,
        feature_file_factory: Callable[[str, str], Path],
    ) -> None:
        """Steps with data tables have data_table attribute set."""
        path = feature_file_factory("data.feature", self.feature_with_data_table)

        feature = parse_feature(path)

        step = feature.scenarios[0].steps[0]
        assert step.data_table is not None

    def test_data_table_rows(
        self,
        feature_file_factory: Callable[[str, str], Path],
    ) -> None:
        """Data table has correct number of rows."""
        path = feature_file_factory("data.feature", self.feature_with_data_table)

        feature = parse_feature(path)

        table = feature.scenarios[0].steps[0].data_table
        assert table is not None
        # Header row + 2 data rows
        assert len(table.rows) == 3

    def test_data_table_as_dicts(
        self,
        feature_file_factory: Callable[[str, str], Path],
    ) -> None:
        """DataTable.as_dicts() converts to list of dicts."""
        path = feature_file_factory("data.feature", self.feature_with_data_table)

        feature = parse_feature(path)

        table = feature.scenarios[0].steps[0].data_table
        assert table is not None
        dicts = table.as_dicts()
        assert len(dicts) == 2
        assert dicts[0] == {"name": "Alice", "email": "alice@test.com"}
        assert dicts[1] == {"name": "Bob", "email": "bob@test.com"}


class TestDocStrings:
    """Test doc string parsing."""

    @property
    def feature_with_doc_string(self) -> str:
        """Feature with a step containing a doc string."""
        return '''Feature: API Testing
          Scenario: Send JSON request
            Given I have the following JSON payload:
              """json
              {
                "name": "test",
                "value": 123
              }
              """
            When I send the request
            Then I should get a 200 response
        '''

    def test_step_has_doc_string(
        self,
        feature_file_factory: Callable[[str, str], Path],
    ) -> None:
        """Steps with doc strings have doc_string attribute set."""
        path = feature_file_factory("doc.feature", self.feature_with_doc_string)

        feature = parse_feature(path)

        step = feature.scenarios[0].steps[0]
        assert step.doc_string is not None

    def test_doc_string_content(
        self,
        feature_file_factory: Callable[[str, str], Path],
    ) -> None:
        """Doc string content is extracted correctly."""
        path = feature_file_factory("doc.feature", self.feature_with_doc_string)

        feature = parse_feature(path)

        doc = feature.scenarios[0].steps[0].doc_string
        assert doc is not None
        assert '"name": "test"' in doc.content
        assert '"value": 123' in doc.content

    def test_doc_string_media_type(
        self,
        feature_file_factory: Callable[[str, str], Path],
    ) -> None:
        """Doc string media type is extracted."""
        path = feature_file_factory("doc.feature", self.feature_with_doc_string)

        feature = parse_feature(path)

        doc = feature.scenarios[0].steps[0].doc_string
        assert doc is not None
        assert doc.media_type == "json"


class TestBackground:
    """Test background step handling."""

    def test_background_prepended_to_scenarios(
        self,
        feature_file_factory: Callable[[str, str], Path],
    ) -> None:
        """Background steps are prepended to each scenario."""
        feature_with_background = """
        Feature: Shopping Cart
           Background:
             Given I am logged in as a customer

           Scenario: Add item to cart
             When I click "Add to Cart"
             Then I should see "Item added"

           Scenario: Remove item from cart
             When I click "Remove"
             Then I should see "Item removed"
         """
        path = feature_file_factory("bg.feature", feature_with_background)

        feature = parse_feature(path)

        # Both scenarios should have the background step first
        for scenario in feature.scenarios:
            assert scenario.steps[0].text == "I am logged in as a customer"
            assert scenario.steps[0].step_type == StepType.CONTEXT


class TestTags:
    """Test tag parsing."""

    @property
    def feature_with_tags(self) -> str:
        """Feature with feature-level and scenario-level tags."""
        return """
        @smoke @regression
        Feature: Tagged Feature

          @critical
          Scenario: Important test
            Given I am ready
            Then everything works

          @slow
          Scenario: Slow test
            Given I wait a long time
            Then it completes
        """

    def test_feature_level_tags(
        self, feature_file_factory: Callable[[str, str], Path]
    ) -> None:
        """Feature-level tags are extracted."""
        path = feature_file_factory("tags.feature", self.feature_with_tags)

        feature = parse_feature(path)

        tag_names = {t.name for t in feature.tags}
        assert "@smoke" in tag_names
        assert "@regression" in tag_names

    def test_scenario_level_tags(
        self, feature_file_factory: Callable[[str, str], Path]
    ) -> None:
        """Scenario-level tags are extracted."""
        path = feature_file_factory("tags.feature", self.feature_with_tags)

        feature = parse_feature(path)

        scenario1_tags = {t.name for t in feature.scenarios[0].tags}
        assert "@critical" in scenario1_tags
        scenario2_tags = {t.name for t in feature.scenarios[1].tags}
        assert "@slow" in scenario2_tags

    def test_tag_inheritance(
        self, feature_file_factory: Callable[[str, str], Path]
    ) -> None:
        """Scenarios inherit feature-level tags."""
        path = feature_file_factory("tags.feature", self.feature_with_tags)

        feature = parse_feature(path)

        # Each scenario should have feature tags plus its own
        for scenario in feature.scenarios:
            tag_names = {t.name for t in scenario.tags}
            assert "@smoke" in tag_names
            assert "@regression" in tag_names


class TestAndButKeywords:
    """Test handling of And/But conjunction keywords."""

    def test_and_steps_have_context_action_outcome_types(
        self,
        feature_file_factory: Callable[[str, str], Path],
    ) -> None:
        """And/But steps inherit the type of their preceding step."""
        feature_with_and_but = """
        Feature: Conjunctions
          Scenario: Using And and But
            Given I am on the page
            And I am logged in
            When I click the button
            And I wait for loading
            Then I see the result
            But I do not see an error
        """
        path = feature_file_factory("conj.feature", feature_with_and_but)

        feature = parse_feature(path)

        steps = feature.scenarios[0].steps
        # Given + And -> both CONTEXT
        assert steps[0].step_type == StepType.CONTEXT  # Given
        assert steps[1].step_type == StepType.CONTEXT  # And (inherits from Given)
        # When + And -> both ACTION
        assert steps[2].step_type == StepType.ACTION  # When
        assert steps[3].step_type == StepType.ACTION  # And (inherits from When)
        # Then + But -> both OUTCOME
        assert steps[4].step_type == StepType.OUTCOME  # Then
        assert steps[5].step_type == StepType.OUTCOME  # But (inherits from Then)


class TestErrorHandling:
    """Test error handling for invalid input."""

    def test_file_not_found_error(self, tmp_path: Path) -> None:
        """FeatureFileNotFoundError raised for missing files."""
        with pytest.raises(FeatureFileNotFoundError) as exc_info:
            parse_feature(tmp_path / "nonexistent.feature")
        assert "nonexistent.feature" in str(exc_info.value)

    def test_parse_error_for_invalid_syntax(
        self, feature_file_factory: Callable[[str, str], Path]
    ) -> None:
        """GherkinParseError raised for invalid Gherkin syntax."""
        # Unclosed doc string is truly invalid syntax
        invalid_content = '''
        Feature: Invalid
          Scenario: Bad
            Given something
              """
              Unclosed doc string
        '''
        path = feature_file_factory("invalid.feature", invalid_content)

        with pytest.raises(GherkinParseError):
            parse_feature(path)

    def test_parse_error_has_line_info(
        self, feature_file_factory: Callable[[str, str], Path]
    ) -> None:
        """GherkinParseError includes line number information."""
        # Unclosed doc string triggers error with line info
        invalid_content = '''
        Feature: Invalid
          Scenario: Bad
            Given something
              """
              Unclosed
        '''
        path = feature_file_factory("invalid.feature", invalid_content)

        with pytest.raises(GherkinParseError) as exc_info:
            parse_feature(path)

        assert exc_info.value.line is not None


class TestParserClass:
    """Test the GherkinParser class directly."""

    @property
    def simple_feature_content(self) -> str:
        """Basic feature with one scenario."""
        return """
        Feature: User Login
          Scenario: Successful login
            Given I am on the login page
            When I enter "user@example.com"
            Then I should see "Welcome"
        """

    def test_parse_string(self) -> None:
        """GherkinParser.parse_string works correctly."""
        parser = GherkinParser()

        feature = parser.parse_string(self.simple_feature_content)

        assert feature.name == "User Login"
        assert len(feature.scenarios) == 1

    def test_parse_string_with_uri(self) -> None:
        """GherkinParser.parse_string uses provided URI."""
        parser = GherkinParser()

        feature = parser.parse_string(self.simple_feature_content, uri="test://custom")

        assert feature.uri == "test://custom"

    def test_parser_reusable(self) -> None:
        """GherkinParser can parse multiple features."""
        parser = GherkinParser()

        feature1 = parser.parse_string(self.simple_feature_content, uri="first")
        feature2 = parser.parse_string(self.simple_feature_content, uri="second")

        assert feature1.uri == "first"
        assert feature2.uri == "second"
