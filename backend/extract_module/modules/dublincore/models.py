from dataclasses import dataclass, field, asdict
from typing import List


@dataclass
class DublinCoreRecord:
    title: List[str] = field(default_factory=list)
    creator: List[str] = field(default_factory=list)
    subject: List[str] = field(default_factory=list)
    description: List[str] = field(default_factory=list)
    publisher: List[str] = field(default_factory=list)
    date: List[str] = field(default_factory=list)
    type: List[str] = field(default_factory=list)
    format: List[str] = field(default_factory=list)
    identifier: List[str] = field(default_factory=list)
    language: List[str] = field(default_factory=list)
    contributor: List[str] = field(default_factory=list)
    coverage: List[str] = field(default_factory=list)
    rights: List[str] = field(default_factory=list)
    relation: List[str] = field(default_factory=list)
    source: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v}

    def has_content(self) -> bool:
        return any(bool(v) for v in asdict(self).values())
