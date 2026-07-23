# pipeline/marc_pipeline.py

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from pymarc import MARCWriter, Record

from mapping_module.core.models import RawExtractionData
from mapping_module.mappers import (
    AuthorCorporateMapper,
    ControlFieldMapper,
    IdentifierMapper,
    NoteMapper,
    PublicationPhysicalMapper,
    RAGEnrichedFieldMapper,
    RAGFieldMapper,
    TitleMapper,
    LocalFieldMapper,
)


class MarcPipeline:
    def __init__(self, mappers: Optional[list] = None):
        self.mappers = mappers or [
            ControlFieldMapper(),
            IdentifierMapper(),
            TitleMapper(),
            AuthorCorporateMapper(),
            PublicationPhysicalMapper(),
            NoteMapper(),
            RAGFieldMapper(),
            RAGEnrichedFieldMapper(),
            LocalFieldMapper(),
        ]

    def build_record_with_data(self, raw_data: Dict[str, Any]) -> Tuple[Record, RawExtractionData]:
        """Dựng biểu ghi VÀ trả về luôn object dữ liệu đã được các mapper làm giàu.

        [VÁ M12] RAGEnrichedFieldMapper gán lcc_classification/nlm_classification
        (kèm confidence) vào chính object `data` trong lúc chạy. Trước đây object
        này bị bỏ đi -> confidence không lấy lại được. Nay trả về cùng record.
        """
        data = RawExtractionData(**raw_data)
        record = Record()
        fields = []

        for mapper in self.mappers:
            if mapper.can_handle(data):
                fields.extend(mapper.map_field(data))

        fields.sort(key=lambda field: field.tag)
        for field in fields:
            record.add_field(field)

        return record, data

    def build_record(self, raw_data: Dict[str, Any]) -> Record:
        """Giữ nguyên chữ ký cũ cho nơi nào chỉ cần Record."""
        record, _ = self.build_record_with_data(raw_data)
        return record

    @staticmethod
    def load_json(source_path: str) -> Dict[str, Any]:
        path = Path(source_path)
        if not path.exists():
            raise FileNotFoundError(f"File không tìm thấy: {source_path}")

        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        if isinstance(payload, list) and len(payload) == 1:
            payload = payload[0]
        if not isinstance(payload, dict):
            raise ValueError("JSON phải là object hoặc list 1 phần tử")

        return payload

    @staticmethod
    def write_marc21(record: Record, path: str) -> None:
        """Ghi record thành MARC21 (nhị phân)."""
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as handle:
            writer = MARCWriter(handle)
            writer.write(record)
            writer.close()

    @staticmethod
    def write_marcxml(record: Record, path: str) -> None:
        """Ghi record thành MARCXML (text)."""
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with output_path.open("w", encoding="utf-8") as handle:
                handle.write(record.as_marcxml())
        except AttributeError:
            # [dọn M16] fallback nhị phân phải mở ở chế độ 'wb'
            with output_path.open("wb") as handle:
                handle.write(record.as_marc())