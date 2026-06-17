import datetime
import json
import uuid
import threading
from pathlib import Path
from typing import List

from pymarc import Field, Subfield

from mapping_module.core.base_mapper import BaseFieldMapper
from mapping_module.core.models import RawExtractionData
from mapping_module.config.settings import Settings


class ControlFieldMapper(BaseFieldMapper):

    _counter_lock = threading.Lock()

    def can_handle(self, raw_data: RawExtractionData) -> bool:
        return True

    def map_field(self, raw_data: RawExtractionData) -> List[Field]:
        return [
            Field(tag="001", data=self._create_control_number(raw_data)),
            Field(tag="005", data=self._current_transaction_date()),
            Field(tag="008", data=self._build_fixed_length_field(raw_data)),
            Field(tag="040", indicators=[" ", " "],
                subfields=[
                    Subfield("a", "DHYD"),
                    Subfield("b", "vie"),
                    Subfield("c", "DHYD"),
                    Subfield("e", "AACR2"),
                ]),
            Field(tag="041",
                indicators=["0", " "],
                subfields=[
                    Subfield("a", "vie")
                ])
        ]

    def _create_control_number(self, raw_data: RawExtractionData) -> str:
        prefix = "YD"
        year_prefix = datetime.datetime.now().strftime("%y")
        sequence = self._next_sequence_number(year_prefix)
        width = getattr(Settings, "CONTROL_NUMBER_SEQ_WIDTH", 5)
        return f"{prefix}{year_prefix}{sequence:0{width}d}"

    def _next_sequence_number(self, year_prefix: str) -> int:
        counter_path = Path(
            getattr(Settings, "CONTROL_NUMBER_COUNTER_FILE", "control_number_counter.json")
        )
        with self._counter_lock:
            data = {}
            if counter_path.exists():
                try:
                    data = json.loads(counter_path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    data = {}

            current = int(data.get(year_prefix, 0)) + 1
            data[year_prefix] = current

            counter_path.parent.mkdir(parents=True, exist_ok=True)
            counter_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            return current

    def _current_transaction_date(self) -> str:
        return datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S.0")

    def _build_fixed_length_field(self, raw_data: RawExtractionData) -> str:
        date_entered = datetime.datetime.utcnow().strftime("%y%m%d")  
        date_type = "s"                                               

        date1 = raw_data.publication_year or "    "                   
        if date1 and len(date1) >= 4:
            date1 = date1[:4]
        else:
            date1 = "    "

        date2 = "    "                                                
        place_code = Settings.DEFAULT_COUNTRY_CODE.strip().ljust(3)[:3]  

        material = list(" " * 17)
        doc_type_code = self._resolve_doc_type_code(raw_data)
        if doc_type_code:
            for i, ch in enumerate(doc_type_code[:4]):
                material[5 + i] = ch
        material = "".join(material)

        language = getattr(Settings, "DEFAULT_LANGUAGE_CODE", "vie").strip().ljust(3)[:3] 
        modified_record = " "                                         
        cataloging_source = "d"                                       

        fixed = (
            date_entered + date_type + date1 + date2 + place_code
            + material + language + modified_record + cataloging_source
        )
        return fixed[:40].ljust(40)

    def _resolve_doc_type_code(self, raw_data: RawExtractionData) -> str:
        if raw_data.document_type:
            key = raw_data.document_type.strip().lower()
            if key in Settings.DOC_TYPE_008_MAP:
                return Settings.DOC_TYPE_008_MAP[key]

        normalized = raw_data.document_type or raw_data.nature_of_content or ""
        normalized = normalized.replace(" ", "_").lower().strip()
        return Settings.DOC_TYPE_008_MAP.get(normalized, "    ")