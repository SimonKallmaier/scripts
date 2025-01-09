import re

import lxml.etree as ET
import pandas as pd


def extract_mode_mapping(cii_path: str) -> dict:
    tree = ET.parse(cii_path)
    root = tree.getroot()
    ns = {"xsl": "http://www.w3.org/1999/XSL/Transform"}
    mapping = {}

    templates = root.xpath("//xsl:template", namespaces=ns)
    for tmpl in templates:
        mode = tmpl.get("mode")
        if not mode:
            continue
        children = list(tmpl)
        if children:
            child_tag = ET.QName(children[0]).localname
            mapping[mode] = child_tag
    return mapping


def extract_id_mapping(xml_path: str) -> dict:
    tree = ET.parse(xml_path)
    root = tree.getroot()

    result = {}
    for entry in root.findall("entry"):
        item_id = entry.get("id")
        item_key = entry.get("key")
        if item_id and item_key:
            # Remove the 'xr:' prefix
            item_key = item_key.replace("xr:", "")
            result[item_id] = item_key

    return result


def extract_id_to_value_mapping(xml_path: str) -> dict:
    tree = ET.parse(xml_path)
    root = tree.getroot()

    result = {}
    for entry in root.findall("entry"):
        item_id = entry.get("id")
        item_value = entry.text.strip() if entry.text else None
        if item_id and item_value:
            result[item_id] = item_value

    return result


def extract_mode_line_mapping(cii_path: str) -> dict:
    """
    Extracts a mapping from mode to the last segment of the match attribute in the XSL file,
    removing namespace prefixes and any predicates (e.g. [preceding-sibling::...]).
    Example: {"BT-99": "Amount", ...}
    """
    tree = ET.parse(cii_path)
    root = tree.getroot()
    ns = {"xsl": "http://www.w3.org/1999/XSL/Transform"}
    mapping = {}

    templates = root.xpath("//xsl:template", namespaces=ns)
    for tmpl in templates:
        mode = tmpl.get("mode")
        match_attr = tmpl.get("match")
        if not mode or not match_attr:
            continue
        # Take the final segment after the last '/'
        last_segment = match_attr.strip().split("/")[-1]
        # Remove anything in brackets (e.g. [preceding-sibling::...])
        last_segment = re.sub(r"\[.*?\]", "", last_segment)
        # Remove namespace prefix if present
        tag = last_segment.split(":")[-1]
        mapping[mode] = tag.strip()
    return mapping


def combine(cii_xsl_path: str, ubl_invoice_xsl_path: str, ubl_creditnote_xsl_path: str, xml_path: str):
    dict1_cii = extract_mode_mapping(cii_xsl_path)
    dict4_cii = extract_mode_line_mapping(cii_xsl_path)

    dict1_invoice = extract_mode_mapping(ubl_invoice_xsl_path)
    dict4_invoice = extract_mode_line_mapping(ubl_invoice_xsl_path)

    dict1_credit = extract_mode_mapping(ubl_creditnote_xsl_path)
    dict4_credit = extract_mode_line_mapping(ubl_creditnote_xsl_path)

    dict2 = extract_id_mapping(xml_path)
    dict3 = extract_id_to_value_mapping(xml_path)

    all_ids = set(dict1_cii.keys()) | set(dict1_invoice.keys()) | set(dict1_credit.keys())

    rows = []
    for mode_id in sorted(all_ids):
        rows.append(
            {
                "ID": mode_id,
                "Key_Cii": dict1_cii.get(mode_id, ""),
                "LineName_Cii": dict4_cii.get(mode_id, ""),
                "Key_UblInvoice": dict1_invoice.get(mode_id, ""),
                "LineName_UblInvoice": dict4_invoice.get(mode_id, ""),
                "Key_UblCreditNote": dict1_credit.get(mode_id, ""),
                "LineName_UblCreditNote": dict4_credit.get(mode_id, ""),
                "XML Key": dict2.get(mode_id, ""),
                "XML Value": dict3.get(mode_id, ""),
            }
        )

    df = pd.DataFrame(
        rows,
        columns=[
            "ID",
            "Key_Cii",
            "LineName_Cii",
            "Key_UblInvoice",
            "LineName_UblInvoice",
            "Key_UblCreditNote",
            "LineName_UblCreditNote",
            "XML Key",
            "XML Value",
        ],
    )
    return df


if __name__ == "__main__":
    import os

    cii_path = os.path.join("xsl", "cii-xr.xsl")
    ubl_invoice_xsl_path = os.path.join("xsl", "ubl-invoice-xr.xsl")
    ubl_creditnote_xsl_path = os.path.join("xsl", "ubl-creditnote-xr.xsl")
    de_xml_path = os.path.join("xsl", "l10n", "de.xml")
    df = combine(cii_path, ubl_invoice_xsl_path, ubl_creditnote_xsl_path, de_xml_path)
