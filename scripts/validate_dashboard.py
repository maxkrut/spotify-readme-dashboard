"""Offline validation of every local image referenced by a generated README."""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path


class HTMLImageReferences(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.images: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "img" and attributes.get("src"):
            self.images.append(attributes["src"])
        if tag in {"img", "source"} and attributes.get("srcset"):
            self.images.extend(
                candidate.strip().split()[0]
                for candidate in attributes["srcset"].split(",")
                if candidate.strip()
            )


def validate(path: Path) -> int:
    content = path.read_text(encoding="utf-8")
    images = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", content)
    html_images = HTMLImageReferences()
    html_images.feed(content)
    images.extend(html_images.images)
    for reference in images:
        if "://" in reference:
            continue
        image = path.parent / reference
        if not image.is_file():
            raise ValueError(f"Missing image: {image}")
        if image.suffix == ".svg":
            root = ET.parse(image).getroot()
            if not root.tag.endswith("svg") or not root.attrib.get("viewBox"):
                raise ValueError(f"Invalid SVG: {image}")
    return len(images)


if __name__ == "__main__":
    print(f"Validated {validate(Path(sys.argv[1]))} dashboard images.")
