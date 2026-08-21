import json
from typing import List
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, tostring, register_namespace

from modules.dublincore.models import DublinCoreRecord

DC_NS = "http://purl.org/dc/elements/1.1/"
OAI_DC_NS = "http://www.openarchives.org/OAI/2.0/oai_dc/"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
SCHEMA_LOC = "http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd"

register_namespace("oai_dc", OAI_DC_NS)
register_namespace("dc", DC_NS)
register_namespace("xsi", XSI_NS)


def _dc_element(parent: Element, element: str, text: str):
    el = SubElement(parent, f"{{{DC_NS}}}{element}")
    el.text = text


def serialize_to_xml(records: List[DublinCoreRecord], pretty: bool = True) -> str:
    if not records:
        records = [DublinCoreRecord()]

    root = Element(f"{{{OAI_DC_NS}}}dc")
    root.set(f"{{{XSI_NS}}}schemaLocation", SCHEMA_LOC)

    for record in records:
        for val in record.title:
            _dc_element(root, "title", val)
        for val in record.creator:
            _dc_element(root, "creator", val)
        for val in record.subject:
            _dc_element(root, "subject", val)
        for val in record.description:
            _dc_element(root, "description", val)
        for val in record.publisher:
            _dc_element(root, "publisher", val)
        for val in record.date:
            _dc_element(root, "date", val)
        for val in record.type:
            _dc_element(root, "type", val)
        for val in record.format:
            _dc_element(root, "format", val)
        for val in record.identifier:
            _dc_element(root, "identifier", val)
        for val in record.language:
            _dc_element(root, "language", val)
        for val in record.contributor:
            _dc_element(root, "contributor", val)
        for val in record.coverage:
            _dc_element(root, "coverage", val)
        for val in record.rights:
            _dc_element(root, "rights", val)
        for val in record.relation:
            _dc_element(root, "relation", val)
        for val in record.source:
            _dc_element(root, "source", val)

    raw = tostring(root, encoding="unicode")
    if pretty:
        dom = minidom.parseString(raw)
        return dom.toprettyxml(indent="  ")
    return raw


def serialize_to_json(records: List[DublinCoreRecord], indent: int = 2) -> str:
    data = [r.to_dict() for r in records] if len(records) != 1 else records[0].to_dict()
    return json.dumps(data, ensure_ascii=False, indent=indent)
