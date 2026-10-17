#!/usr/bin/env python3
"""Convert the face_snapshot overview YAML to an Excel workbook.

Usage:
    python3 branch_diff/yaml_to_xlsx.py branch_diff/face_snapshot-new/差异情况概览.yaml
    python3 branch_diff/yaml_to_xlsx.py input.yaml -o output.xlsx

Requires PyYAML. XLSX creation uses only the Python standard library.
"""

import argparse
from datetime import date, datetime
from pathlib import Path
import re
import sys
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile

try:
    import yaml
except ImportError:
    raise SystemExit("缺少 PyYAML：请先安装 pyyaml")


MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
DOC_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
CONTENT_TYPES = "http://schemas.openxmlformats.org/package/2006/content-types"
XML = "http://www.w3.org/XML/1998/namespace"

# YAML 中用不同键保存原表两个同名的“备注”列；XLSX 恢复原表表头。
COLUMNS = (
    ("序号", "序号", 9),
    ("commit-id", "commit-id", 16),
    ("标题", "标题", 75),
    ("状态", "状态", 25),
    ("备注", "状态备注", 80),
    ("处理情况", "处理情况", 40),
    ("备注", "处理备注", 80),
    ("已确认", "已确认", 12),
    ("完整性", "完整性", 15),
    ("与人工备注一致", "与人工备注一致", 20),
    ("人工备注来源", "人工备注来源", 100),
    ("其他", "其他", 100),
    ("合入时间", "合入时间", 15),
    ("Change-Id", "Change-Id", 48),
)
CONFIRMED_INDEX = next(index for index, (_, key, _) in enumerate(COLUMNS) if key == "已确认")
NUMERIC_KEYS = {"序号", "已确认"}
INVALID_XML = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff]")


def tag(namespace, name):
    return f"{{{namespace}}}{name}"


def xml_bytes(element):
    return ET.tostring(element, encoding="utf-8", xml_declaration=True)


def cell_ref(column, row):
    letters = ""
    while column:
        column, remainder = divmod(column - 1, 26)
        letters = chr(65 + remainder) + letters
    return f"{letters}{row}"


def text_value(value, row_number, key):
    if value is None:
        return ""
    if isinstance(value, (date, datetime)):
        value = value.isoformat()
    else:
        value = str(value)
    if len(value) > 32767:
        raise ValueError(f"第 {row_number} 条的 {key} 超过 Excel 单元格长度上限")
    if INVALID_XML.search(value):
        raise ValueError(f"第 {row_number} 条的 {key} 包含无效 XML 字符")
    return value


def read_rows(path):
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("YAML 顶层必须是记录列表")
    rows = []
    for number, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"第 {number} 条必须是字段映射")
        missing = [key for _, key, _ in COLUMNS if key not in item]
        if missing:
            raise ValueError(f"第 {number} 条缺少字段：{', '.join(missing)}")
        sequence = item["序号"]
        confirmed = item["已确认"]
        if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 1:
            raise ValueError(f"第 {number} 条的序号必须是正整数")
        if type(confirmed) is not int or confirmed not in (0, 1):
            raise ValueError(f"第 {number} 条的已确认必须是整数 0 或 1")
        rows.append([item[key] for _, key, _ in COLUMNS])
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError("序号不能重复")
    return rows


def add_cell(row_element, column_number, row_number, value, style=0):
    cell = ET.SubElement(row_element, tag(MAIN, "c"), {
        "r": cell_ref(column_number, row_number), "s": str(style),
    })
    if COLUMNS[column_number - 1][1] in NUMERIC_KEYS and row_number > 1:
        ET.SubElement(cell, tag(MAIN, "v")).text = str(value)
        return
    cell.set("t", "inlineStr")
    inline = ET.SubElement(cell, tag(MAIN, "is"))
    value_element = ET.SubElement(inline, tag(MAIN, "t"))
    value_element.set(tag(XML, "space"), "preserve")
    value_element.text = text_value(value, row_number - 1, COLUMNS[column_number - 1][1])


def worksheet(rows):
    sheet = ET.Element(tag(MAIN, "worksheet"))
    last_row = len(rows) + 1
    last_column = cell_ref(len(COLUMNS), last_row)
    ET.SubElement(sheet, tag(MAIN, "dimension"), {"ref": f"A1:{last_column}"})
    views = ET.SubElement(sheet, tag(MAIN, "sheetViews"))
    view = ET.SubElement(views, tag(MAIN, "sheetView"), {"workbookViewId": "0"})
    ET.SubElement(view, tag(MAIN, "pane"), {
        "ySplit": "1", "topLeftCell": "A2", "activePane": "bottomLeft", "state": "frozen",
    })
    columns = ET.SubElement(sheet, tag(MAIN, "cols"))
    for number, (_, _, width) in enumerate(COLUMNS, start=1):
        ET.SubElement(columns, tag(MAIN, "col"), {
            "min": str(number), "max": str(number), "width": str(width), "customWidth": "1",
        })
    sheet_data = ET.SubElement(sheet, tag(MAIN, "sheetData"))
    header = ET.SubElement(sheet_data, tag(MAIN, "row"), {"r": "1", "ht": "27", "customHeight": "1"})
    for column_number, (name, _, _) in enumerate(COLUMNS, start=1):
        add_cell(header, column_number, 1, name, style=1)
    for row_number, values in enumerate(rows, start=2):
        row = ET.SubElement(sheet_data, tag(MAIN, "row"), {"r": str(row_number)})
        style = 2 if values[CONFIRMED_INDEX] == 0 else 0
        for column_number, value in enumerate(values, start=1):
            add_cell(row, column_number, row_number, value, style=style)
    ET.SubElement(sheet, tag(MAIN, "autoFilter"), {"ref": f"A1:{last_column}"})
    return xml_bytes(sheet)


