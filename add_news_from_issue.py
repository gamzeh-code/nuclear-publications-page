#!/usr/bin/env python3
"""Validate a GitHub Issue Form submission and append it to news.json."""

from __future__ import annotations

import json
import os
import re
import unicodedata
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EVENT_PATH = Path(os.environ["GITHUB_EVENT_PATH"])
DATA_PATH = ROOT / "news.json"

FIELDS = {
    "Haber başlığı": "title",
    "Tarih": "date",
    "Kategori": "category",
    "Kısa özet": "summary",
    "Ayrıntılı metin": "content",
    "Görsel URL'si": "image_url",
    "Görsel açıklaması": "image_alt",
    "Görsel notu": "image_note",
    "Harici bağlantı": "external_url",
    "Öne çıkarılsın mı?": "featured",
}


def parse_form(body: str) -> dict[str, str]:
    sections = re.split(r"^###\s+", body, flags=re.MULTILINE)[1:]
    values: dict[str, str] = {}
    for section in sections:
        heading, _, value = section.partition("\n")
        key = FIELDS.get(heading.strip())
        if key:
            cleaned = value.strip()
            values[key] = "" if cleaned == "_No response_" else cleaned
    return values


def slugify(value: str) -> str:
    substitutions = str.maketrans({"ı": "i", "İ": "i", "ş": "s", "Ş": "s", "ğ": "g", "Ğ": "g", "ü": "u", "Ü": "u", "ö": "o", "Ö": "o", "ç": "c", "Ç": "c"})
    ascii_value = unicodedata.normalize("NFKD", value.translate(substitutions)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-")[:70]


def main() -> None:
    event = json.loads(EVENT_PATH.read_text(encoding="utf-8"))
    issue = event["issue"]
    values = parse_form(issue.get("body") or "")
    for field in ("title", "date", "category", "summary", "content"):
        if not values.get(field):
            raise ValueError(f"Zorunlu alan eksik: {field}")
    parsed_date = datetime.strptime(values["date"], "%Y-%m-%d").date()
    base_slug = slugify(values["title"])
    if not base_slug:
        raise ValueError("Başlıktan geçerli bir slug üretilemedi.")

    items = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    existing = {item["slug"] for item in items}
    slug = base_slug
    counter = 2
    while slug in existing:
        slug = f"{base_slug}-{counter}"
        counter += 1

    items.append({
        "slug": slug,
        "date": parsed_date.isoformat(),
        "category": values["category"],
        "kicker": values["category"],
        "title": values["title"],
        "summary": values["summary"],
        "content": values["content"],
        "image_url": values.get("image_url", ""),
        "image_alt": values.get("image_alt", ""),
        "image_note": values.get("image_note", ""),
        "external_url": values.get("external_url", ""),
        "featured": values.get("featured", "").casefold().startswith("evet"),
        "published": True,
    })
    DATA_PATH.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8").write(f"slug={slug}\n")


if __name__ == "__main__":
    main()
