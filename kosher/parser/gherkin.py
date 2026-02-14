"""Gherkin parser wrapping the gherkin-official library."""

from pathlib import Path
from typing import cast

from gherkin.errors import CompositeParserException, ParserError
from gherkin.parser import Parser
from gherkin.pickles.compiler import (
    Compiler,
    GherkinDocumentWithURI,
    Pickle,
    PickleArgumentDataTableEnvelope,
    PickleArgumentDocStringEnvelope,
    PickleStep,
)

from .exceptions import FeatureFileNotFoundError, GherkinParseError
from .models import (
    DataTable,
    DataTableCell,
    DataTableRow,
    DocString,
    Feature,
    Scenario,
    Step,
    StepType,
    Tag,
)

# Map gherkin-official keywordType to our StepType
_KEYWORD_TYPE_MAP: dict[str, StepType] = {
    "Context": StepType.CONTEXT,
    "Action": StepType.ACTION,
    "Outcome": StepType.OUTCOME,
    "Conjunction": StepType.CONJUNCTION,
    "Unknown": StepType.UNKNOWN,
}

# Map StepType to display keyword for LLM
_STEP_TYPE_TO_KEYWORD: dict[StepType, str] = {
    StepType.CONTEXT: "Given ",
    StepType.ACTION: "When ",
    StepType.OUTCOME: "Then ",
    StepType.CONJUNCTION: "And ",
    StepType.UNKNOWN: "* ",
}


class GherkinParser:
    """Parser for Gherkin .feature files.

    Wraps the gherkin-official library and converts its output to typed
    dataclasses. Uses Pickles for execution (auto-expands Scenario Outlines).
    """

    def __init__(self) -> None:
        self._parser = Parser()
        self._compiler = Compiler()

    def parse_file(self, path: str | Path) -> Feature:
        """Parse a .feature file.

        Args:
            path: Path to the .feature file.

        Returns:
            Parsed Feature object.

        Raises:
            FeatureFileNotFoundError: If the file does not exist.
            GherkinParseError: If the file contains invalid Gherkin syntax.
        """
        path = Path(path)
        if not path.exists():
            raise FeatureFileNotFoundError(str(path))

        content = path.read_text(encoding="utf-8")
        return self.parse_string(content, uri=str(path))

    def parse_string(self, content: str, uri: str = "<string>") -> Feature:
        """Parse Gherkin content from a string.

        Args:
            content: Gherkin content as a string.
            uri: URI to use for error messages and the feature's uri field.

        Returns:
            Parsed Feature object.

        Raises:
            GherkinParseError: If the content contains invalid Gherkin syntax.
        """
        try:
            gherkin_document = self._parser.parse(content)
        except CompositeParserException as e:
            # Multiple errors - report the first one
            first_error = e.errors[0]
            raise GherkinParseError(
                str(first_error.args[0]),
                line=first_error.location.get("line"),
                column=first_error.location.get("column"),
            ) from e
        except ParserError as e:
            raise GherkinParseError(str(e)) from e

        # Add URI for the compiler
        doc_with_uri = cast(GherkinDocumentWithURI, gherkin_document)
        doc_with_uri["uri"] = uri

        # Check for empty or featureless documents
        if "feature" not in gherkin_document:
            return Feature(
                name="",
                description="",
                scenarios=(),
                uri=uri,
                language="en",
                tags=(),
            )

        feature_ast = gherkin_document["feature"]

        # Compile to pickles (expands Scenario Outlines)
        pickles = self._compiler.compile(doc_with_uri)

        # Convert pickles to our model
        scenarios = tuple(self._convert_pickle(pickle) for pickle in pickles)

        # Extract feature-level tags
        feature_tags = tuple(Tag(name=t["name"]) for t in feature_ast["tags"])

        return Feature(
            name=feature_ast["name"],
            description=feature_ast["description"],
            scenarios=scenarios,
            uri=uri,
            language=feature_ast["language"],
            tags=feature_tags,
        )

    def _convert_pickle(self, pickle: Pickle) -> Scenario:
        """Convert a gherkin Pickle to our Scenario model."""
        steps = tuple(self._convert_pickle_step(step) for step in pickle["steps"])
        tags = tuple(Tag(name=t["name"]) for t in pickle["tags"])

        return Scenario(
            name=pickle["name"],
            steps=steps,
            tags=tags,
        )

    def _convert_pickle_step(self, pickle_step: PickleStep) -> Step:
        """Convert a gherkin PickleStep to our Step model."""
        # Map the type to our StepType enum
        step_type = _KEYWORD_TYPE_MAP.get(pickle_step["type"], StepType.UNKNOWN)

        # Generate keyword from type for LLM display
        keyword = _STEP_TYPE_TO_KEYWORD.get(step_type, "* ")

        # Extract data table if present
        data_table: DataTable | None = None
        doc_string: DocString | None = None

        if "argument" in pickle_step:
            argument = pickle_step["argument"]
            if "dataTable" in argument:
                dt_envelope = cast(PickleArgumentDataTableEnvelope, argument)
                data_table = self._convert_data_table(dt_envelope)
            elif "docString" in argument:
                ds_envelope = cast(PickleArgumentDocStringEnvelope, argument)
                data_table_raw = ds_envelope["docString"]
                doc_string = DocString(
                    content=data_table_raw["content"] or "",
                    media_type=data_table_raw.get("mediaType"),
                )

        return Step(
            keyword=keyword,
            text=pickle_step["text"],
            step_type=step_type,
            data_table=data_table,
            doc_string=doc_string,
        )

    def _convert_data_table(
        self, envelope: PickleArgumentDataTableEnvelope
    ) -> DataTable:
        """Convert a gherkin data table to our DataTable model."""
        rows = []
        for row in envelope["dataTable"]["rows"]:
            cells = tuple(DataTableCell(value=cell["value"]) for cell in row["cells"])
            rows.append(DataTableRow(cells=cells))

        return DataTable(rows=tuple(rows))


def parse_feature(path: str | Path) -> Feature:
    """Parse a .feature file.

    Convenience function that creates a GherkinParser and parses the file.

    Args:
        path: Path to the .feature file.

    Returns:
        Parsed Feature object.

    Raises:
        FeatureFileNotFoundError: If the file does not exist.
        GherkinParseError: If the file contains invalid Gherkin syntax.
    """
    return GherkinParser().parse_file(path)