def styles():
    root = ET.Element(tag(MAIN, "styleSheet"))
    fonts = ET.SubElement(root, tag(MAIN, "fonts"), {"count": "2"})
    normal = ET.SubElement(fonts, tag(MAIN, "font"))
    ET.SubElement(normal, tag(MAIN, "sz"), {"val": "11"})
    ET.SubElement(normal, tag(MAIN, "name"), {"val": "Calibri"})
    header = ET.SubElement(fonts, tag(MAIN, "font"))
    ET.SubElement(header, tag(MAIN, "b"))
    ET.SubElement(header, tag(MAIN, "color"), {"rgb": "FFFFFFFF"})
    ET.SubElement(header, tag(MAIN, "sz"), {"val": "11"})
    ET.SubElement(header, tag(MAIN, "name"), {"val": "Calibri"})
    fills = ET.SubElement(root, tag(MAIN, "fills"), {"count": "4"})
    for pattern in ("none", "gray125"):
        fill = ET.SubElement(fills, tag(MAIN, "fill"))
        ET.SubElement(fill, tag(MAIN, "patternFill"), {"patternType": pattern})
    for color in ("FF1F4E78", "FFFFF2CC"):
        fill = ET.SubElement(fills, tag(MAIN, "fill"))
        pattern = ET.SubElement(fill, tag(MAIN, "patternFill"), {"patternType": "solid"})
        ET.SubElement(pattern, tag(MAIN, "fgColor"), {"rgb": color})
        ET.SubElement(pattern, tag(MAIN, "bgColor"), {"indexed": "64"})
    borders = ET.SubElement(root, tag(MAIN, "borders"), {"count": "1"})
    ET.SubElement(borders, tag(MAIN, "border"))
    style_xfs = ET.SubElement(root, tag(MAIN, "cellStyleXfs"), {"count": "1"})
    ET.SubElement(style_xfs, tag(MAIN, "xf"), {"numFmtId": "0", "fontId": "0", "fillId": "0", "borderId": "0"})
    cell_xfs = ET.SubElement(root, tag(MAIN, "cellXfs"), {"count": "3"})
    for font_id, fill_id in ((0, 0), (1, 2), (0, 3)):
        xf = ET.SubElement(cell_xfs, tag(MAIN, "xf"), {
            "numFmtId": "0", "fontId": str(font_id), "fillId": str(fill_id),
            "borderId": "0", "xfId": "0", "applyAlignment": "1", "applyFill": "1",
        })
        ET.SubElement(xf, tag(MAIN, "alignment"), {"vertical": "top", "wrapText": "1"})
    cell_styles = ET.SubElement(root, tag(MAIN, "cellStyles"), {"count": "1"})
    ET.SubElement(cell_styles, tag(MAIN, "cellStyle"), {"name": "Normal", "xfId": "0", "builtinId": "0"})
    return xml_bytes(root)


def workbook():
    root = ET.Element(tag(MAIN, "workbook"))
    sheets = ET.SubElement(root, tag(MAIN, "sheets"))
    ET.SubElement(sheets, tag(MAIN, "sheet"), {
        "name": "差异情况概览", "sheetId": "1", tag(DOC_REL, "id"): "rId1",
    })
    return xml_bytes(root)


def relationships(items):
    root = ET.Element(tag(PKG_REL, "Relationships"))
    for rel_id, rel_type, target in items:
        ET.SubElement(root, tag(PKG_REL, "Relationship"), {
            "Id": rel_id, "Type": f"{DOC_REL}/{rel_type}", "Target": target,
        })
    return xml_bytes(root)


def content_types():
    root = ET.Element(tag(CONTENT_TYPES, "Types"))
    for extension, content_type in (
        ("rels", "application/vnd.openxmlformats-package.relationships+xml"),
        ("xml", "application/xml"),
    ):
        ET.SubElement(root, tag(CONTENT_TYPES, "Default"), {
            "Extension": extension, "ContentType": content_type,
        })
    for part, content_type in (
        ("/xl/workbook.xml", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"),
        ("/xl/worksheets/sheet1.xml", "application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"),
        ("/xl/styles.xml", "application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"),
    ):
        ET.SubElement(root, tag(CONTENT_TYPES, "Override"), {
            "PartName": part, "ContentType": content_type,
        })
    return xml_bytes(root)


def write_xlsx(path, rows):
    # Build the sheet before opening the output, so invalid source data cannot
    # leave behind a partial workbook.
    sheet = worksheet(rows)
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types())
        archive.writestr("_rels/.rels", relationships([
            ("rId1", "officeDocument", "xl/workbook.xml"),
        ]))
        archive.writestr("xl/workbook.xml", workbook())
        archive.writestr("xl/_rels/workbook.xml.rels", relationships([
            ("rId1", "worksheet", "worksheets/sheet1.xml"),
            ("rId2", "styles", "styles.xml"),
        ]))
        archive.writestr("xl/worksheets/sheet1.xml", sheet)
        archive.writestr("xl/styles.xml", styles())


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("yaml_file", type=Path, help="源 YAML 文件")
    parser.add_argument("-o", "--output", type=Path, help="输出 XLSX 路径；默认与 YAML 同名")
    args = parser.parse_args()
    output = args.output or args.yaml_file.with_suffix(".xlsx")
    if output.resolve() == args.yaml_file.resolve():
        parser.error("输入和输出路径不能相同")
    try:
        rows = read_rows(args.yaml_file)
        write_xlsx(output, rows)
    except (OSError, ValueError, yaml.YAMLError) as error:
        parser.exit(1, f"生成失败：{error}\n")
    print(f"已生成 {output}（{len(rows)} 条记录）")


if __name__ == "__main__":
    main()
