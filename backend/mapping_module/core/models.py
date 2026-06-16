from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Any

class IsbnModel(BaseModel):
    isbn_number: Optional[str] = None
    price: Optional[str] = None

class ClassificationCodeModel(BaseModel):
    """Model cho mã phân loại (LCC/NLM)"""
    code: str
    description: str
    confidence: Optional[str] = None

class ExtractionMetadataModel(BaseModel):
    source_pages_used: List[str] = Field(default_factory=list)
    low_confidence_fields: Optional[List[str]] = Field(default_factory=list)

class RawExtractionData(BaseModel):
    document_type: Optional[str] = Field(None)
    document_part_info: Optional[str] = None
    nature_of_content: Optional[str] = None
    
    publication_year: Optional[str] = None
    copyright_year: Optional[str] = None
    country_of_publication: Optional[str] = None
    place_of_publication: Optional[str] = None
    publisher_name: Optional[str] = None
    isbn: Optional[List[IsbnModel]] = Field(default_factory=list)
    issn: Optional[str] = None
    edition_statement: Optional[str] = None
    
    author_personal_name: Optional[str] = None
    author_role: Optional[str] = None
    corporate_name: Optional[str] = None
    advisor_name: Optional[str] = None
    advisor_title: Optional[str] = None
    
    title_main: Optional[str] = None
    title_remainder: Optional[str] = None
    statement_of_responsibility: Optional[str] = None
    title_variant: Optional[List[str]] = Field(default_factory=list)
    
    extent: Optional[str] = None
    physical_details: Optional[str] = None
    dimensions: Optional[str] = None
    series_statement: Optional[str] = None
    series_volume: Optional[str] = None
    
    general_notes: Optional[List[str]] = Field(default_factory=list)
    dissertation_note: Optional[str] = None
    bibliography_note: Optional[str] = None
    number_of_references: Optional[str] = None
    acquisition_source: Optional[str] = None
    
    subject_terms: Optional[List[str]] = Field(default_factory=list)
    major: Optional[str] = None
    academic_level: Optional[str] = None
    
    lcc_classification: Optional[List[ClassificationCodeModel]] = Field(default_factory=list)
    nlm_classification: Optional[List[ClassificationCodeModel]] = Field(default_factory=list)
    
    has_illustrations: Optional[bool] = None
    has_index: Optional[bool] = None
    extraction_metadata: Optional[ExtractionMetadataModel] = None
    summary: Optional[str] = None

    @field_validator('isbn', 'title_variant', 'general_notes', 'subject_terms', mode='before')
    @classmethod
    def convert_none_to_empty_list(cls, value: Any) -> List[Any]:
        return value if value is not None else []