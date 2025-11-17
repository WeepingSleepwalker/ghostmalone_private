# # servers/emotion_server.py
# from fastmcp import FastMCP, tool
# import re

# app = FastMCP("emotion-server")

# _PATTERNS = {
#     "happy":   r"\b(happy|grateful|excited|joy|delighted|content|optimistic)\b",
#     "sad":     r"\b(sad|down|depressed|cry|lonely|upset|miserable)\b",
#     "angry":   r"\b(angry|mad|furious|irritated|pissed|annoyed|resentful)\b",
#     "anxious": r"\b(worried|anxious|nervous|stressed|overwhelmed|scared)\b",
#     "tired":   r"\b(tired|exhausted|drained|burnt|sleepy|fatigued)\b",
#     "love":    r"\b(love|affection|caring|fond|admire|cherish)\b",
#     "fear":    r"\b(afraid|fear|terrified|panicked|shaken)\b",
# }

# _TONES = {"happy":"light","love":"light","sad":"gentle","fear":"gentle",
#           "angry":"calming","anxious":"calming","tired":"gentle"}

# def _analyze(text: str) -> dict:
#     t = text.lower()
#     found = [k for k,pat in _PATTERNS.items() if re.search(pat, t)]
#     valence = 0.0
#     if "happy" in found or "love" in found: valence += 0.6
#     if "sad" in found or "fear" in found:   valence -= 0.6
#     if "angry" in found:                    valence -= 0.4
#     if "anxious" in found:                  valence -= 0.3
#     if "tired" in found:                    valence -= 0.2
#     arousal = 0.5 + (0.3 if ("angry" in found or "anxious" in found) else 0) - (0.2 if "tired" in found else 0)
#     tone = "neutral"
#     for e in found:
#         if e in _TONES: tone = _TONES[e]; break
#     return {
#         "labels": found or ["neutral"],
#         "valence": max(-1, min(1, round(valence, 2))),
#         "arousal": max(0, min(1, round(arousal, 2))),
#         "tone": tone,
#     }

# @tool
# def analyze(text: str) -> dict:
#     """
#     Analyze user text for emotion.
#     Args:
#       text: str - user message
#     Returns: dict {labels, valence, arousal, tone}
#     """
#     return _analyze(text)

# if __name__ == "__main__":
#     app.run()  # serves MCP over stdio
# servers/emotion_server.py
from __future__ import annotations

# ---- FastMCP import shim (works across versions) ----
# Ensures: FastMCP is imported and `@tool` is ALWAYS a callable decorator.
from typing import Callable, Any

try:
    from fastmcp import FastMCP  # present across versions
except Exception as e:
    raise ImportError(f"FastMCP missing: {e}")

_tool_candidate: Any = None
# Try common locations
try:
    from fastmcp import tool as _tool_candidate  # newer API: function
except Exception:
    try:
        from fastmcp.tools import tool as _tool_candidate  # older API: function
    except Exception:
        _tool_candidate = None

# If we somehow got a module instead of a function, try attribute
if _tool_candidate is not None and not callable(_tool_candidate):
    try:
        _tool_candidate = _tool_candidate.tool  # some builds expose module.tools.tool
    except Exception:
        _tool_candidate = None


def tool(*dargs, **dkwargs):
    """
    Wrapper that behaves correctly in both usages:
      @tool
      @tool(...)
    If real decorator exists, delegate. Otherwise:
      - If called as @tool (i.e., first arg is fn), return fn (no-op).
      - If called as @tool(...), return a decorator that returns fn (no-op).
    """
    if callable(_tool_candidate):
        return _tool_candidate(*dargs, **dkwargs)

    # No real decorator available — provide no-op behavior.
    if dargs and callable(dargs[0]) and not dkwargs:
        # Used as @tool
        fn = dargs[0]
        return fn

    # Used as @tool(...)
    def _noop_decorator(fn):
        return fn

    return _noop_decorator


# ---- end shim ----


import re, math, time
from typing import Dict, List, Tuple, Optional

app = FastMCP("emotion-server")

