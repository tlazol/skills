#!/usr/bin/env python3
"""Audit PPTX list semantics and speaker-note coverage without python-pptx."""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"
MANUAL_LIST = re.compile(r"^\s*(?:[-•●▪◦]|\d+[.)])\s+\S")


def slide_number(name: str) -> int:
    match = re.search(r"slide(\d+)\.xml$", name)
    return int(match.group(1)) if match else 0


def text_of(paragraph: ET.Element) -> str:
    return "".join(node.text or "" for node in paragraph.iter(f"{A}t"))


def has_list_marker(paragraph: ET.Element) -> bool:
    ppr = paragraph.find(f"{A}pPr")
    if ppr is None:
        return False
    return ppr.find(f"{A}buChar") is not None or ppr.find(f"{A}buAutoNum") is not None


def list_level(paragraph: ET.Element) -> int:
    ppr = paragraph.find(f"{A}pPr")
    if ppr is None:
        return 0
    return int(ppr.get("lvl", "0"))


def looks_like_unmarked_list(paragraph: ET.Element) -> bool:
    ppr = paragraph.find(f"{A}pPr")
    if ppr is None or has_list_marker(paragraph):
        return False
    try:
        margin_left = int(ppr.get("marL", "0"))
        indent = int(ppr.get("indent", "0"))
    except ValueError:
        return False
    return margin_left > 0 and indent < 0


def notes_body_text(root: ET.Element) -> str:
    for shape in root.iter(f"{P}sp"):
        placeholder = shape.find(f"./{P}nvSpPr/{P}nvPr/{P}ph")
        if placeholder is None or placeholder.get("type") != "body":
            continue
        text_body = shape.find(f"{P}txBody")
        if text_body is None:
            return ""
        return "".join(node.text or "" for node in text_body.iter(f"{A}t")).strip()
    return ""


def notes_target(zf: zipfile.ZipFile, slide_name: str) -> str | None:
    rel_name = slide_name.replace("ppt/slides/", "ppt/slides/_rels/") + ".rels"
    if rel_name not in zf.namelist():
        return None
    root = ET.fromstring(zf.read(rel_name))
    for rel in root.findall(f"{REL}Relationship"):
        if rel.get("Type", "").endswith("/notesSlide"):
            target = rel.get("Target", "")
            return "ppt/notesSlides/" + Path(target).name
    return None


def audit(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    with zipfile.ZipFile(path) as zf:
        slides = sorted(
            (name for name in zf.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)),
            key=slide_number,
        )
        for slide_name in slides:
            number = slide_number(slide_name)
            root = ET.fromstring(zf.read(slide_name))
            for text_body in root.iter(f"{P}txBody"):
                paragraphs = list(text_body.iter(f"{A}p"))
                manual = [
                    text_of(paragraph).strip()
                    for paragraph in paragraphs
                    if MANUAL_LIST.match(text_of(paragraph).strip())
                    and not has_list_marker(paragraph)
                ]
                for text in manual:
                    message = f"slide {number}: manual list marker: {text[:80]}"
                    (errors if len(manual) >= 2 else warnings).append(message)

                unmarked = [
                    text_of(paragraph).strip()
                    for paragraph in paragraphs
                    if text_of(paragraph).strip() and looks_like_unmarked_list(paragraph)
                ]
                if len(unmarked) >= 2:
                    for text in unmarked:
                        errors.append(f"slide {number}: indented list paragraph has no list marker: {text[:80]}")

                for paragraph in paragraphs:
                    text = text_of(paragraph).strip()
                    level = list_level(paragraph)
                    if has_list_marker(paragraph) and level >= 3:
                        errors.append(f"slide {number}: list nesting exceeds 3 levels: {text[:80]}")
                    elif has_list_marker(paragraph) and level == 2:
                        warnings.append(f"slide {number}: 3rd-level list needs justification: {text[:80]}")

            notes_name = notes_target(zf, slide_name)
            if notes_name is None or notes_name not in zf.namelist():
                warnings.append(f"slide {number}: speaker notes missing")
                continue
            notes_root = ET.fromstring(zf.read(notes_name))
            notes_text = notes_body_text(notes_root)
            if not notes_text:
                warnings.append(f"slide {number}: speaker notes empty")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pptx", type=Path)
    args = parser.parse_args()
    if not args.pptx.is_file():
        parser.error(f"file not found: {args.pptx}")
    errors, warnings = audit(args.pptx)
    for item in errors:
        print(f"ERROR {item}")
    for item in warnings:
        print(f"WARN  {item}")
    print(f"SUMMARY errors={len(errors)} warnings={len(warnings)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
