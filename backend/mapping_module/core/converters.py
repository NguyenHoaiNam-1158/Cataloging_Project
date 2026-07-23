from pathlib import Path
from typing import Any, Optional
import json
from pymarc import MARCReader
from mapping_module.config.settings import Settings
from mapping_module.pipeline.marc_pipeline import MarcPipeline
from mapping_module.core.serializers import MARCFieldSerializer
from mapping_module.utils import pdf_extractor


class DocumentConverter:
    def __init__(self):
        self.pipeline = MarcPipeline()
        self.serializer = MARCFieldSerializer()

    def json_to_marc(
        self,
        input_path: str,
        output_mrc: str,
        output_json: Optional[str] = None,
        output_xml: Optional[str] = None,
    ) -> None:
        try:
            lcc_path = Path(Settings.LCC_OUTPUT_FILE)
            if not lcc_path.exists():
                Settings.log.info(f"⚙️ LCC index chưa tồn tại, đang tự động trích xuất từ PDF vào {lcc_path}...")
                pdf_extractor.extract_all_lcc(Settings.PDF_FOLDER, str(lcc_path))
        except Exception as exc:
            Settings.log.warning(f"⚠️ Không thể tự động tạo LCC index: {exc}")

        raw_data = self.pipeline.load_json(input_path)
        # [VÁ M12] lấy cả object đã làm giàu để đọc confidence
        record, enriched = self.pipeline.build_record_with_data(raw_data)

        output_mrc_path = output_mrc or "output.mrc"
        self.pipeline.write_marc21(record, output_mrc_path)
        print(f"Đã ghi MARC21 vào: {output_mrc_path}")

        if output_json:
            evaluation_metrics = self._collect_confidence_metrics(enriched)
            self._write_record_json(record, output_json, evaluation_metrics)
            print(f"Đã ghi MARC record JSON kèm chỉ số chính xác vào: {output_json}")

        if output_xml:
            self.pipeline.write_marcxml(record, output_xml)
            print(f"Đã ghi MARCXML vào: {output_xml}")

    def process_raw_dict(
        self,
        raw_data: dict,
        output_mrc: str,
        output_json: Optional[str] = None
    ) -> dict:
        """Xử lý trực tiếp dữ liệu dict trích xuất từ AI, chuyển đổi sang biểu ghi MARC21.
        Ghi ra file .mrc, file .json kiểm chuẩn và trả về dữ liệu dạng dict cho hệ thống.
        """
        try:
            # 1. Dựng biểu ghi + lấy object đã làm giàu (chứa lcc/nlm + confidence)
            record, enriched = self.pipeline.build_record_with_data(raw_data)

            # 2. Ghi biểu ghi ra file nhị phân .mrc chuẩn thư viện
            output_mrc_path = output_mrc or "output.mrc"
            self.pipeline.write_marc21(record, output_mrc_path)

            # 3. Nếu có yêu cầu xuất file JSON kết quả kèm chỉ số chính xác
            if output_json:
                evaluation_metrics = self._collect_confidence_metrics(enriched)
                self._write_record_json(record, output_json, evaluation_metrics)

            # 4. Trả về định dạng dict để main.py có thể dùng hiển thị hoặc phản hồi API
            return self.serializer.record_to_dict(record)

        except Exception as e:
            Settings.log.error(f"❌ Lỗi trong quá trình xử lý biên mục trực tiếp: {e}")
            raise e

    def mrc_to_json(self, input_path: str, output_path: str) -> None:
        input_file = Path(input_path)
        if not input_file.exists():
            raise FileNotFoundError(f"Không tìm thấy file MARC: {input_path}")

        records = []
        with input_file.open("rb") as handle:
            reader = MARCReader(handle)
            for record in reader:
                records.append(self.serializer.record_to_dict(record))

        data = records[0] if len(records) == 1 else records
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with output_file.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)

    @staticmethod
    def _get_attr(obj: Any, key: str) -> Any:
        """Đọc thuộc tính dù obj là dict hay pydantic model."""
        if isinstance(obj, dict):
            return obj.get(key)
        return getattr(obj, key, None)

    def save_edited_record(
        self,
        marc_dict: dict,
        output_mrc: str,
        output_json: Optional[str] = None,
    ) -> dict:
        """[VÁ F04] Ghi biểu ghi ĐÃ SỬA (dict {leader, fields}) xuống đĩa.

        Dùng khi thủ thư chỉnh sửa trên giao diện rồi bấm Lưu: dựng lại
        pymarc.Record từ dict, ghi đè .mrc và cập nhật _marc.json. Giữ lại
        ai_evaluation_metrics cũ nếu file JSON đã tồn tại (không xoá confidence).
        """
        record = self.serializer.record_from_dict(marc_dict)

        output_mrc_path = output_mrc or "output.mrc"
        self.pipeline.write_marc21(record, output_mrc_path)

        if output_json:
            metrics = {}
            json_path = Path(output_json)
            if json_path.exists():
                try:
                    old = json.loads(json_path.read_text(encoding="utf-8"))
                    metrics = old.get("ai_evaluation_metrics", {}) or {}
                except Exception:
                    metrics = {}
            self._write_record_json(record, output_json, metrics)

        return self.serializer.record_to_dict(record)

    def _collect_confidence_metrics(self, enriched: Any) -> dict:
        """[VÁ M12] Đọc mã phân loại + độ tin cậy từ object ĐÃ LÀM GIÀU trong
        pipeline (không phải từ dict thô đầu vào — nơi các trường này luôn rỗng).

        Mỗi phần tử lcc/nlm có thể là dict {code, description, confidence} hoặc
        ClassificationCodeModel — hàm xử lý được cả hai.
        """
        metrics: dict = {}

        def _first(items):
            return items[0] if isinstance(items, list) and items else None

        lcc_first = _first(self._get_attr(enriched, "lcc_classification"))
        if lcc_first is not None:
            metrics["Field_050_LCC_Code"] = self._get_attr(lcc_first, "code") or "N/A"
            metrics["Field_050_LCC_Confidence"] = self._get_attr(lcc_first, "confidence") or "N/A"

        nlm_first = _first(self._get_attr(enriched, "nlm_classification"))
        if nlm_first is not None:
            metrics["Field_060_NLM_Code"] = self._get_attr(nlm_first, "code") or "N/A"
            metrics["Field_060_NLM_Confidence"] = self._get_attr(nlm_first, "confidence") or "N/A"

        return metrics

    def _write_record_json(self, record, output_path: str, evaluation_metrics: Optional[dict] = None) -> None:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        combined_output = {
            "marc21_record": self.serializer.record_to_dict(record),
            "ai_evaluation_metrics": evaluation_metrics or {}
        }

        with open(output_file, "w", encoding="utf-8") as handle:
            json.dump(
                combined_output,
                handle,
                ensure_ascii=False,
                indent=2,
            )