# ---------------------------
# Lexicons & heuristics
# ---------------------------
EMO_LEX = {
    "happy": r"\b(happy|grateful|excited|joy(?:ful)?|delighted|content|optimistic|glad|thrilled|yay|better|good|great|fine)\b",
    "sad": r"\b(sad|down|depress(?:ed|ing)|cry(?:ing)?|lonely|upset|miserable|heartbroken|devastat(?:ed|ing))\b",
    "angry": r"\b(angry|mad|furious|irritated|pissed|pissy|annoyed|resentful|rage|hate|infuriat(?:ed|ing)|frustrat(?:ed|ing)|boiling)\b",
    "anxious": r"\b(worried|anxious|nervous|stressed|overwhelmed|scared|uneasy|tense|on edge|freaking out)\b",
    "tired": r"\b(tired|exhaust(?:ed|ing)|drained|burnt(?:\s*out)?|sleepy|fatigued|worn out)\b",
    "love": r"\b(love|affection|caring|fond|admire|cherish|adore)\b",
    "fear": r"\b(afraid|fear|terrified|panic(?:ky|ked)?|panicked|shaken|petrified)\b",
}

# Emojis contribute signals even without words
EMOJI_SIGNAL = {
    "happy": ["😀", "😄", "😊", "🙂", "😁", "🥳", "✨"],
    "sad": ["😢", "😭", "😞", "😔", "☹️"],
    "angry": ["😠", "😡", "🤬", "💢"],
    "anxious": ["😰", "😱", "😬", "😟", "😧"],
    "tired": ["🥱", "😪", "😴"],
    "love": ["❤️", "💖", "💕", "😍", "🤍", "💗", "💓", "😘"],
    "fear": ["🫣", "😨", "😱", "👀"],
}

NEGATORS = r"\b(no|not|never|hardly|barely|scarcely|isn['’]t|aren['’]t|can['’]t|don['’]t|doesn['’]t|won['’]t|without)\b"
INTENSIFIERS = {
    r"\b(very|really|super|so|extremely|incredibly|totally|absolutely)\b": 1.35,
    r"\b(kinda|kind of|somewhat|slightly|a bit|a little)\b": 0.75,
}
SARCASM_CUES = [
    r"\byeah right\b",
    r"\bsure\b",
    r"\".+\"",
    r"/s\b",
    r"\bokayyy+\b",
    r"\blol\b(?!\w)",
]


# Tone map by quadrant
# arousal high/low × valence pos/neg
def quad_tone(valence: float, arousal: float) -> str:
    if arousal >= 0.6 and valence >= 0.1:
        return "excited"
    if arousal >= 0.6 and valence < -0.1:
        return "concerned"
    if arousal < 0.6 and valence < -0.1:
        return "gentle"
    if arousal < 0.6 and valence >= 0.1:
        return "calm"
    return "neutral"


# ---------------------------
# Utilities
# ---------------------------
_compiled = {k: re.compile(p, re.I) for k, p in EMO_LEX.items()}
_neg_pat = re.compile(NEGATORS, re.I)
_int_pats = [(re.compile(p, re.I), w) for p, w in INTENSIFIERS.items()]
_sarcasm = [re.compile(p, re.I) for p in SARCASM_CUES]


def _emoji_hits(text: str) -> Dict[str, int]:
    hits = {k: 0 for k in EMO_LEX}
    for emo, arr in EMOJI_SIGNAL.items():
        for e in arr:
            hits[emo] += text.count(e)
    return hits


def _intensity_multiplier(text: str) -> float:
    mult = 1.0
    for pat, w in _int_pats:
        if pat.search(text):
            mult *= w
    # Exclamation marks increase arousal a bit (cap effect)
    bangs = min(text.count("!"), 5)
    mult *= 1.0 + 0.04 * bangs
    # ALL CAPS word run nudges intensity
    if re.search(r"\b[A-Z]{3,}\b", text):
        mult *= 1.08
    return max(0.5, min(1.8, mult))


def _negation_factor(text: str, span_start: int) -> float:
    """
    Look 5 words (~40 chars) backwards for a negator.
    If present, invert or dampen signal.
    Stop at clause boundaries (comma, period, semicolon) to avoid cross-clause negation.
    """
    window_start = max(0, span_start - 40)
    window = text[window_start:span_start]

    # Stop at last clause boundary (comma, period, semicolon, colon)
    # This prevents "not responded" from negating "nervous" in "not responded, I'm nervous"
    last_boundary = max(
        window.rfind(","), window.rfind("."), window.rfind(";"), window.rfind(":")
    )
    if last_boundary != -1:
        # Only look after the last boundary
        window = window[last_boundary + 1 :]

    if _neg_pat.search(window):
        return -0.7  # invert and dampen
    return 1.0


