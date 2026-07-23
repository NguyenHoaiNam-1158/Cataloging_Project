import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from dublin_core_module.core.dc_record import DublinCoreRecord
from dublin_core_module.pipeline.dc_pipeline import DublinCorePipeline
from dublin_core_module.validator import DublinCoreValidator

DCResult = Dict[str, List[str]]


class DublinCoreConverter:
    
    def __init__(
        self,
        pipeline: Optional[DublinCorePipeline] = None,
        validator: Optional[DublinCoreValidator] = None,
    ):
        self.pipeline = pipeline or DublinCorePipeline()
        self.validator = validator or DublinCoreValidator()

    def convert(self, raw: Dict[str, Any], drop_empty: bool = False) -> DCResult:
        record = self.pipeline.build(raw)
        return record.to_dict(drop_empty=drop_empty)

    def convert_to_record(self, raw: Dict[str, Any]) -> DublinCoreRecord:
        return self.pipeline.build(raw)

    def convert_many(self, raws: List[Dict[str, Any]], drop_empty: bool = False) -> List[DCResult]:
        return [self.convert(r, drop_empty=drop_empty) for r in raws]

    def convert_file(
        self,
        input_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        drop_empty: bool = False,
    ) -> Union[DCResult, List[DCResult]]:
        payload = self._load(input_path)

        if isinstance(payload, list):
            result: Union[DCResult, List[DCResult]] = self.convert_many(payload, drop_empty)
        else:
            result = self.convert(payload, drop_empty=drop_empty)

        if output_path:
            self._write_json(result, output_path)
        return result

    def process_raw_dict(
        self,
        raw_data: Dict[str, Any],
        output_json: Optional[Union[str, Path]] = None,
        drop_empty: bool = False,
    ) -> DCResult:
        result = self.convert(raw_data, drop_empty=drop_empty)
        if output_json:
            self._write_json(result, output_json)
        return result

    @staticmethod
    def _load(input_path: Union[str, Path]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        path = Path(input_path)
        if not path.exists():
            raise FileNotFoundError(f"Không tìm thấy file raw: {input_path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list) and len(payload) == 1:
            return payload[0]
        if not isinstance(payload, (dict, list)):
            raise ValueError("File raw phải là JSON object hoặc list.")
        return payload

    @staticmethod
    def _write_json(data: Any, output_path: Union[str, Path]) -> None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
