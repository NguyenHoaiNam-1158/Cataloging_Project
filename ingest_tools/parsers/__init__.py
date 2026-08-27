"""Parsers for converting raw extracted text into structured data."""

from parsers.table_parser import TableParser
from parsers.marc_spec_parser import MarcSpecParser
from parsers.dept_lookup_parser import DeptLookupParser
from parsers.rubric_parser import RubricParser

__all__ = ["TableParser", "MarcSpecParser", "DeptLookupParser", "RubricParser"]
