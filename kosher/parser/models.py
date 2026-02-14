"""Data models for parsed Gherkin features."""

from dataclasses import dataclass
from enum import Enum


class StepType(Enum):
    """Semantic type of a Gherkin step."""

    CONTEXT = "context"  # Given
    ACTION = "action"  # When
    OUTCOME = "outcome"  # Then
    CONJUNCTION = "conjunction"  # And/But
    UNKNOWN = "unknown"  # * or unrecognized


@dataclass(frozen=True)
class Tag:
    """A Gherkin tag (e.g., @smoke, @wip)."""

    name: str


@dataclass(frozen=True)
class DataTableCell:
    """A cell in a data table."""

    value: str


@dataclass(frozen=True)
class DataTableRow:
    """A row in a data table."""

    cells: tuple[DataTableCell, ...]


@dataclass(frozen=True)
class DataTable:
    """A data table attached to a step."""

    rows: tuple[DataTableRow, ...]

    def as_dicts(self) -> list[dict[str, str]]:
        """Convert table to list of dicts using first row as headers.

        Returns:
            List of dictionaries where keys are header values and
            values are corresponding cell values for each data row.

        Raises:
            ValueError: If the table has no rows (no headers).
        """
        if not self.rows:
            raise ValueError("Cannot convert empty table to dicts")
        if len(self.rows) < 2:
            return []

        headers = [cell.value for cell in self.rows[0].cells]
        return [
            {headers[i]: cell.value for i, cell in enumerate(row.cells)}
            for row in self.rows[1:]
        ]


@dataclass(frozen=True)
class DocString:
    """A doc string attached to a step."""

    content: str
    media_type: str | None = None


@dataclass(frozen=True)
class Step:
    """A single Gherkin step."""

    keyword: str  # "Given ", "When ", etc. (includes trailing space)
    text: str  # Step text without keyword
    step_type: StepType
    data_table: DataTable | None = None
    doc_string: DocString | None = None

    @property
    def full_text(self) -> str:
        """Return 'Given I am on...' format expected by LLM."""
        return f"{self.keyword.strip()} {self.text}"


@dataclass(frozen=True)
class Scenario:
    """A Gherkin scenario (or expanded scenario outline instance)."""

    name: str
    steps: tuple[Step, ...]
    tags: tuple[Tag, ...] = ()


@dataclass(frozen=True)
class Feature:
    """A parsed Gherkin feature."""

    name: str
    description: str
    scenarios: tuple[Scenario, ...]
    uri: str = ""
    language: str = "en"
    tags: tuple[Tag, ...] = ()
