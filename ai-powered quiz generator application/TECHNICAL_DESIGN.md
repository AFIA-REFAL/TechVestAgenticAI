# Technical Design — AI Quiz Generator

**Version:** 2.0  
**Date:** June 2026  
**Author:** AFIA-REFAL  
**Project:** TechVest Agentic AI — Academic Year 2025–26

---

## 1. Architecture Overview

AI Quiz Generator is a **single-file, single-process Streamlit application**. There is no separate backend server, database, or API layer. All logic — UI rendering, multi-format file parsing, AI calls, and state management — lives in `app.py` and executes within one Python process.

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser (Client)                      │
│        Streamlit WebSocket + Static Assets                   │
└───────────────────────────────┬─────────────────────────────┘
                                │ HTTP / WS
┌───────────────────────────────▼─────────────────────────────┐
│                    Streamlit Server (Python)                  │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────────┐ │
│  │  UI Layer    │  │  Session State │  │  Backend Logic   │ │
│  │  (CSS + HTML)│  │  (st.session_  │  │  extract_file()  │ │
│  │  + Widgets   │  │   state dict)  │  │  ├─ extract_pptx │ │
│  └──────────────┘  └────────────────┘  │  ├─ extract_pdf  │ │
│                                        │  ├─ extract_docx │ │
│                                        │  ├─ extract_txt  │ │
│                                        │  llm()           │ │
│                                        │  gen_mcqs()      │ │
│                                        │  gen_exp()       │ │
│                                        └──────┬───────────┘ │
└─────────────────────────────────────────────┬─┘─────────────┘
                                              │ HTTPS POST
┌─────────────────────────────────────────────▼─────────────┐
│                  OpenRouter API                             │
│          https://openrouter.ai/api/v1/chat/completions     │
│          Model: anthropic/claude-haiku-4-5                 │
└────────────────────────────────────────────────────────────┘
```

---

## 2. Technology Choices

### 2.1 Streamlit

Streamlit was chosen because it allows a Python developer to build a fully interactive web application without writing any JavaScript. Every Python variable change triggers a full page re-render, making it natural to express a state-machine UI (upload → config → quiz → results) using `st.session_state`.

**Trade-offs:**
- Pro: Rapid development, no frontend build tooling required.
- Con: Full page re-render on every interaction. Worked around using `st.rerun()` only when state transitions are needed.
- Con: Streamlit's default widget styling is opinionated. Overridden entirely with injected CSS targeting internal `data-testid` selectors.

### 2.2 OpenRouter / Claude Haiku

OpenRouter provides a single API endpoint that proxies multiple AI providers. `anthropic/claude-haiku-4-5` was selected for its balance of speed and instruction-following quality. MCQ generation requires the model to return structured JSON, which Haiku handles reliably with explicit prompt instructions.

**Trade-offs:**
- Pro: Single API key, model can be swapped by changing one constant.
- Con: Requires internet; no offline mode.

### 2.3 python-pptx

Extracts text from every `TextFrame` across all shapes on all slides. Pure Python, no native dependencies.

### 2.4 pypdf

Extracts text from each page of a PDF using embedded text streams. Pure Python. Does not support scanned/image-based PDFs (no OCR).

### 2.5 python-docx

Reads `.docx` XML structure and exposes paragraphs. Paragraphs are grouped into chunks of ~12 to simulate "sections" for the AI prompt.

### 2.6 Plain Text (.txt)

Decoded as UTF-8 and split into 250-word chunks. No external library required.

---

## 3. Multi-Format File Parsing

### 3.1 Dispatcher — `extract_file(b, filename)`

All format routing goes through a single dispatcher that inspects the file extension and calls the appropriate parser:

```python
def extract_file(b: bytes, filename: str) -> tuple[list[dict], int]:
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext == "pptx": return extract_pptx(b)
    if ext == "pdf":  return extract_pdf(b)
    if ext == "docx": return extract_docx(b)
    if ext == "txt":  return extract_txt(b)
    raise ValueError(f"Unsupported file type: .{ext}")
```

All parsers return the same structure: `(list[{slide: int, text: str}], total_word_count)`. The `slide` field is a generic section index regardless of format, allowing `gen_mcqs` to work identically for all formats.

### 3.2 Format Comparison

| Format | Parser | Section Unit | Content Source |
|---|---|---|---|
| `.pptx` | `python-pptx` | 1 slide = 1 section | All text frames in all shapes |
| `.pdf` | `pypdf` | 1 page = 1 section | Embedded text stream per page |
| `.docx` | `python-docx` | ~12 paragraphs = 1 section | Paragraph text |
| `.txt` | built-in | 250 words = 1 chunk | Raw decoded string |

### 3.3 Empty Section Handling

All parsers skip sections that produce empty or whitespace-only text after joining. This handles image-only slides, blank pages, and whitespace-only paragraphs without errors.

---

## 4. Application State Machine

The application is driven by `st.session_state.step`, which acts as the current screen indicator. Navigation between screens is triggered by button clicks that mutate this value followed by `st.rerun()`.

```
             ┌──────────┐
   start ──► │  upload  │
             └────┬─────┘
      file parsed │
             ┌────▼─────┐
             │  config  │
             └────┬─────┘
    questions gen │
             ┌────▼─────┐
             │   quiz   │◄──── retake
             └────┬─────┘
        submitted │
             ┌────▼─────┐
             │ results  │──── upload new ──► upload (reset, history preserved)
             └──────────┘