def _sarcasm_penalty(text: str) -> float:
    return 0.85 if any(p.search(text) for p in _sarcasm) else 1.0


def _softmax(d: Dict[str, float]) -> Dict[str, float]:
    xs = list(d.values())
    if not xs:
        return d
    m = max(xs)
    exps = [math.exp(x - m) for x in xs]
    s = sum(exps) or 1.0
    return {k: exps[i] / s for i, k in enumerate(d.keys())}


# ---------------------------
# Per-user calibration (in-memory)
# ---------------------------
CALIBRATION: Dict[str, Dict[str, float]] = (
    {}
)  # user_id -> {bias_emo: float, arousal_bias: float, valence_bias: float}


def _apply_calibration(
    user_id: Optional[str], emo_scores: Dict[str, float], valence: float, arousal: float
):
    if not user_id or user_id not in CALIBRATION:
        return emo_scores, valence, arousal
    calib = CALIBRATION[user_id]
    # shift emotions
    for k, bias in calib.items():
        if k in emo_scores:
            emo_scores[k] += bias * 0.2
    # dedicated valence/arousal bias keys if present
    valence += calib.get("valence_bias", 0.0) * 0.15
    arousal += calib.get("arousal_bias", 0.0) * 0.15
    return emo_scores, valence, arousal


# ---------------------------
# Core analysis
# ---------------------------
def _analyze(text: str, user_id: Optional[str] = None) -> dict:
    t = text or ""
    tl = t.lower()

    # Base scores from lexicon hits
    emo_scores: Dict[str, float] = {k: 0.0 for k in EMO_LEX}
    spans: Dict[str, List[Tuple[int, int, str]]] = {k: [] for k in EMO_LEX}

    for emo, pat in _compiled.items():
        for m in pat.finditer(tl):
            factor = _negation_factor(tl, m.start())
            emo_scores[emo] += 1.0 * factor
            spans[emo].append((m.start(), m.end(), tl[m.start() : m.end()]))

    # Emoji contributions
    e_hits = _emoji_hits(t)
    for emo, c in e_hits.items():
        if c:
            emo_scores[emo] += 0.6 * c

    # Check for sarcasm - if detected, invert positive emotions
    sarcasm_detected = any(p.search(tl) for p in _sarcasm)

    if sarcasm_detected:
        # Sarcasm inverts positive emotions to negative
        # "yeah right, like they care" → anger/sadness, not love
        happy_score = emo_scores["happy"]
        love_score = emo_scores["love"]

        if happy_score > 0 or love_score > 0:
            # Transfer positive emotion scores to anger/sad
            emo_scores["angry"] += happy_score * 0.8
            emo_scores["sad"] += love_score * 0.8
            emo_scores["happy"] = 0.0
            emo_scores["love"] = 0.0

    # Intensifiers / punctuation adjustments (global)
    intensity = _intensity_multiplier(t)

    for emo in emo_scores:
        emo_scores[emo] *= intensity

    # Map to valence/arousal
    pos = emo_scores["happy"] + emo_scores["love"]
    neg = (
        emo_scores["sad"]
        + emo_scores["fear"]
        + 0.9 * emo_scores["angry"]
        + 0.6 * emo_scores["anxious"]
    )
    valence = max(-1.0, min(1.0, round((pos - neg) * 0.4, 3)))

    base_arousal = 0.5
    arousal = (
        base_arousal
        + 0.12 * (emo_scores["angry"] > 0)
        + 0.08 * (emo_scores["anxious"] > 0)
        - 0.10 * (emo_scores["tired"] > 0)
        + 0.02 * min(t.count("!"), 5)
    )

    arousal = max(0.0, min(1.0, round(arousal, 3)))

    # Confidence: count signals + consistency
    hits = sum(1 for v in emo_scores.values() if abs(v) > 0.01) + sum(e_hits.values())
    consistency = 0.0
    if hits:
        top2 = sorted(emo_scores.items(), key=lambda kv: kv[1], reverse=True)[:2]
        if len(top2) == 2 and top2[1][1] > 0:
            ratio = top2[0][1] / (top2[1][1] + 1e-6)
            consistency = max(
                0.0, min(1.0, (ratio - 1) / 3)
            )  # >1 means some separation
        elif len(top2) == 1:
            consistency = 0.6
    conf = max(0.0, min(1.0, 0.25 + 0.1 * hits + 0.5 * consistency))
    # downweight very short texts
    if len(t.strip()) < 6:
        conf *= 0.6

    # Normalize emotions to pseudo-probs (softmax over positive scores)
    pos_scores = {k: max(0.0, v) for k, v in emo_scores.items()}
    probs = _softmax(pos_scores)

    # Apply per-user calibration
    probs, valence, arousal = _apply_calibration(user_id, probs, valence, arousal)

    # Tone
    tone = quad_tone(valence, arousal)

    # Explanations
    reasons = []
    if intensity > 1.0:
        reasons.append(f"intensifiers x{intensity:.2f}")
    if sarcasm_detected:
        reasons.append("sarcasm inverted positive emotions")
    if any(
        _neg_pat.search(tl[max(0, s - 40) : s])
        for emo, spans_ in spans.items()
        for (s, _, _) in spans_
    ):
        reasons.append("negation near emotion tokens")
    if any(e_hits.values()):
        reasons.append("emoji signals")

    labels_sorted = sorted(probs.items(), key=lambda kv: kv[1], reverse=True)
    top_labels = [k for k, v in labels_sorted[:3] if v > 0.05] or ["neutral"]

    return {
        "labels": top_labels,
        "scores": {k: round(v, 3) for k, v in probs.items()},
        "valence": round(valence, 3),
        "arousal": round(arousal, 3),
        "tone": tone,
        "confidence": round(conf, 3),
        "reasons": reasons,
        "spans": {k: spans[k] for k in top_labels if spans.get(k)},
        "ts": time.time(),
        "user_id": user_id,
    }


