"""Exceptions for Gherkin parsing."""


class GherkinParseError(Exception):
    """Error parsing Gherkin syntax.

    Attributes:
        message: The error message.
        line: Line number where the error occurred (1-indexed).
        column: Column number where the error occurred (1-indexed).
    """

    def __init__(
        self,
        message: str,
        line: int | None = None,
        column: int | None = None,
    ) -> None:
        self.message = message
        self.line = line
        self.column = column

        location = ""
        if line is not None:
            location = f" at line {line}"
            if column is not None:
                location = f" at line {line}, column {column}"

        super().__init__(f"{message}{location}")


class FeatureFileNotFoundError(Exception):
    """Feature file not found at the specified path.

    Attributes:
        path: The path that was not found.
    """

    def __init__(self, path: str) -> None:
        self.path = path
        super().__init__(f"Feature file not found: {path}")