```

A second state variable, `st.session_state.nav_page`, controls which sidebar page is visible (`home` / `analytics` / `history` / `settings`) independently of the quiz flow.

### Full Session State Schema

| Key | Type | Description |
|---|---|---|
| `step` | `str` | Current quiz screen: `upload`, `config`, `quiz`, `results` |
| `nav_page` | `str` | Active sidebar tab: `home`, `analytics`, `history`, `settings` |
| `slides` | `list[dict]` | Parsed content sections: `[{slide: int, text: str}]` |
| `filename` | `str` | Uploaded file name (includes extension) |
| `slide_count` | `int` | Number of non-empty sections extracted |
| `word_count` | `int` | Total word count across all sections |
| `num_questions` | `int` | Configured question count (5–30) |
| `difficulty` | `str` | `Simple`, `Medium`, or `Complex` |
| `questions` | `list[dict]` | Generated MCQ objects from AI |
| `user_answers` | `dict[str, str]` | Maps question ID → selected option letter |
| `current_q` | `int` | Zero-based index of the question currently displayed |
| `start_time` | `float` | Unix timestamp when quiz started |
| `elapsed` | `int` | Total seconds taken (set on submit) |
| `explanations` | `dict[str, str]` | Maps question ID → AI explanation string |
| `rk` | `int` | Render key — incremented on retake to force button re-render |
| `quiz_history` | `list[dict]` | Records of completed quiz sessions |

---

## 5. Backend Functions

### 5.1 `extract_pptx(b: bytes) → tuple[list[dict], int]`

Parses `.pptx` binary using `python-pptx`. Iterates over every slide, collects all paragraph text from shapes with a `TextFrame`. Each slide becomes one section dict.

### 5.2 `extract_pdf(b: bytes) → tuple[list[dict], int]`

Parses PDF binary using `pypdf.PdfReader`. Calls `page.extract_text()` for each page. Falls back to empty string if extraction returns `None`. Each page becomes one section dict.

### 5.3 `extract_docx(b: bytes) → tuple[list[dict], int]`

Parses `.docx` binary using `python-docx`. Iterates over all paragraphs in document order. Accumulates paragraphs in a buffer; flushes into a section every 12 non-empty paragraphs. Remaining paragraphs form the final section.

### 5.4 `extract_txt(b: bytes) → tuple[list[dict], int]`

Decodes bytes as UTF-8, splits on whitespace. Divides into chunks of 250 words using `range(0, len(words), 250)`. Each chunk becomes one section dict.

### 5.5 `extract_file(b, filename)` — Dispatcher

Routes to the appropriate parser based on lowercase file extension. Raises `ValueError` for unsupported types.

### 5.6 `llm(prompt: str) → str`

Sends a single-turn chat completion request to the OpenRouter API with a 120-second timeout. Returns the raw text content of the first choice message.

### 5.7 `gen_mcqs(slides, n, diff) → list[dict]`

Constructs a prompt embedding all section text (labelled `[Section N]` regardless of source format), specifies difficulty, and requests a JSON array. Strips markdown fences before parsing.

**MCQ schema:**
```json
{
  "id": 1,
  "question": "...",
  "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
  "correct": "B",
  "topic": "label"
}
```

### 5.8 `gen_exp(questions, answers) → dict[str, str]`

Filters to wrong answers only, sends a single prompt requesting 1–2 sentence explanations per wrong answer, returns a dict of `{question_id: explanation}`. Returns `{}` if all answers were correct.

---

## 6. UI Architecture

### 6.1 Layout Structure

```
st.columns([0.06, 0.94])
    ├── nav_col   → nav dock with 4 icon buttons
    └── main_col
        ├── top header HTML (gradient brand title + step progress)
        └── st.columns([1, 3, 1])   ← centers the glass panel
               └── center col
                   └── screen content (upload / config / quiz / results)
                       or nav page content (analytics / history / settings)
