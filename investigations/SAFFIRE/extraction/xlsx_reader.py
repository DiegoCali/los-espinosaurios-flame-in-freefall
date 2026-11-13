"""Streaming XLSX reader using cached Excel values; never executes formulae."""
from __future__ import annotations

import posixpath
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RNS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


class Workbook:
    def __init__(self, path):
        self.path = path
        self.zip = ZipFile(path)
        self.strings = []
        if "xl/sharedStrings.xml" in self.zip.namelist():
            with self.zip.open("xl/sharedStrings.xml") as handle:
                context = ET.iterparse(handle, events=("start", "end"))
                _, root = next(context)
                for event, element in context:
                    if event == "end" and element.tag == NS + "si":
                        self.strings.append("".join(n.text or "" for n in element.iter(NS + "t")))
                        root.clear()
        rels = ET.fromstring(self.zip.read("xl/_rels/workbook.xml.rels"))
        targets = {r.get("Id"): r.get("Target") for r in rels}
        book = ET.fromstring(self.zip.read("xl/workbook.xml"))
        self.sheets = {}
        for sheet in book.find(NS + "sheets"):
            target = targets[sheet.get(RNS + "id")]
            name = target.lstrip("/") if target.startswith("/") else posixpath.normpath("xl/" + target)
            self.sheets[sheet.get("name")] = name

    def rows(self, sheet, columns=None):
        """Yield (Excel row number, {column letter: cached value}) incrementally."""
        columns = set(columns) if columns else None
        with self.zip.open(self.sheets[sheet]) as handle:
            context = ET.iterparse(handle, events=("start", "end"))
            _, root = next(context)
            for event, element in context:
                if event != "end" or element.tag != NS + "row":
                    continue
                values = {}
                for cell in element.findall(NS + "c"):
                    column = re.sub(r"\d", "", cell.get("r", ""))
                    if columns is not None and column not in columns:
                        continue
                    node = cell.find(NS + "v")
                    if cell.get("t") == "inlineStr":
                        value = "".join(n.text or "" for n in cell.iter(NS + "t"))
                    elif node is None or node.text is None:
                        continue
                    elif cell.get("t") == "s":
                        value = self.strings[int(node.text)]
                    elif cell.get("t") in ("str", "e"):
                        value = node.text
                    else:
                        try:
                            value = float(node.text)
                        except ValueError:
                            value = node.text
                    values[column] = value
                yield int(element.get("r")), values
                root.clear()

    def close(self):
        self.zip.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
