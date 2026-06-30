"""
validators.py
Graceful handling of bad input (empty name, nonsensical audience) BEFORE
any API call is made — saves tokens and gives the user a clear inline error
instead of a confusing model output or a stack trace.
"""

import re

_HAS_LETTERS = re.compile(r"[a-zA-Z]")
_HAS_VOWEL = re.compile(r"[aeiou]", re.IGNORECASE)
_REPEATED_CHAR = re.compile(r"(.)\1{3,}", re.IGNORECASE)  # e.g. "aaaa", "!!!!"

# A small denylist of common keyboard-mash / placeholder strings, checked
# case-insensitively. Catches the most common lazy/test inputs that the
# vowel heuristic alone would miss (e.g. "asdf", "qwerty", "test", "idk").
_MASH_DENYLIST = {
    "asdf", "asdfg", "asdfgh", "qwerty", "qwertyuiop", "zxcv", "zxcvb",
    "test", "testing", "idk", "na", "n/a", "none", "xxx", "abc", "abcd",
    "blah", "blahblah", "lol", "lorem", "ipsum",
}


def _is_keyboard_mash(text: str) -> bool:
    compact = text.strip().lower().replace(" ", "")
    if not compact:
        return True
    if compact in _MASH_DENYLIST:
        return True
    if _REPEATED_CHAR.search(compact):
        return True
    # Short strings (<=6 chars) with zero vowels are very likely mash/garbage
    # for an audience description (real short words almost always have a vowel).
    if len(compact) <= 6 and not _HAS_VOWEL.search(compact):
        return True
    return False


def validate_inputs(product_name: str, audience: str, tone: str):
    """
    Returns (is_valid: bool, error_message: str | None)
    """
    product_name = (product_name or "").strip()
    audience = (audience or "").strip()
    tone = (tone or "").strip()

    if not product_name:
        return False, "Product name can't be empty. Give your product a name."

    if len(product_name) < 2:
        return False, "Product name is too short to work with — try a few more characters."

    if not audience:
        return False, "Audience can't be empty. Tell us who this campaign is for."

    if not _HAS_LETTERS.search(audience):
        return False, "Audience needs to be a real description (e.g. 'busy parents'), not just symbols/numbers."

    if _is_keyboard_mash(audience.replace(" ", "")):
        return False, "That audience description looks like a placeholder or typo. Try something like 'college students' or 'small business owners'."

    if len(audience) > 200:
        return False, "Audience description is too long — keep it to a short phrase."

    if not tone:
        return False, "Pick a tone for the campaign."

    return True, None