```

### 6.2 Upload Screen — Format-Aware

The upload zone shows all 4 format badges (`.pptx`, `.pdf`, `.docx`, `.txt`). The `st.file_uploader` is configured with `type=["pptx","pdf","docx","txt"]`. After upload, the processing animation labels dynamically reflect the detected format (e.g. "Extracting pages from PDF…" vs "Extracting slides from PPTX…"). The success card shows a format-specific emoji icon.

### 6.3 CSS Strategy

All custom styling is injected via `st.markdown("<style>...</style>")`. Key Streamlit selectors:

| Target | Selector |
|---|---|
| Main container | `[data-testid="block-container"]` |
| Streamlit header | `[data-testid="stHeader"]` |
| Default sidebar | `[data-testid="stSidebar"]` |
| Column wrappers | `[data-testid="column"]` |
| File uploader | `[data-testid="stFileUploaderDropzone"]` |
| Buttons | `.stButton > button[kind="primary|secondary"]` |

**Key CSS techniques:**
- **Glassmorphism:** `backdrop-filter: blur(32px)` + `rgba` background
- **Gradient mesh background:** Two `radial-gradient` layers on `stAppViewContainer`
- **Animated shimmer:** `@keyframes shimmer` with `background-position` sweep
- **Floating icon:** `@keyframes floatIcon` using `translateY`
- **Pulse rings:** `@keyframes pulseRing` using `scale` + `opacity`
- **Overflow fix:** All Streamlit column containers forced to `overflow: visible`

### 6.4 Option Selection Pattern

Streamlit does not support custom-styled radio feedback. Solution uses `st.button` with `type="primary"` for selected option and `type="secondary"` for others, keyed with `rk` that increments on retake.

---

## 7. Data Flow

```
User uploads file (.pptx / .pdf / .docx / .txt)
        │
        ▼
extract_file(bytes, filename)
  → dispatches to format-specific parser
  → list of {slide, text} sections + word count
        │
        ▼
User configures n, difficulty
        │
        ▼
gen_mcqs(sections, n, difficulty)
  → prompt: [Section N]: <text> for all sections
  → llm() → POST /chat/completions
  → parse JSON → list of MCQ dicts
        │
        ▼
User takes quiz (user_answers updated per question)
        │
        ▼
On submit:
  gen_exp(questions, user_answers)
  → wrong answers only
  → llm() → explanation dict
        │
        ▼
Results screen + history saved
```

---

## 8. API Integration

### 8.1 Request Format

```json
POST https://openrouter.ai/api/v1/chat/completions

{
  "model": "anthropic/claude-haiku-4-5",
  "messages": [{"role": "user", "content": "<prompt>"}],
  "temperature": 0.7,
  "max_tokens": 4096
}
```

### 8.2 Response Parsing

The model is instructed to return only raw JSON. As a safety measure, any ` ```json ` or ` ``` ` wrappers are stripped before `json.loads`. A `json.JSONDecodeError` is caught and surfaced as a retry prompt.

### 8.3 Prompt Design

The `gen_mcqs` prompt labels content sections as `[Section N]` regardless of source format, keeping the prompt format-agnostic. Difficulty is injected via a pre-written instruction string for each level.

---

## 9. Error Handling

| Scenario | Handling |
|---|---|
| File > 25 MB | Checked before parsing; `st.error` shown |
| Unsupported file type | Blocked by `st.file_uploader` type filter |
| No extractable text | Parser returns empty list; `st.error` shown |
| Password-protected file | Parser raises exception; caught and shown as error |
| Image-only PDF | `page.extract_text()` returns empty; section skipped silently |
| AI returns malformed JSON | `json.JSONDecodeError` caught; retry prompt shown |
| API HTTP error | `requests.HTTPError` caught; error message shown |
| API timeout | Caught via general `Exception`; error shown |
| Explanation generation fails | Silently returns `{}`; results still display |

---

## 10. Security Considerations

- **API key:** Loaded from `.env` via `python-dotenv`; excluded from git via `.gitignore`.
- **No persistent storage:** All data in `st.session_state` (cleared on session end).
- **Input validation:** File type enforced by `st.file_uploader`; size validated before parsing.
- **No authentication:** Acceptable for local single-user deployment.
- **Prompt injection:** Slide text is embedded in prompts; acceptable in controlled academic context.

---

## 11. Known Limitations

| Limitation | Impact | Mitigation |
|---|---|---|
| Image-only PDFs produce no text | Questions cannot be generated | Error message + word count shows 0 |
| Scanned DOCX (no embedded text) | Same as above | Same |
| Password-protected files fail | Parser raises exception | Caught and shown as clear error |
| Session history lost on server restart | Analytics/history cleared | Acceptable for single-session use |
| Large PDFs (100+ pages) may be slow | Prompt can exceed token limits | Prompt truncation could be added |
| AI JSON output not schema-validated | Malformed responses surface as errors | Could add Pydantic validation |

---

## 12. Deployment Notes

The application is designed for **local development use**. To deploy on a server:

1. Set `OPENROUTER_API_KEY` as an environment variable (not via `.env`).
2. Run: `streamlit run app.py --server.port 8501 --server.address 0.0.0.0`
3. Add `--server.maxUploadSize 25` to enforce the 25 MB limit at the Streamlit level.
4. Consider placing behind a reverse proxy with authentication for multi-user environments.
