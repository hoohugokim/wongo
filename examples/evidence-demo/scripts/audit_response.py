"""Check one declared scalar and its exact rendered paragraph/table contexts."""
import csv
import json
import os
import zipfile
from pathlib import Path

from lxml import etree

from wongo.audit_helpers import paragraph_assertion, scalar_assertion, table_cell_assertion

root = Path(os.environ["WONGO_AUDIT_PROJECT"])
with (root / "data/measurements.csv").open(encoding="utf-8", newline="") as stream:
    values = list(csv.DictReader(stream))
value = float(values[0]["response"])
docx = next(Path(raw) for raw in os.environ["WONGO_AUDIT_OUTPUTS"].split(os.pathsep)
            if Path(raw).name.startswith("main-"))
source = {"file": "index.qmd", "line": 16}
artifact = {"file": "data/measurements.csv", "pointer": "row:1/response"}
with zipfile.ZipFile(docx) as package:
    xml = etree.fromstring(package.read("word/document.xml"))
ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
tables = xml.xpath("//w:tbl", namespaces=ns)
matches = [index for index, table in enumerate(tables)
           if table.xpath("./w:tr[1]/w:tc//w:t/text()", namespaces=ns) == ["sample", "response"]]
if len(matches) != 1:
    raise ValueError("Expected exactly one rendered table with sample/response column headers.")
table_index = matches[0]
assertions = [
    scalar_assertion({"response": value}, "/response", source=source, assertion_id="finite-response"),
    paragraph_assertion(docx, context="The measured response was", expected=f"{value:.1f}",
                        source=source, artifact=artifact, assertion_id="rendered-response"),
    table_cell_assertion(docx, table=table_index, row=1, column=1, expected=f"{value:.1f}",
                         source=source, artifact=artifact, assertion_id="response-cell"),
]
report = {"assertions": assertions, "coverage": {
    "checked": [item["id"] for item in assertions],
    "untested": ["scientific-interpretation", "units-policy", "other-manuscript-content"],
}}
Path(os.environ["WONGO_AUDIT_RESULT"]).write_text(json.dumps(report), encoding="utf-8")
