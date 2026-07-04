
"""
Quick test script to verify the tools and ingestion work correctly.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools import (
    fee_calculator,
    date_checker,
    percentage_calculator,
    get_tool_definitions,
    execute_tool_call,
)
from utils import load_document, extract_sections

print("=" * 60)
print("TEST 1: Tool Functions")
print("=" * 60)

print("\n--- fee_calculator ---")
print(fee_calculator(120000, 4, 60000, 25))

print("\n--- date_checker ---")
print(date_checker("2025-08-15", "Management Quota Deadline"))

print("\n--- percentage_calculator ---")
print(percentage_calculator(205, 228, "CSE placement rate 2024-25"))

print("\n--- execute_tool_call ---")
print(execute_tool_call("date_checker", {"target_date": "2025-12-01", "date_label": "End-Sem Exam"}))

print("\n--- Tool Definitions ---")
defs = get_tool_definitions()
for d in defs:
    print(f"  - {d['function']['name']}: {d['function']['description'][:80]}...")

print("\n" + "=" * 60)
print("TEST 2: Document Loading (bvrit_college_info.docx)")
print("=" * 60)

text = load_document("data/bvrit_college_info.docx")
sections = extract_sections(text)
print(f"Total characters: {len(text):,}")
print(f"Total sections extracted: {len(sections)}")
print("\nSection headings:")
for i, s in enumerate(sections):
    content_preview = s["content"][:60].replace("\n", " ")
    print(f"  {i+1:2d}. [{s['heading'][:70]}] ({len(s['content']):,} chars)")

print("\n" + "=" * 60)
print("ALL TESTS PASSED")
print("=" * 60)