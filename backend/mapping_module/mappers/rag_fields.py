from typing import List
from pymarc import Field, Subfield

from mapping_module.core.base_mapper import BaseFieldMapper
from mapping_module.core.models import RawExtractionData
from mapping_module.core.rag_bridge import get_rag_integration


class RAGFieldMapper(BaseFieldMapper):
    """Mapper cho trường 050 (LCC), 060 (NLM), 650 (Subject) sử dụng RAG."""
    
    def __init__(self):
        super().__init__()
        try:
            self.rag = get_rag_integration()
            self.use_rag = self.rag is not None
        except Exception as e:
            print(f"⚠️  RAG Engine initialization failed: {e}. Mapper will work with existing data only.")
            self.rag = None
            self.use_rag = False
    
    def can_handle(self, raw_data: RawExtractionData) -> bool:
        """Xử lý nếu có LCC/NLM/subject data."""
        has_lcc = raw_data.lcc_classification and len(raw_data.lcc_classification) > 0
        has_nlm = raw_data.nlm_classification and len(raw_data.nlm_classification) > 0
        has_subject = raw_data.subject_terms and len(raw_data.subject_terms) > 0
        return has_lcc or has_nlm or has_subject
    
    def map_field(self, raw_data: RawExtractionData) -> List[Field]:
        """Tạo các trường MARC 050, 060, 650."""
        fields = []
        
        # Field 050 - Library of Congress Classification
        if raw_data.lcc_classification and len(raw_data.lcc_classification) > 0:
            fields.extend(self._map_050_field(raw_data.lcc_classification))
        
        # Field 060 - National Library of Medicine Classification
        if raw_data.nlm_classification and len(raw_data.nlm_classification) > 0:
            fields.extend(self._map_060_field(raw_data.nlm_classification))
        
        # Field 650 - Subject Terms
        if raw_data.subject_terms and len(raw_data.subject_terms) > 0:
            fields.extend(self._map_650_field(raw_data.subject_terms))
        
        return fields
    
    def _map_050_field(self, lcc_codes: List) -> List[Field]:
        fields = []
        for item in lcc_codes:
            code = item.code if hasattr(item, "code") else item.get("code", "")
            
            if not code:
                continue
            
            # Tách Cutter number nếu có (format thường là: RC270.8 -> RC270 + .8)
            parts = code.split(".")
            classification = parts[0] if parts else code
            cutter = f".{parts[1]}" if len(parts) > 1 else ""
            
            field = Field(
                tag="050",
                indicators=[" ", "0"],  # 0 = LC assigned
                subfields=[Subfield("a", classification)],
            )
            if cutter:
                field.add_subfield("b", cutter)
            
            fields.append(field)
        
        return fields
    
    def _map_060_field(self, nlm_codes: List) -> List[Field]:
        fields = []
        for item in nlm_codes:
            code = item.code if hasattr(item, "code") else item.get("code", "")
            
            if not code:
                continue
            
            # Tách cutter nếu có
            parts = code.split("-")
            classification = parts[0] if parts else code
            cutter = f"-{parts[1]}" if len(parts) > 1 else ""
            
            field = Field(
                tag="060",
                indicators=[" ", " "],  # " " = NLM provided/assigned
                subfields=[Subfield("a", classification)],
            )
            if cutter:
                field.add_subfield("b", cutter)
            
            fields.append(field)
        
        return fields
    
    def _map_650_field(self, subject_terms: List[str]) -> List[Field]:
        fields = []
        for term in subject_terms:
            if not term or not term.strip():
                continue

            field = Field(
                tag="650",
                indicators=["1", "4"],  # Legacy subject heading / direct topical term
                subfields=[Subfield("a", term.strip())],
            )
            fields.append(field)
        
        return fields


class RAGEnrichedFieldMapper(BaseFieldMapper):
    def __init__(self):
        super().__init__()
        try:
            self.rag = get_rag_integration()
            self.use_rag = self.rag is not None
        except Exception as e:
            print(f"RAG Engine initialization failed: {e}. Auto-enrichment disabled.")
            self.rag = None
            self.use_rag = False
    
    def can_handle(self, raw_data: RawExtractionData) -> bool:
        if not self.use_rag:
            return False
        
        has_title = raw_data.title_main and raw_data.title_main.strip()
        has_subject = raw_data.subject_terms and len(raw_data.subject_terms) > 0
        no_lcc = not raw_data.lcc_classification or len(raw_data.lcc_classification) == 0
        no_nlm = not raw_data.nlm_classification or len(raw_data.nlm_classification) == 0
        
        return (has_title or has_subject) and (no_lcc or no_nlm)
    
    def map_field(self, raw_data: RawExtractionData) -> List[Field]:
        if not self.use_rag:
            return []
        
        fields = []
        
        if (not raw_data.lcc_classification or len(raw_data.lcc_classification) == 0):
            try:
                lcc_results = self.rag.query_lcc(
                    title=raw_data.title_main or "",
                    subject_terms=raw_data.subject_terms
                )
                if lcc_results:
                    raw_data.lcc_classification = lcc_results
                    fields.extend(self._map_050_field(lcc_results))
            except Exception as e:
                print(f"LCC RAG query lỗi: {e}")
        
        # Query RAG nếu chưa có NLM
        if (not raw_data.nlm_classification or len(raw_data.nlm_classification) == 0):
            try:
                nlm_results = self.rag.query_nlm(
                    title=raw_data.title_main or "",
                    subject_terms=raw_data.subject_terms
                )
                if nlm_results:
                    raw_data.nlm_classification = nlm_results
                    fields.extend(self._map_060_field(nlm_results))
            except Exception as e:
                print(f"⚠️  NLM RAG query lỗi: {e}")
        
        return fields
    
    def _map_050_field(self, lcc_codes: List) -> List[Field]:
        """Tạo MARC field 050."""
        fields = []
        for item in lcc_codes:
            code = item.get("code", "") if isinstance(item, dict) else item.code
            if not code:
                continue
            
            parts = code.split(".")
            classification = parts[0]
            cutter = f".{parts[1]}" if len(parts) > 1 else ""
            
            field = Field(
                tag="050",
                indicators=[" ", "0"],
                subfields=[Subfield("a", classification)],
            )
            if cutter:
                field.add_subfield("b", cutter)
            fields.append(field)
        
        return fields
    
    def _map_060_field(self, nlm_codes: List) -> List[Field]:
        """Tạo MARC field 060."""
        fields = []
        for item in nlm_codes:
            code = item.get("code", "") if isinstance(item, dict) else item.code
            if not code:
                continue
            
            parts = code.split("-")
            classification = parts[0]
            cutter = f"-{parts[1]}" if len(parts) > 1 else ""
            
            field = Field(
                tag="060",
                indicators=[" ", " "],
                subfields=[Subfield("a", classification)],
            )
            if cutter:
                field.add_subfield("b", cutter)
            fields.append(field)
        
        return fields
