"""
image_lookup.py
BVRIT image lookup module — matches user queries to relevant images.
"""
import json
import streamlit as st
from pathlib import Path

IMAGES_PATH = Path(__file__).parent / "images.json"


@st.cache_data
def load_image_map():
    with open(IMAGES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    data.pop("_meta", None)
    return data


def find_image_for_query(query: str):
    """Return the best-matching image entry dict for a user query, or None."""
    query_lower = query.lower()
    image_map = load_image_map()

    best_match = None
    best_match_len = 0
    for _topic_key, entry in image_map.items():
        for kw in entry.get("keywords", []):
            if kw in query_lower and len(kw) > best_match_len:
                best_match = entry
                best_match_len = len(kw)
    return best_match


def show_image_if_relevant(query: str):
    """Call this right after showing the chatbot's text answer."""
    entry = find_image_for_query(query)
    if entry:
        caption = entry["name"]
        if entry.get("designation"):
            caption += f" — {entry['designation']}"
        st.image(
            entry["image_url"],
            caption=caption,
            width=280,
        )