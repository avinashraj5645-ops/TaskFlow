"""
Section 3 — Integrated AI Quick-Add.

Contains:
  1. build_messages()   — role-based (system/user) prompt construction.
  2. mock_parse()        — required, deterministic, keyless parser (Task 3).
  3. real_llm_parse()    — OPTIONAL real-model path, feature-flagged off by
                           default. Never required for grading.
  4. parse_description() — picks mock vs real based on USE_REAL_LLM env var,
                           always falling back to the mock on any failure.
"""
import os
import re
from typing import Optional, TypedDict, Tuple

# Ordered exactly as specified in the brief.
HIGH_KEYWORDS = ["urgent", "asap"]
LOW_KEYWORDS = ["whenever", "low priority"]

NEXT_WEEKDAY_PHRASES = [
    "next monday", "next tuesday", "next wednesday", "next thursday",
    "next friday", "next saturday", "next sunday",
]
BARE_WEEKDAYS = [
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
]


class ParsedTask(TypedDict):
    title: str
    priority: str
    due_date_hint: Optional[str]


# ---------------------------------------------------------------------------
# Role-based prompt construction (Task 2).
# Used to build the "conversation" the mock (or a real LLM) is standing in
# for — keeps the code path identical whether the mock or a real model answers.
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are a task-parsing assistant for TaskFlow. Given one free-text "
    "sentence describing a task, extract three fields: `title` (the task "
    "description with priority/date keywords removed), `priority` (exactly "
    "one of \"low\", \"medium\", \"high\"), and `due_date_hint` (the raw "
    "matched date phrase, or null if none is present). Follow the keyword "
    "rules exactly and deterministically. Respond with those three fields "
    "only."
)


