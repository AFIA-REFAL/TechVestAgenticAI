"""Fetch BVRIT Hyderabad website to extract branding colors and logo info."""
import requests
import re

r = requests.get("https://bvrithyderabad.edu.in", timeout=15)
html = r.text

# Extract logo URL
logo_match = re.search(r'<img[^>]*src=["\']([^"\']*logo[^"\']*)["\']', html, re.IGNORECASE)
if logo_match:
    print(f"LOGO: {logo_match.group(1)}")

# Extract colors from CSS
color_matches = re.findall(r'#[0-9a-fA-F]{6}', html)
print(f"\nCOLORS FOUND ({len(color_matches)}):")
for c in sorted(set(color_matches))[:20]:
    print(f"  {c}")

# Extract title
title_match = re.search(r'<title>(.*?)</title>', html)
if title_match:
    print(f"\nTITLE: {title_match.group(1)}")

# Check for favicon
favicon_match = re.search(r'<link[^>]*rel=["\'](?:shortcut )?icon["\'][^>]*href=["\']([^"\']*)["\']', html, re.IGNORECASE)
if favicon_match:
    print(f"FAVICON: {favicon_match.group(1)}")

print(f"\nHTML length: {len(html)} chars")
print(f"\n--- First 3000 chars ---\n{html[:3000]}")