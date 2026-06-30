# Content Engine Pro — Spec

**Course:** GenAI & Agentic AI Engineering — Day 3 Homework
**App:** `prompt-pipeline-content-engine-pro`

## 1. Objective

Extend a base "Content Engine" (5 AI calls: tagline, blog, social posts, image
brief, video brief) into a production-aware pipeline by adding three new
capabilities:

1. **Self-Critique Loop** — an LLM critic grades tagline/blog/social against
   the brief and triggers auto-regeneration (max 2 retries) on failure.
2. **Voiceover Generation** — adapts the blog intro into a TTS-ready script
   and synthesizes playable/downloadable audio.
3. **Multi-Channel Adaptation** — rewrites all text assets for a selected
   target channel (B2B LinkedIn / Gen-Z TikTok / Parents Facebook) while
   leaving image/video briefs untouched.

## 2. Pipeline Stages

```
Input (product name, audience, tone)
   │
   ▼
[1] Generate Suite ───────────────────────────────────────
   ├─ Tagline call
   ├─ Blog intro call
   ├─ Social posts call (JSON: 3 platforms)
   ├─ Image brief call
   └─ Video brief call
   │
   ▼
[2] Self-Critique Loop  (NEW)
   ├─ Critic grades {tagline, blog, social} → pass/fail + issue
   ├─ If any fail → regenerate that asset with issue injected as feedback
   ├─ Repeat up to 2 retries total
   └─ If still failing → show ⚠️ warning flag, display last attempt anyway
   │
   ▼
[3] Voiceover Generation  (NEW)
   ├─ Script Adapter call: blog intro → TTS-ready script
   │   (breath pauses, short sentences, no visual references)
   └─ TTS synthesis → playable audio + .mp3 download
   │
   ▼
[4] Multi-Channel Adaptation  (NEW)
   ├─ User picks channel from dropdown
   ├─ Adapt call: rewrites tagline/blog/social for channel tone/vocab/emoji
   ├─ Image & video briefs are passed through unchanged
   └─ Live before/after preview
```

## 3. Data Contracts

### Suite object (session state)
```json
{
  "product_name": "string",
  "audience": "string",
  "tone": "string",
  "tagline": "string",
  "blog": "string",
  "social": {
    "instagram": "string",
    "twitter": "string",
    "linkedin": "string"
  },
  "image_brief": "string",
  "video_brief": "string"
}
```

### Critic verdict
```json
{
  "tagline": {"pass": true, "issue": null},
  "blog":    {"pass": false, "issue": "Intro exceeds 60 words"},
  "social":  {"pass": true, "issue": null}
}
```

### Channel adaptation result
```json
{
  "tagline": "string",
  "blog": "string",
  "social": {"instagram": "...", "twitter": "...", "linkedin": "..."}
}
```

## 4. Prompts (from spec, used verbatim as system prompts)

- `CRITIC_SYSTEM` — grades tagline/blog/social, returns strict JSON.
- `SCRIPT_ADAPTER` — blog intro → voiceover script (punctuation cues,
  ≤15-word sentences, no visual references, text-only output).
- `ADAPT_SYSTEM` — rewrites 3 text assets for `{channel}`, returns JSON
  with same 3 keys.

## 5. Rules Implemented

| Rule | Implementation |
|---|---|
| Critique runs automatically before output shown | `run_critique_loop()` called right after generation, before render |
| Max 2 retries | `MAX_RETRIES = 2` constant; loop bounded |
| Warning flag if still failing | Red `st.error` banner per failing asset, output still shown |
| Voiceover playable or .mp3 | `st.audio()` player + `st.download_button` for `.mp3` |
| Channel adaptation = text only | Image/video briefs copied from suite, never sent to `ADAPT_SYSTEM` |
| Run on ≥2 products, capture output | "Run History" panel logs each run with critic verdicts |
| Handle bad input gracefully | Validation layer rejects empty name / nonsense audience with inline error, no API call wasted |
| Reflection paragraph | `REFLECTION.md` |

## 6. Tech Stack

- **Frontend:** Streamlit
- **LLM:** OpenRouter (`openai/gpt-4o-mini` default, swappable) — same
  pattern as `prompt-pipeline-triage`
- **TTS:** `gTTS` (no API key required) — swap-in point documented for
  OpenAI TTS / ElevenLabs if preferred
- **Config:** `.streamlit/secrets.toml` → `OPENROUTER_API_KEY`

## 7. File Layout

```
content-engine-pro/
├── app.py                  # Streamlit app — UI + orchestration
├── engine.py               # LLM call functions (generation, critique, adapt, script)
├── tts.py                  # Voiceover synthesis wrapper
├── prompts.py              # All system prompts (base + 3 additions)
├── validators.py           # Bad-input handling
├── requirements.txt
├── .streamlit/secrets.toml.example
├── spec.md                 # this file
└── REFLECTION.md           # one-paragraph reflection
```

## 8. Out of Scope (Stretch goals, not implemented)

A/B testing with LLM-as-judge, campaign brief PDF export, cost tracker,
multilingual regeneration — left as stretch goals per spec, not required
for base submission.