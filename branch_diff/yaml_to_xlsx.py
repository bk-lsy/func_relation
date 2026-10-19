#!/usr/bin/env python3
"""Combine the face_snapshot AC and BC YAML into one workbook.

Usage:
    python3 branch_diff/yaml_to_xlsx.py
    python3 branch_diff/yaml_to_xlsx.py branch_diff/face_snapshot-new -o output.xlsx

Requires PyYAML. XLSX creation uses only the Python standard library.
"""

import argparse
from datetime import date, datetime
from pathlib import Path
import re
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

# 与 face_snapshot-new/差异情况概览.2.0.xlsx 的前 15 列保持一致。
SIDE_COLUMNS = (
    ("序号", "序号", 9),
    ("合入时间", "合入时间", 15),
    ("commit-id", "commit-id", 16),
    ("标题", "标题", 75),
    ("类型", "类型", 28),
    ("Change-Id", "Change-Id", 48),
    ("备注", "备注", 100),
    ("是否需要评审", "是否需要评审", 18),
    ("是否需要处理", "是否需要处理", 18),
    ("是否已做修复提交", "是否已做修复提交", 20),
    ("修复提交是否已合入", "修复提交是否已合入", 22),
    ("修复提交标题", "修复提交标题", 75),
    ("修复提交commit id", "修复提交commit id", 46),
    ("修复提交change id", "修复提交change id", 48),
    ("修复提交链接", "修复提交链接", 65),
)
SIDE_NUMERIC_KEYS = {"序号", "是否需要评审", "是否需要处理", "是否已做修复提交", "修复提交是否已合入"}
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


def read_rows(path, columns, sequence_keys=("序号",)):
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("YAML 顶层必须是记录列表")
    rows = []
    for number, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"第 {number} 条必须是字段映射")
        missing = [key for _, key, _ in columns if key not in item]
        if missing:
            raise ValueError(f"第 {number} 条缺少字段：{', '.join(missing)}")
        for key in sequence_keys:
            sequence = item[key]
            if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 1:
                raise ValueError(f"第 {number} 条的 {key} 必须是正整数")
        rows.append([item[key] for _, key, _ in columns])
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError("序号不能重复")
    return rows


def add_cell(row_element, column_number, row_number, value, columns, numeric_keys, style=0):
    cell = ET.SubElement(row_element, tag(MAIN, "c"), {
        "r": cell_ref(column_number, row_number), "s": str(style),
    })
    if columns[column_number - 1][1] in numeric_keys and row_number > 1 and type(value) is int:
        ET.SubElement(cell, tag(MAIN, "v")).text = str(value)
        return
    cell.set("t", "inlineStr")
    inline = ET.SubElement(cell, tag(MAIN, "is"))
    value_element = ET.SubElement(inline, tag(MAIN, "t"))
    value_element.set(tag(XML, "space"), "preserve")
    value_element.text = text_value(value, row_number - 1, columns[column_number - 1][1])


def worksheet(rows, columns_spec, numeric_keys, type_index):
    sheet = ET.Element(tag(MAIN, "worksheet"))
    last_row = len(rows) + 1
    last_column = cell_ref(len(columns_spec), last_row)
    ET.SubElement(sheet, tag(MAIN, "dimension"), {"ref": f"A1:{last_column}"})
    views = ET.SubElement(sheet, tag(MAIN, "sheetViews"))
    view = ET.SubElement(views, tag(MAIN, "sheetView"), {"workbookViewId": "0"})
    ET.SubElement(view, tag(MAIN, "pane"), {
        "ySplit": "1", "topLeftCell": "A2", "activePane": "bottomLeft", "state": "frozen",
    })
    columns = ET.SubElement(sheet, tag(MAIN, "cols"))
    for number, (_, _, width) in enumerate(columns_spec, start=1):
        ET.SubElement(columns, tag(MAIN, "col"), {
            "min": str(number), "max": str(number), "width": str(width), "customWidth": "1",
        })
    sheet_data = ET.SubElement(sheet, tag(MAIN, "sheetData"))
    header = ET.SubElement(sheet_data, tag(MAIN, "row"), {"r": "1", "ht": "27", "customHeight": "1"})
    for column_number, (name, _, _) in enumerate(columns_spec, start=1):
        add_cell(header, column_number, 1, name, columns_spec, numeric_keys, style=1)
    for row_number, values in enumerate(rows, start=2):
        row = ET.SubElement(sheet_data, tag(MAIN, "row"), {"r": str(row_number)})
        style = 2 if values[type_index] == "无差异" else 0
        for column_number, value in enumerate(values, start=1):
            add_cell(row, column_number, row_number, value, columns_spec, numeric_keys, style=style)
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
    ET.SubElement(header, tag(MAIN, "sz"), {"val": "11"})
    ET.SubElement(header, tag(MAIN, "name"), {"val": "Calibri"})
    fills = ET.SubElement(root, tag(MAIN, "fills"), {"count": "3"})
    for pattern in ("none", "gray125"):
        fill = ET.SubElement(fills, tag(MAIN, "fill"))
        ET.SubElement(fill, tag(MAIN, "patternFill"), {"patternType": pattern})
    fill = ET.SubElement(fills, tag(MAIN, "fill"))
    pattern = ET.SubElement(fill, tag(MAIN, "patternFill"), {"patternType": "solid"})
    ET.SubElement(pattern, tag(MAIN, "fgColor"), {"rgb": "FFE2F0D9"})
    ET.SubElement(pattern, tag(MAIN, "bgColor"), {"indexed": "64"})
    borders = ET.SubElement(root, tag(MAIN, "borders"), {"count": "1"})
    ET.SubElement(borders, tag(MAIN, "border"))
    style_xfs = ET.SubElement(root, tag(MAIN, "cellStyleXfs"), {"count": "1"})
    ET.SubElement(style_xfs, tag(MAIN, "xf"), {"numFmtId": "0", "fontId": "0", "fillId": "0", "borderId": "0"})
    cell_xfs = ET.SubElement(root, tag(MAIN, "cellXfs"), {"count": "3"})
    for font_id, fill_id in ((0, 0), (1, 0), (0, 2)):
        xf = ET.SubElement(cell_xfs, tag(MAIN, "xf"), {
            "numFmtId": "0", "fontId": str(font_id), "fillId": str(fill_id),
            "borderId": "0", "xfId": "0", "applyAlignment": "1", "applyFill": "1",
        })
        ET.SubElement(xf, tag(MAIN, "alignment"), {"vertical": "top", "wrapText": "1"})
    cell_styles = ET.SubElement(root, tag(MAIN, "cellStyles"), {"count": "1"})
    ET.SubElement(cell_styles, tag(MAIN, "cellStyle"), {"name": "Normal", "xfId": "0", "builtinId": "0"})
    return xml_bytes(root)


