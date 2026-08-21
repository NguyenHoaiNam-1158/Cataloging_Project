#!/usr/bin/env python3
"""
run_dub.py – CLI chuyển đổi MARC21 → Dublin Core

Hỗ trợ đầu vào:
  - File MARC-in-JSON (.json) – list các record từ pymarc record.as_dict()

Đầu ra (mặc định: cả hai):
  - Dublin Core XML  (.xml) – chuẩn OAI_DC
  - Dublin Core JSON (.json)

Cách dùng:
  python run_dub.py path/to/MARC21_file.json
  python run_dub.py path/to/MARC21_file.json --format xml
  python run_dub.py path/to/MARC21_file.json --format json
  python run_dub.py path/to/MARC21_file.json --output-dir ./output
"""

import argparse
import json
import os
import sys
from typing import List

from modules.dublincore.dc_serializer import serialize_to_json, serialize_to_xml
from modules.dublincore.marc21_to_dc import Marc21ToDublinCoreConverter
from modules.dublincore.models import DublinCoreRecord


def load_marc_json(path: str) -> List[dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return [data]
    return data


def convert_all(records: List[dict]) -> List[DublinCoreRecord]:
    converter = Marc21ToDublinCoreConverter()
    return [converter.convert(rec) for rec in records]


def write_output(dc_records: List[DublinCoreRecord], base_name: str, output_dir: str, fmt: str):
    os.makedirs(output_dir, exist_ok=True)

    if fmt in ("xml", "all"):
        xml_content = serialize_to_xml(dc_records)
        xml_path = os.path.join(output_dir, f"{base_name}_dc.xml")
        with open(xml_path, "w", encoding="utf-8") as f:
            f.write(xml_content)
        print(f"Đã ghi DC XML: {xml_path}")

    if fmt in ("json", "all"):
        json_content = serialize_to_json(dc_records)
        json_path = os.path.join(output_dir, f"{base_name}_dc.json")
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(json_content)
        print(f"Đã ghi DC JSON: {json_path}")


def main():
    parser = argparse.ArgumentParser(description="Chuyển đổi MARC21 → Dublin Core")
    parser.add_argument("input", help="File MARC-in-JSON (.json)")
    parser.add_argument(
        "--format",
        choices=["xml", "json", "all"],
        default="all",
        help="Định dạng đầu ra (mặc định: cả hai)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Thư mục đầu ra (mặc định: cùng thư mục với file input)",
    )
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Lỗi: Không tìm thấy file: {args.input}", file=sys.stderr)
        sys.exit(1)

    base_name = os.path.splitext(os.path.basename(args.input))[0]
    output_dir = args.output_dir or os.path.dirname(os.path.abspath(args.input))

    marc_records = load_marc_json(args.input)
    dc_records = convert_all(marc_records)

    if not dc_records:
        print("Không có bản ghi nào để chuyển đổi.")
        sys.exit(0)

    print(f"Đã chuyển đổi {len(dc_records)} bản ghi MARC21 → Dublin Core")
    write_output(dc_records, base_name, output_dir, args.format)


if __name__ == "__main__":
    main()
