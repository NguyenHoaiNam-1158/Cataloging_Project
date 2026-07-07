import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("QWEN_API_KEY", "test-key")
os.environ.setdefault("USE_OCR", "false")

from modules.ocr_adapters.base_ocr_adapter import BaseOCRAdapter
from modules.ocr_adapters.paddle_ocr_adapter import PaddleOCRAdapter


def test_base_ocr_adapter_is_abstract():
    assert BaseOCRAdapter.__abstractmethods__ == {"process_pdf"}


def test_paddle_ocr_adapter_extends_base():
    assert issubclass(PaddleOCRAdapter, BaseOCRAdapter)


@patch("paddleocr.PaddleOCR")
def test_process_pdf_returns_markdown(mock_paddleocr):
    mock_page_result = MagicMock()
    mock_page_result.save_to_json = MagicMock()

    mock_ocr_instance = MagicMock()
    mock_ocr_instance.predict.return_value = [mock_page_result]
    mock_paddleocr.return_value = mock_ocr_instance

    with (
        tempfile.TemporaryDirectory() as model_dir,
        tempfile.TemporaryDirectory() as output_dir,
    ):
        json_path = Path(model_dir) / "page_1_result.json"
        fake_json = {
            "rec_texts": ["Dòng 1", "Dòng 2"],
            "rec_boxes": [[0, 0, 100, 20], [0, 30, 100, 50]],
            "page_index": 0,
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(fake_json, f)

        def save_json_side_effect(path):
            import shutil
            shutil.copy(str(json_path), path)

        mock_page_result.save_to_json = MagicMock(side_effect=save_json_side_effect)

        adapter = PaddleOCRAdapter(model_size="tiny", model_dir=model_dir)
        result = adapter.process_pdf("fake.pdf", output_dir=output_dir)

        assert "# Trang 1" in result
        assert "Dòng 1" in result
        assert "Dòng 2" in result
        assert len(result) > 0


@patch("paddleocr.PaddleOCR")
def test_process_pdf_empty_result(mock_paddleocr):
    mock_page_result = MagicMock()
    mock_page_result.save_to_json = MagicMock()

    mock_ocr_instance = MagicMock()
    mock_ocr_instance.predict.return_value = [mock_page_result]
    mock_paddleocr.return_value = mock_ocr_instance

    with (
        tempfile.TemporaryDirectory() as model_dir,
        tempfile.TemporaryDirectory() as output_dir,
    ):
        json_path = Path(model_dir) / "page_1_result.json"
        fake_json = {"rec_texts": [], "rec_boxes": [], "page_index": 0}
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(fake_json, f)

        def save_json_side_effect(path):
            import shutil
            shutil.copy(str(json_path), path)

        mock_page_result.save_to_json = MagicMock(side_effect=save_json_side_effect)

        adapter = PaddleOCRAdapter(model_size="tiny", model_dir=model_dir)
        result = adapter.process_pdf("fake.pdf", output_dir=output_dir)

        assert result == ""
