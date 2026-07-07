from dublin_core_module.mappers.descriptive import (
    TitleMapper,
    CreatorMapper,
    ContributorMapper,
    SubjectMapper,
    DescriptionMapper,
)
from dublin_core_module.mappers.publication import (
    PublisherMapper,
    DateMapper,
    RelationMapper,
    CoverageMapper,
    RightsMapper,
)
from dublin_core_module.mappers.technical import (
    TypeMapper,
    FormatMapper,
    IdentifierMapper,
    SourceMapper,
    LanguageMapper,
)


def default_mappers():
    return [
        TitleMapper(),
        CreatorMapper(),
        SubjectMapper(),
        DescriptionMapper(),
        PublisherMapper(),
        ContributorMapper(),
        DateMapper(),
        TypeMapper(),
        FormatMapper(),
        IdentifierMapper(),
        SourceMapper(),
        LanguageMapper(),
        RelationMapper(),
        CoverageMapper(),
        RightsMapper(),
    ]


__all__ = [
    "TitleMapper", "CreatorMapper", "ContributorMapper", "SubjectMapper",
    "DescriptionMapper", "PublisherMapper", "DateMapper", "RelationMapper",
    "CoverageMapper", "RightsMapper", "TypeMapper", "FormatMapper",
    "IdentifierMapper", "SourceMapper", "LanguageMapper", "default_mappers",
]
