import re
import time
import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from mapping_module import config

def parse_schedule_page(html: str, schedule_code: str) -> dict:
    """Phân tích HTML trang phân lớp của NLM để trích xuất danh sách mã."""
    soup = BeautifulSoup(html, "html.parser")
    schedule_name = ""
    for h2 in soup.find_all("h2"):
        text = h2.get_text(strip=True)
        if text and text != schedule_code:
            schedule_name = text
            break

    entries = []
    current_section = "General"
    main = soup.find("main") or soup.find("div", id=re.compile(r"main")) or soup.body

    for tag in main.find_all(["h3", "h4", "li", "p"], recursive=True):
        if tag.name in ("h3", "h4"):
            sec = tag.get_text(strip=True)
            if sec:
                current_section = sec
            continue

        text = tag.get_text(" ", strip=True)
        if not text:
            continue

        pattern = rf"\[?({re.escape(schedule_code)}\s+\d+[\d\.A-Z]*)\]?"
        m = re.search(pattern, text)
        if not m:
            continue

        entry_code = m.group(1).strip()
        remainder = text[m.end():].strip()
        remainder = re.sub(r'^[.\s]+', '', remainder)

        parts = re.split(r"\s{2,}", remainder)
        entry_name = parts[0].strip() if parts else remainder
        notes = " | ".join(p.strip() for p in parts[1:] if p.strip())
        is_unused = "not used" in text.lower() or text.strip().startswith("[")

        entries.append({
            "code": entry_code,
            "name": entry_name,
            "notes": notes,
            "section": current_section,
            "unused": is_unused,
        })

    return {
        "schedule_code": schedule_code,
        "schedule_name": schedule_name,
        "url": f"{config.BASE_URL}/schedules/{schedule_code}",
        "total_entries": len(entries),
        "entries": entries,
    }

def scrape_schedule(session: requests.Session, code: str) -> dict:
    url = f"{config.BASE_URL}/schedules/{code}"
    resp = session.get(url, headers=config.HEADERS, timeout=20)
    resp.raise_for_status()
    return parse_schedule_page(resp.text, code)

def scrape_all_nlm(output_path: str = config.NLM_OUTPUT_FILE):
    """Quét lần lượt 36 phân lớp NLM trực tuyến."""
    session = requests.Session()
    config.log.info("Khởi động session, kết nối với NLM...")
    session.get(f"{config.BASE_URL}/schedules", headers=config.HEADERS, timeout=15)
    time.sleep(1)

    all_data = {}
    for i, code in enumerate(config.ALL_SCHEDULES, 1):
        config.log.info(f"[{i:02d}/{len(config.ALL_SCHEDULES)}] Đang cào phân lớp NLM: {code}...")
        try:
            data = scrape_schedule(session, code)
            all_data[code] = data
        except Exception as e:
            config.log.error(f"✗ Lỗi hệ thống tại phân lớp {code}: {e}")
            all_data[code] = {"schedule_code": code, "error": str(e), "entries": []}
        if i < len(config.ALL_SCHEDULES):
            time.sleep(config.DELAY)

    out = Path(output_path)
    out.write_text(json.dumps(all_data, ensure_ascii=False, indent=4), encoding="utf-8")
    return all_data

if __name__ == "__main__":
    scrape_all_nlm()