def build_messages(description: str) -> list[dict]:
    """Standard role-based message list: system instruction + user content."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": description},
    ]


# ---------------------------------------------------------------------------
# Task 3 — required, deterministic, keyless mock parser.
# ---------------------------------------------------------------------------
def _find_span(lower_text: str, phrase: str) -> Optional[Tuple[int, int]]:
    idx = lower_text.find(phrase)
    if idx == -1:
        return None
    return (idx, idx + len(phrase))


def mock_parse(description: str) -> ParsedTask:
    original = description
    lower = description.lower()

    # (b) Priority — check group (i) then group (ii); first match wins.
    matched_priority_keywords: list[str] = []
    priority = "medium"

    high_hit = any(kw in lower for kw in HIGH_KEYWORDS)
    low_hit = any(kw in lower for kw in LOW_KEYWORDS)

    if high_hit:
        priority = "high"
    elif low_hit:
        priority = "low"
    else:
        priority = "medium"

    # Title-stripping note: remove EVERY occurrence of EVERY group (i)/(ii)
    # keyword found anywhere in the text, regardless of which one decided
    # priority.
    for kw in HIGH_KEYWORDS + LOW_KEYWORDS:
        if kw in lower:
            matched_priority_keywords.append(kw)

    # (c) Due-date hint — checked in the exact specified order; stop at first.
    due_date_hint: Optional[str] = None
    date_span = None

    ordered_date_candidates = ["today", "tomorrow", "next week"] + NEXT_WEEKDAY_PHRASES + BARE_WEEKDAYS
    for phrase in ordered_date_candidates:
        span = _find_span(lower, phrase)
        if span:
            due_date_hint = phrase
            date_span = span
            break

    # (d) Title — remove matched spans from the ORIGINAL-cased description.
    # Build a list of (start, end) spans to strip, found via a lower-case
    # scan but applied to the original string (same offsets, since we only
    # ever compare lower-cased text against lower-cased text).
    spans_to_remove: list[Tuple[int, int]] = []

    for kw in matched_priority_keywords:
        start = 0
        while True:
            idx = lower.find(kw, start)
            if idx == -1:
                break
            spans_to_remove.append((idx, idx + len(kw)))
            start = idx + len(kw)

    if due_date_hint is not None:
        start = 0
        while True:
            idx = lower.find(due_date_hint, start)
            if idx == -1:
                break
            spans_to_remove.append((idx, idx + len(due_date_hint)))
            start = idx + len(due_date_hint)

    # Remove spans from the ORIGINAL-cased string, right-to-left so earlier
    # offsets stay valid.
    spans_to_remove.sort(key=lambda s: s[0], reverse=True)
    title_chars = list(original)
    for start, end in spans_to_remove:
        del title_chars[start:end]
    title = "".join(title_chars).strip()

    # Collapse leftover double-spaces created by span removal, then re-strip.
    title = re.sub(r"\s{2,}", " ", title).strip()

    if not title:
        title = "Untitled task"

    return {"title": title, "priority": priority, "due_date_hint": due_date_hint}


# ---------------------------------------------------------------------------
# OPTIONAL real-LLM path. Feature-flagged off by default (USE_REAL_LLM).
# Grading always runs with the flag off / no API key present.
# ---------------------------------------------------------------------------
def real_llm_parse(description: str) -> Optional[ParsedTask]:
    """
    CHANGEABLE: plug in any provider you already have access to here. This
    stub intentionally does nothing unless USE_REAL_LLM=true AND an API key
    is present — otherwise parse_description() below falls back to the mock.
    """
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return None

    try:
        # Example only — left unimplemented on purpose so the repo never
        # requires a paid dependency to install/run. Wire in your provider's
        # SDK here, sending build_messages(description) as the conversation,
        # and mapping the response back into the ParsedTask shape.
        return None
    except Exception:
        return None


def parse_description(description: str) -> ParsedTask:
    """Entry point used by the /tasks/quick-add endpoint."""
    use_real = os.getenv("USE_REAL_LLM", "false").lower() == "true"
    if use_real:
        result = real_llm_parse(description)
        if result is not None:
            return result
    return mock_parse(description)

"""
Grok (xAI) integration for real_llm_parse().
Replace the corresponding section in your Section-3 file with this.
"""
import os
import json
import requests  # pip install requests --break-system-packages

XAI_API_URL = "https://api.x.ai/v1/chat/completions"


def real_llm_parse(description: str) -> Optional[ParsedTask]:
    """
    Calls Grok (xAI) using build_messages() as the conversation, and maps
    the response back into the ParsedTask shape. Falls back to None (which
    triggers mock_parse) on any failure — same contract as before.
    """
    api_key = os.getenv("XAI_API_KEY", "")
    if not api_key:
        return None

    messages = build_messages(description)

    # Add explicit JSON-only instruction so we get clean, parseable output.
    messages[0]["content"] += (
        " Respond ONLY with a raw JSON object with exactly these keys: "
        '"title" (string), "priority" (one of "low", "medium", "high"), '
        '"due_date_hint" (string or null). No markdown, no extra text.'
    )

    try:
        response = requests.post(
            XAI_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "grok-4",          # or "grok-4-fast", check xAI docs for current model names
                "messages": messages,
                "temperature": 0,
                "max_tokens": 200,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        raw_text = data["choices"][0]["message"]["content"].strip()
        # Strip accidental ```json fences if the model adds them.
        raw_text = raw_text.replace("```json", "").replace("```", "").strip()

        parsed = json.loads(raw_text)

        # Basic validation — fall back to mock if shape is wrong.
        if not all(k in parsed for k in ("title", "priority", "due_date_hint")):
            return None
        if parsed["priority"] not in ("low", "medium", "high"):
            return None

        return {
            "title": parsed["title"],
            "priority": parsed["priority"],
            "due_date_hint": parsed["due_date_hint"],
        }

    except Exception:
        # Network error, timeout, bad JSON, missing key, etc. -> mock fallback.
        return None


def parse_description(description: str) -> ParsedTask:
    """Entry point used by the /tasks/quick-add endpoint."""
    use_real = os.getenv("USE_REAL_LLM", "false").lower() == "true"
    if use_real:
        result = real_llm_parse(description)
        if result is not None:
            return result
    return mock_parse(description)