def workbook(sheet_names):
    root = ET.Element(tag(MAIN, "workbook"))
    sheets = ET.SubElement(root, tag(MAIN, "sheets"))
    for number, name in enumerate(sheet_names, start=1):
        ET.SubElement(sheets, tag(MAIN, "sheet"), {
            "name": name, "sheetId": str(number), tag(DOC_REL, "id"): f"rId{number}",
        })
    return xml_bytes(root)


def relationships(items):
    root = ET.Element(tag(PKG_REL, "Relationships"))
    for rel_id, rel_type, target in items:
        ET.SubElement(root, tag(PKG_REL, "Relationship"), {
            "Id": rel_id, "Type": f"{DOC_REL}/{rel_type}", "Target": target,
        })
    return xml_bytes(root)


def content_types(sheet_count):
    root = ET.Element(tag(CONTENT_TYPES, "Types"))
    for extension, content_type in (
        ("rels", "application/vnd.openxmlformats-package.relationships+xml"),
        ("xml", "application/xml"),
    ):
        ET.SubElement(root, tag(CONTENT_TYPES, "Default"), {
            "Extension": extension, "ContentType": content_type,
        })
    parts = [
        ("/xl/workbook.xml", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"),
        ("/xl/styles.xml", "application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"),
    ]
    parts.extend(
        (f"/xl/worksheets/sheet{number}.xml", "application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml")
        for number in range(1, sheet_count + 1)
    )
    for part, content_type in parts:
        ET.SubElement(root, tag(CONTENT_TYPES, "Override"), {
            "PartName": part, "ContentType": content_type,
        })
    return xml_bytes(root)


def write_xlsx(path, sheets):
    # Build all sheets before opening the output, so invalid source data cannot
    # leave behind a partial workbook.
    sheet_data = [worksheet(rows, columns, numeric_keys, type_index) for _, rows, columns, numeric_keys, type_index in sheets]
    sheet_names = [name for name, _, _, _, _ in sheets]
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types(len(sheets)))
        archive.writestr("_rels/.rels", relationships([
            ("rId1", "officeDocument", "xl/workbook.xml"),
        ]))
        archive.writestr("xl/workbook.xml", workbook(sheet_names))
        archive.writestr("xl/_rels/workbook.xml.rels", relationships([
            (f"rId{number}", "worksheet", f"worksheets/sheet{number}.xml")
            for number in range(1, len(sheets) + 1)
        ] + [(f"rId{len(sheets) + 1}", "styles", "styles.xml")]))
        for number, sheet in enumerate(sheet_data, start=1):
            archive.writestr(f"xl/worksheets/sheet{number}.xml", sheet)
        archive.writestr("xl/styles.xml", styles())


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source_dir", nargs="?", type=Path,
                        default=Path(__file__).resolve().parent / "face_snapshot-new",
                        help="包含 AC、BC 两份 YAML 的目录；默认是脚本旁的 face_snapshot-new")
    parser.add_argument("-o", "--output", type=Path, help="输出 XLSX 路径；默认是目录下的差异情况概览.xlsx")
    args = parser.parse_args()
    source_dir = args.source_dir.parent if args.source_dir.suffix.lower() == ".yaml" else args.source_dir
    output = args.output or source_dir / "差异情况概览.xlsx"
    source_paths = [source_dir / name for name in ("ac侧提交概览.yaml", "bc侧提交概览.yaml")]
    if output.resolve() in (path.resolve() for path in source_paths):
        parser.error("输出路径不能覆盖源 YAML 文件")
    try:
        type_index = next(index for index, (_, key, _) in enumerate(SIDE_COLUMNS) if key == "类型")
        sheets = [
            ("AC侧提交概览", read_rows(source_paths[0], SIDE_COLUMNS), SIDE_COLUMNS, SIDE_NUMERIC_KEYS, type_index),
            ("BC侧提交概览", read_rows(source_paths[1], SIDE_COLUMNS), SIDE_COLUMNS, SIDE_NUMERIC_KEYS, type_index),
        ]
        write_xlsx(output, sheets)
    except (OSError, ValueError, yaml.YAMLError) as error:
        parser.exit(1, f"生成失败：{error}\n")
    print(f"已生成 {output}（AC {len(sheets[0][1])} 条，BC {len(sheets[1][1])} 条）")


if __name__ == "__main__":
    main()
