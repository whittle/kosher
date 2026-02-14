"""Gherkin parser module for Kosher.

This module provides functionality to parse Gherkin .feature files
and convert them to typed dataclasses for execution.
"""

from .exceptions import FeatureFileNotFoundError, GherkinParseError
from .gherkin import GherkinParser, parse_feature
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

__all__ = [
    # Main API
    "parse_feature",
    "GherkinParser",
    # Models
    "Feature",
    "Scenario",
    "Step",
    "StepType",
    "Tag",
    "DataTable",
    "DataTableRow",
    "DataTableCell",
    "DocString",
    # Exceptions
    "GherkinParseError",
    "FeatureFileNotFoundError",
]
