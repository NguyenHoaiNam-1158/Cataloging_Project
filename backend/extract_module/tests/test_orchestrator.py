import os
from unittest.mock import AsyncMock, MagicMock, patch

os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("QWEN_API_KEY", "test-key")
os.environ.setdefault("USE_OCR", "false")

import pytest
from core.orchestrator import CentralOrchestrator


@pytest.mark.asyncio
@patch("core.orchestrator.PaddleOCRAdapter")
@patch("core.orchestrator.LLMManager")
async def test_handle_request_ocr_path(mock_llm_manager, mock_ocr_adapter):
    mock_llm = MagicMock()
    mock_llm.get_extraction_text_from_text = AsyncMock(return_value="* title_main: Test Title")
    mock_llm_manager.return_value = mock_llm

    mock_ocr = MagicMock()
    mock_ocr.process_pdf.return_value = "# Trang 1\nTest content\n---"
    mock_ocr_adapter.return_value = mock_ocr

    orch = CentralOrchestrator(use_ocr=True)
    code, data = await orch.handle_request("test.pdf")

    assert code == 200
    assert data is not None
    mock_ocr.process_pdf.assert_called_once_with("test.pdf")
    mock_llm.get_extraction_text_from_text.assert_called_once()


@pytest.mark.asyncio
@patch("core.orchestrator.ImageProcessor")
@patch("core.orchestrator.LLMManager")
async def test_handle_request_image_path(mock_llm_manager, mock_image_processor):
    mock_llm = MagicMock()
    mock_llm.get_extraction_text = AsyncMock(return_value="* title_main: Test Title")
    mock_llm_manager.return_value = mock_llm

    mock_img = MagicMock()
    mock_img.pdf_pages_to_images.return_value = ["page_1.jpg"]
    mock_img.cleanup_image = MagicMock()
    mock_image_processor.return_value = mock_img

    orch = CentralOrchestrator(use_ocr=False)
    code, data = await orch.handle_request("test.pdf")

    assert code == 200
    mock_img.pdf_pages_to_images.assert_called_once()


@pytest.mark.asyncio
@patch("core.orchestrator.ImageProcessor")
@patch("core.orchestrator.LLMManager")
async def test_handle_request_image_no_pages(mock_llm_manager, mock_image_processor):
    mock_img = MagicMock()
    mock_img.pdf_pages_to_images.return_value = []
    mock_image_processor.return_value = mock_img

    orch = CentralOrchestrator(use_ocr=False)
    code, data = await orch.handle_request("empty.pdf")

    assert code == 400
    assert "error" in data


@pytest.mark.asyncio
@patch("core.orchestrator.PaddleOCRAdapter")
@patch("core.orchestrator.LLMManager")
async def test_handle_request_ocr_empty(mock_llm_manager, mock_ocr_adapter):
    mock_ocr = MagicMock()
    mock_ocr.process_pdf.return_value = ""
    mock_ocr_adapter.return_value = mock_ocr

    orch = CentralOrchestrator(use_ocr=True)
    code, data = await orch.handle_request("empty.pdf")

    assert code == 400
    assert "OCR" in data["error"]


@pytest.mark.asyncio
@patch("core.orchestrator.PaddleOCRAdapter")
@patch("core.orchestrator.LLMManager")
async def test_handle_request_ocr_error(mock_llm_manager, mock_ocr_adapter):
    mock_ocr = MagicMock()
    mock_ocr.process_pdf.side_effect = RuntimeError("OCR failed")
    mock_ocr_adapter.return_value = mock_ocr

    orch = CentralOrchestrator(use_ocr=True)
    code, data = await orch.handle_request("test.pdf")

    assert code == 500
    assert "error" in data
