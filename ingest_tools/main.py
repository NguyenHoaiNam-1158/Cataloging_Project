"""CLI entry point for PDF to CSV/JSON ingest pipeline."""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from extractors.pdf_extractor import PDFExtractor
from parsers.table_parser import TableParser
from parsers.dept_lookup_parser import DeptLookupParser
from parsers.marc_spec_parser import MarcSpecParser
from parsers.rubric_parser import RubricParser
from exporters.csv_exporter import CSVExporter
from exporters.json_exporter import JSONExporter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("ingest_tools")

PARSER_MAP = {
    "phu_luc_6": "dept",
    "departments": "dept",
    "marc_spec": "marc",
    "marc": "marc",
    "rubric": "rubric",
    "generic": "generic",
}


def cmd_ingest(args):
    pdf_path = args.input
    parser_type = PARSER_MAP.get(args.type, args.type)
    output_path = args.output

    logger.info(f"Ingesting: {pdf_path} (type={parser_type})")

    extractor = PDFExtractor()
    result = extractor.extract(pdf_path, pages=args.pages)

    if result.is_image_only and not args.no_ai:
        logger.info("PDF is image-only, falling back to AI extraction")
        try:
            from ai_extractor import AIExtractor
            ai = AIExtractor()
            records = ai.extract_from_pdf(pdf_path)
        except Exception as e:
            logger.error(f"AI extraction failed: {e}")
            logger.info("Try: set GEMINI_API_KEY in .env, or use --no-ai to skip")
            return
    elif result.is_image_only and args.no_ai:
        logger.error("PDF is image-only and AI extraction disabled. Cannot proceed.")
        return
    else:
        records = _parse_extracted_data(result, parser_type)

    if not records:
        logger.warning("No records extracted. Check the PDF content.")
        return

    logger.info(f"Extracted {len(records)} records")

    if output_path is None:
        stem = Path(pdf_path).stem
        output_path = str(Path(pdf_path).parent / f"{stem}.csv")

    if output_path.endswith(".json"):
        exporter = JSONExporter()
        exporter.export_with_metadata(records, output_path, source_file=pdf_path, parser_used=parser_type)
    else:
        exporter = CSVExporter()
        if parser_type == "dept":
            exporter.export_phu_luc_6(records, output_path)
        else:
            exporter.export(records, output_path)

    logger.info(f"Done! Output: {output_path}")


def cmd_validate_dept(args):
    pdf_path = args.input
    existing_path = args.existing

    extractor = PDFExtractor()
    result = extractor.extract(pdf_path, pages=args.pages)
    records = _parse_extracted_data(result, "dept")

    if not records:
        logger.warning("No records extracted from PDF.")
        return

    parser = DeptLookupParser()
    diff = parser.validate_against_existing(records, existing_path)

    output_path = args.output or str(
        Path(pdf_path).parent / f"{Path(pdf_path).stem}_diff.json"
    )

    exporter = JSONExporter()
    exporter.export(diff, output_path)

    logger.info(f"Added: {len(diff['added'])}")
    logger.info(f"Removed: {len(diff['removed'])}")
    logger.info(f"Modified: {len(diff['modified'])}")
    logger.info(f"Diff report: {output_path}")


def _parse_extracted_data(result, parser_type: str):
    if result.tables:
        if parser_type == "dept":
            parser = DeptLookupParser()
            return parser.parse_tables(result.tables)
        table_parser = TableParser()
        return table_parser.parse_from_tables(result.tables)

    if parser_type == "dept":
        parser = DeptLookupParser()
        return parser.parse(result.raw_text)
    elif parser_type == "marc":
        parser = MarcSpecParser()
        return parser.parse(result.raw_text)
    elif parser_type == "rubric":
        parser = RubricParser()
        return parser.parse(result.raw_text)
    else:
        table_parser = TableParser()
        return table_parser.parse_from_text(result.raw_text)


def main():
    parser = argparse.ArgumentParser(
        prog="ingest",
        description="Ingest PDF documents to CSV/JSON for library cataloging.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    ingest_parser = subparsers.add_parser(
        "ingest", help="Ingest a PDF file to CSV or JSON"
    )
    ingest_parser.add_argument("input", help="Path to input PDF file")
    ingest_parser.add_argument(
        "-o", "--output", help="Output file path (.csv or .json)"
    )
    ingest_parser.add_argument(
        "-t",
        "--type",
        choices=["phu_luc_6", "departments", "marc_spec", "marc", "rubric", "generic"],
        default="generic",
        help="Document type (default: generic)",
    )
    ingest_parser.add_argument(
        "--pages", nargs="+", type=int, help="Specific pages to extract (1-based)"
    )
    ingest_parser.add_argument(
        "--no-ai", action="store_true", help="Disable AI fallback for image PDFs"
    )
    ingest_parser.set_defaults(func=cmd_ingest)

    validate_parser = subparsers.add_parser(
        "validate-dept", help="Compare PDF data against existing departments.json"
    )
    validate_parser.add_argument("input", help="Path to input PDF file")
    validate_parser.add_argument(
        "-e", "--existing", required=True, help="Path to existing departments.json"
    )
    validate_parser.add_argument(
        "-o", "--output", help="Output diff file path (.json)"
    )
    validate_parser.add_argument(
        "--pages", nargs="+", type=int, help="Specific pages to extract (1-based)"
    )
    validate_parser.set_defaults(func=cmd_validate_dept)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
