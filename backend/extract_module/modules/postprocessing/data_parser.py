import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class DataParser:
    def __init__(self):
        #các trường cần lưu dưới dạng array
        self.array_fields = [
            "title_variant", "general_notes", "subject_terms", 
            "isbn", "source_pages_used", "low_confidence_fields"
        ]
    def parse_text_to_json(self, text_response: str) -> Dict:
        logger.info("Parsing kết quả dạng text thành JSON")
        result = {
            "document_type": None, "document_part_info": None, "publication_year": None, "copyright_year": None,
            "country_of_publication": None, "has_illustrations": None, "has_index": None, "nature_of_content": None,
            "isbn": [], "issn": None, "author_personal_name": None, "author_role": None, "corporate_name": None,
            "title_main": None, "title_remainder": None, "statement_of_responsibility": None, "title_variant": [],
            "edition_statement": None, "place_of_publication": None, "publisher_name": None, "extent": None,
            "physical_details": None, "dimensions": None, "series_statement": None, "series_volume": None,
            "general_notes": [], "dissertation_note": None, "bibliography_note": None, "number_of_references": None,
            "acquisition_source": None, "subject_terms": [], "major": None, "academic_level": None,
            "advisor_name": None, "advisor_title": None,
            "extraction_metadata": { "source_pages_used": [], "low_confidence_fields": [] }
        }
        
        lines = text_response.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith("*") or line.startswith("-"):
                line = line[1:].strip()
            if ':' not in line:
                continue
            
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            if value.lower() == 'null' or value == '':
                value = None
            
            if value is not None and key in self.array_fields:
                if '|' in value:
                    value = [v.strip() for v in value.split('|') if v.strip()]
                else:
                    value = [v.strip() for v in value.split(',') if v.strip()]
            elif value is None and key in self.array_fields:
                value = []
            
            if key in result and key != "extraction_metadata":
                result[key] = value
            elif key in result["extraction_metadata"]:
                result["extraction_metadata"][key] = value
        return result
                        