# ---------------------------
# MCP tools
# ---------------------------


@app.tool()
def analyze(text: str, user_id: Optional[str] = None) -> dict:
    """
    Analyze text for emotion.
    Args:
      text: user message
      user_id: optional user key for calibration
    Returns:
      dict with labels, scores (per emotion), valence [-1..1], arousal [0..1],
      tone (calm/neutral/excited/concerned/gentle), confidence, reasons, spans.
    """
    return _analyze(text, user_id=user_id)


@app.tool()
def batch_analyze(messages: List[str], user_id: Optional[str] = None) -> List[dict]:
    """
    Batch analyze a list of messages.
    """
    return [_analyze(m or "", user_id=user_id) for m in messages]


@app.tool()
def calibrate(
    user_id: str,
    bias: Dict[str, float] = None,
    arousal_bias: float = 0.0,
    valence_bias: float = 0.0,
) -> dict:
    """
    Adjust per-user calibration.
    - bias: e.g. {"anxious": -0.1, "love": 0.1}
    - arousal_bias/valence_bias: small nudges (-1..1) applied after scoring.
    """
    if user_id not in CALIBRATION:
        CALIBRATION[user_id] = {}
    if bias:
        for k, v in bias.items():
            CALIBRATION[user_id][k] = float(v)
    if arousal_bias:
        CALIBRATION[user_id]["arousal_bias"] = float(arousal_bias)
    if valence_bias:
        CALIBRATION[user_id]["valence_bias"] = float(valence_bias)
    return {"ok": True, "calibration": CALIBRATION[user_id]}


@app.tool()
def reset_calibration(user_id: str) -> dict:
    """Remove per-user calibration."""
    CALIBRATION.pop(user_id, None)
    return {"ok": True}


@app.tool()
def health() -> dict:
    """Simple health check for MCP status chips."""
    return {"status": "ok", "version": "1.2.0", "time": time.time()}


@app.tool()
def version() -> dict:
    """Return server version & feature flags."""
    return {
        "name": "emotion-server",
        "version": "1.2.0",
        "features": [
            "negation",
            "intensifiers",
            "emoji",
            "sarcasm",
            "confidence",
            "batch",
            "calibration",
        ],
        "emotions": list(EMO_LEX.keys()),
    }


if __name__ == "__main__":
    app.run()  # serves MCP over stdio
