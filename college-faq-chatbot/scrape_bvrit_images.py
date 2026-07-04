"""Scrape BVRIT page images and build a source_url -> image index.

The app uses this file to surface related images for answers retrieved
from the knowledge base.

Usage:
    python scrape_bvrit_images.py
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from utils import load_knowledge_base_entries


BASE_URL = "https://bvrithyderabad.edu.in/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    )
}


def normalize_url(base_url: str, candidate: str) -> Optional[str]:
    if not candidate:
        return None
    candidate = candidate.strip()
    if candidate.startswith("data:"):
        return None
    absolute = urljoin(base_url, candidate)
    parsed = urlparse(absolute)
    if not parsed.scheme or not parsed.netloc:
        return None
    return absolute


def extract_images_from_page(url: str) -> Dict[str, Any]:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    title_tag = soup.find("title")
    h1_tag = soup.find("h1")
    page_title = " ".join(
        filter(
            None,
            [
                h1_tag.get_text(" ", strip=True) if h1_tag else "",
                title_tag.get_text(" ", strip=True) if title_tag else "",
            ],
        )
    ).strip()

    seen = set()
    images: List[Dict[str, Any]] = []

    def add_image(image_url: Optional[str], alt_text: str = "", is_primary: bool = False) -> None:
        normalized = normalize_url(url, image_url or "")
        if not normalized or normalized in seen:
            return
        seen.add(normalized)
        images.append(
            {
                "image_url": normalized,
                "alt_text": alt_text.strip(),
                "is_primary": is_primary,
                "source_page_url": url,
            }
        )

    for meta_name in ("og:image", "twitter:image", "twitter:image:src"):
        for meta in soup.find_all("meta", attrs={"property": meta_name}):
            add_image(meta.get("content"), is_primary=True)
        for meta in soup.find_all("meta", attrs={"name": meta_name}):
            add_image(meta.get("content"), is_primary=True)

    for link in soup.find_all("link", attrs={"rel": re.compile(r"image_src", re.I)}):
        add_image(link.get("href"), is_primary=True)

    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
        if not src and img.get("srcset"):
            src = img.get("srcset").split(",")[0].strip().split(" ")[0]
        add_image(src, alt_text=img.get("alt", ""), is_primary=False)

    return {
        "page_url": url,
        "page_title": page_title or url,
        "images": images[:8],
    }


def build_image_index() -> Dict[str, Any]:
    kb_entries = load_knowledge_base_entries("data/BVRITH_Knowledge_Base.md") or []
    source_urls = []
    seen_urls = set()
    for entry in kb_entries:
        source_url = entry.get("source_url")
        if source_url and source_url not in seen_urls:
            seen_urls.add(source_url)
            source_urls.append(source_url)

    pages: Dict[str, Any] = {}
    for url in source_urls:
        try:
            pages[url] = extract_images_from_page(url)
            print(f"✓ scraped images for {url}")
        except Exception as exc:
            print(f"✗ failed to scrape {url}: {exc}")

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": BASE_URL,
        "pages": pages,
    }


def main() -> None:
    output_path = Path("data/bvrit_image_index.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    image_index = build_image_index()
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(image_index, f, ensure_ascii=False, indent=2)

    print(f"Image index written to {output_path}")


if __name__ == "__main__":
    main()
