# # servers/memory_server.py
# from fastmcp import FastMCP, tool
# import json, os, time

# app = FastMCP("memory-server")
# FILE = os.environ.get("GM_MEMORY_FILE", "memory.json")

# def _load():
#     if os.path.exists(FILE):
#         with open(FILE) as f: return json.load(f)
#     return []

# def _save(history):
#     with open(FILE, "w") as f: json.dump(history[-50:], f)  # keep up to 50

# @tool
# def remember(text: str, meta: dict | None = None) -> dict:
#     """
#     Append an entry to memory.
#     Args:
#       text: str - content to store
#       meta: dict - optional info like {"tone":"gentle","labels":["sad"]}
#     Returns: {"ok": True, "size": <n>}
#     """
#     data = _load()
#     data.append({"t": int(time.time()), "text": text, "meta": meta or {}})
#     _save(data)
#     return {"ok": True, "size": len(data)}

# @tool
# def recall(k: int = 3) -> dict:
#     """
#     Return last k entries from memory (most recent last).
#     Args:
#       k: int - how many items
#     Returns: {"items":[...]}
#     """
#     data = _load()
#     return {"items": data[-k:]}

# if __name__ == "__main__":
#     app.run()
# servers/memory_server.py
# servers/memory_server.py
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
    from fastmcp import tool as _tool_candidate       # newer API: function
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


import json, os, time, math, re
from typing import Dict, List, Optional, Any, Tuple
from collections import Counter

app = FastMCP("memory-server")

# ---------------------------
# Storage & limits
# ---------------------------
FILE = os.environ.get("GM_MEMORY_FILE", "memory.json")
STM_MAX = int(os.environ.get("GM_STM_MAX", "120"))
EP_MAX  = int(os.environ.get("GM_EPISODES_MAX", "240"))
FACT_MAX= int(os.environ.get("GM_FACTS_MAX", "200"))
# ---------------------------
# Emotion Drift Analysis
# ---------------------------
def compute_emotional_direction(trajectory: List[Dict[str, Any]]) -> str:
    """
    Analyze emotion trajectory to detect escalation/de-escalation/volatility/stability.
    trajectory: list of {"label": str, "valence": float, "arousal": float, "ts": int}
    """
    if len(trajectory) < 2:
        return "stable"

    # Get last 5 emotions for trend
    recent = trajectory[-5:]
    valences = [e.get("valence", 0.0) for e in recent]
    arousals = [e.get("arousal", 0.5) for e in recent]

    # Detect trend
    valence_trend = valences[-1] - valences[0]  # negative = more negative, positive = more positive
    arousal_trend = arousals[-1] - arousals[0]  # positive = escalating

    # Classify
    if arousal_trend > 0.15 and valence_trend < -0.1:
        return "escalating"  # Getting more activated and negative
    elif arousal_trend < -0.15 and valence_trend > 0.1:
        return "de-escalating"  # Calming down and more positive
    elif max(arousals) - min(arousals) > 0.3:
        return "volatile"  # Wide swings in arousal
    else:
        return "stable"

def get_emotion_trajectory(store: Dict[str, Any], k: int = 10) -> Tuple[List[Dict[str, Any]], str]:
    """
    Returns last k emotion events from memory and the trajectory direction.
    If a message is neutral, it inherits the previous emotion state.
    """
    stm = store.get("stm", [])
    trajectory = []
    last_emotion_state = None  # Track last non-neutral emotion

    for item in stm[-k:]:
        # Check if emotion data is in event.emotion (from remember_event)
        event = item.get("event", {})
        emotion = event.get("emotion", {})

        # Also check if emotion data is in meta (from remember)
        if not emotion or not emotion.get("labels"):
            meta = item.get("meta", {})
            if meta and meta.get("labels"):
                emotion = meta

        if emotion and emotion.get("labels"):
            primary_label = (emotion.get("labels") or ["neutral"])[0]
            valence = float(emotion.get("valence", 0.0))
            arousal = float(emotion.get("arousal", 0.5))

            # If this is neutral/weak emotion, inherit previous state
            confidence = float(emotion.get("confidence", 0.25))
            if primary_label in ["happy", "neutral"] and confidence < 0.35 and last_emotion_state:
                # Carry forward previous emotion (decay slightly toward neutral)
                primary_label = last_emotion_state["primary_label"]
                valence = last_emotion_state["valence"] * 0.8  # Slight decay
                arousal = last_emotion_state["arousal"] * 0.9
            else:
                # Strong emotion detected, update state
                last_emotion_state = {
                    "primary_label": primary_label,
                    "valence": valence,
                    "arousal": arousal
                }

            trajectory.append({
                "primary_label": primary_label,
                "valence": valence,
                "arousal": arousal,
                "ts": item.get("t", int(time.time())),
                "text": item.get("text", "")[:50]  # First 50 chars
            })

    direction = compute_emotional_direction(trajectory)
    return trajectory, direction
# ---------------------------
# File helpers & migrations
# ---------------------------
def _default_store() -> Dict[str, Any]:
    return {"stm": [], "episodes": [], "facts": [], "meta": {"created": int(time.time()), "version": "1.3.0"}}

def _load() -> Dict[str, Any]:
    if os.path.exists(FILE):
        with open(FILE) as f:
            try:
                data = json.load(f)
                # migrate flat list → tiered
                if isinstance(data, list):
                    data = {"stm": data[-STM_MAX:], "episodes": [], "facts": [], "meta": {"created": int(time.time()), "version": "1.3.0"}}
                # backfill ids in stm
                changed = False
                for i, it in enumerate(data.get("stm", [])):
                    if "id" not in it:
                        it["id"] = f"stm-{it.get('t', int(time.time()))}-{i}"
                        changed = True
                if changed:
                    _save(data)
                return data
            except Exception:
                return _default_store()
    return _default_store()

def _save(store: Dict[str, Any]) -> None:
    store["stm"]      = store.get("stm", [])[-STM_MAX:]
    store["episodes"] = store.get("episodes", [])[-EP_MAX:]
    store["facts"]    = store.get("facts", [])[-FACT_MAX:]
    with open(FILE, "w") as f:
        json.dump(store, f, ensure_ascii=False)

# ---------------------------
# Salience & decay (same as before)
# ---------------------------
def time_decay(ts: float, now: Optional[float] = None, half_life_hours: float = 72.0) -> float:
    now = now or time.time()
    dt_h = max(0.0, (now - ts) / 3600.0)
    return 0.5 ** (dt_h / half_life_hours)

_WORD = re.compile(r"[a-zA-Z']+")

def keyword_set(text: str) -> set:
    return set(w.lower() for w in _WORD.findall(text or "") if len(w) > 2)

def novelty_score(text: str, recent_texts: List[str], k: int = 10) -> float:
    if not text:
        return 0.0
    A = keyword_set(text)
    if not A:
        return 0.0
    recent = [keyword_set(t) for t in recent_texts[-k:] if t]
    if not recent:
        return 1.0
    sims = []
    for B in recent:
        inter = len(A & B)
        union = len(A | B) or 1
        sims.append(inter / union)
    sim = max(sims) if sims else 0.0
    return max(0.0, 1.0 - sim)

def compute_salience(ev: Dict[str, Any], recent_texts: List[str]) -> float:
    labels = ev.get("emotion", {}).get("labels") or []
    conf   = float(ev.get("emotion", {}).get("confidence") or 0.0)
    valence= float(ev.get("emotion", {}).get("valence") or 0.0)
    arousal= float(ev.get("emotion", {}).get("arousal") or 0.5)
    sinc   = float(ev.get("sincerity") or 0.0) / 100.0
    text   = ev.get("text", "")

    affect = abs(valence) * (0.7 + 0.3 * arousal) * conf
    nov = novelty_score(text, recent_texts)
    user_flag = 1.0 if ev.get("user_pinned") else 0.0
    boundary  = 1.0 if ev.get("task_boundary") else 0.0

    sal = 0.45 * affect + 0.25 * nov + 0.18 * user_flag + 0.12 * boundary + 0.10 * sinc
    return round(max(0.0, min(1.0, sal)), 3)

# ---------------------------
# Episode & fact synthesis
# ---------------------------
def make_episode(ev: Dict[str, Any], salience: float) -> Dict[str, Any]:
    emo = ev.get("emotion", {})
    return {
        "episode_id": ev.get("id") or f"ep-{int(time.time()*1000)}",
        "ts_start": ev.get("ts") or int(time.time()),
        "ts_end": ev.get("ts") or int(time.time()),
        "summary": ev.get("summary") or (ev.get("text")[:140] if ev.get("text") else ""),
        "topics": list(set(emo.get("labels") or [])) or ["misc"],
        "emotion_peak": (emo.get("labels") or ["neutral"])[0],
        "emotion_conf": float(emo.get("confidence") or 0.0),
        "tone": emo.get("tone") or "neutral",
        "salience": float(salience),
        "provenance_event": ev.get("id"),
    }

def cluster_topics(episodes: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    buckets: Dict[str, List[Dict[str, Any]]] = {}
    for ep in episodes:
        for t in ep.get("topics") or ["misc"]:
            buckets.setdefault(t, []).append(ep)
    return buckets

def synthesize_fact(topic: str, eps: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not eps:
        return None
    support = len(eps)
    avg_sal = sum(e.get("salience", 0.0) for e in eps) / max(1, support)
    avg_conf= sum(e.get("emotion_conf", 0.0) for e in eps) / max(1, support)
    conf = max(0.0, min(1.0, 0.5 * avg_sal + 0.5 * avg_conf))
    if support < 3 or conf < 0.6:
        return None
    tones = {}
    for e in eps: tones[e.get("tone", "neutral")] = tones.get(e.get("tone", "neutral"), 0) + 1
    top_tone = sorted(tones.items(), key=lambda kv: kv[1], reverse=True)[0][0]
    return {
        "fact_id": f"fact-{topic}-{int(time.time())}",
        "proposition": f"Prefers {top_tone} tone for topic '{topic}'",
        "support": support,
        "confidence": round(conf, 2),
        "last_updated": int(time.time()),
        "topics": [topic],
        "provenance_episode_ids": [e["episode_id"] for e in eps],
    }

# ---------------------------
# ID helpers
# ---------------------------
def _ensure_stm_id(item: Dict[str, Any], idx: int) -> Dict[str, Any]:
    if "id" not in item:
        item["id"] = f"stm-{item.get('t', int(time.time()))}-{idx}"
    return item

def _stm_text(item: Dict[str, Any]) -> str:
    if "text" in item and isinstance(item["text"], str):
        return item["text"]
    return (item.get("event") or {}).get("text", "") or ""

def _collect_docs(store: Dict[str, Any], tier: Optional[str] = None) -> List[Tuple[str,str,str,int]]:
    """
    Returns list of (id, tier, text, ts)
    """
    docs: List[Tuple[str,str,str,int]] = []
    if tier in (None, "stm"):
        for i, it in enumerate(store.get("stm", [])):
            it = _ensure_stm_id(it, i)
            docs.append((it["id"], "stm", _stm_text(it), int(it.get("t", time.time()))))
    if tier in (None, "episodes"):
        for ep in store.get("episodes", []):
            docs.append((ep.get("episode_id",""), "episodes", ep.get("summary",""), int(ep.get("ts_end", time.time()))))
    if tier in (None, "facts"):
        for f in store.get("facts", []):
            docs.append((f.get("fact_id",""), "facts", f.get("proposition",""), int(f.get("last_updated", time.time()))))
    return [d for d in docs if d[0] and d[2]]

# ---------------------------
# Simple TF-IDF search
# ---------------------------
def _tfidf_rank(query: str, docs: List[Tuple[str,str,str,int]], k: int = 5):
    q_terms = [w for w in keyword_set(query)]
    if not q_terms or not docs:
        return []
    # DF
    df = Counter()
    doc_terms = {}
    for _id, _tier, text, _ts in docs:
        terms = [w for w in keyword_set(text)]
        doc_terms[_id] = terms
        for t in set(terms):
            df[t] += 1
    N = len(docs)
    idf = {t: math.log((N + 1) / (df[t] + 1)) + 1.0 for t in df}
    # Score
    scored = []
    qset = set(q_terms)
    for _id, _tier, text, _ts in docs:
        terms = doc_terms[_id]
        tf = Counter(terms)
        score = 0.0
        matched = []
        for t in q_terms:
            if tf[t] > 0:
                score += tf[t] * idf.get(t, 1.0)
                matched.append(t)
        if score > 0:
            scored.append((_id, _tier, text, _ts, score, matched))
    scored.sort(key=lambda x: (-x[4], -x[3]))  # score desc, then recent
    return scored[:k]

# ---------------------------
# Tools (API)
# ---------------------------

@app.tool()
def remember(text: str, meta: dict | None = None) -> dict:
    store = _load()
    item = {"t": int(time.time()), "text": text, "meta": meta or {}}
    item["id"] = f"stm-{item['t']}-{len(store.get('stm', []))}"
    store["stm"].append(item)
    _save(store)
    return {"ok": True, "stm_size": len(store["stm"]), "id": item["id"]}

@app.tool()
def remember_event(event: dict, promote: bool = True) -> dict:
    store = _load()
    ev = dict(event or {})
    ev.setdefault("ts", int(time.time()))
    ev.setdefault("role", "user")
    ev.setdefault("text", "")
    if "salience" not in ev:
        recent_texts = [it.get("text","") for it in store.get("stm", [])[-10:]]
        ev["salience"] = compute_salience(ev, recent_texts)
    stm_item = {
        "id": f"stm-{ev['ts']}-{len(store.get('stm', []))}",
        "t": ev["ts"],
        "text": ev.get("text",""),
        "event": ev
    }
    store["stm"].append(stm_item)
    if promote:
        aff_conf = float(ev.get("emotion", {}).get("confidence") or 0.0)
        if ev["salience"] >= 0.45 or ev.get("user_pinned") or ev.get("task_boundary"):
            ep = make_episode(ev, ev["salience"])
            store["episodes"].append(ep)
    _save(store)
    return {"ok": True, "salience": ev["salience"], "id": stm_item["id"],
            "sizes": {"stm": len(store["stm"]), "episodes": len(store["episodes"]), "facts": len(store["facts"])}}

@app.tool()
def recall(k: int = 3) -> dict:
    store = _load()
    items = store.get("stm", [])[-k:]
    return {"items": items}

@app.tool()
def recall_episodes(k: int = 5, topic: str | None = None) -> dict:
    store = _load()
    eps = store.get("episodes", [])
    if topic:
        eps = [e for e in eps if topic in (e.get("topics") or [])]
    return {"items": eps[-k:]}

@app.tool()
def recall_facts() -> dict:
    store = _load()
    return {"facts": store.get("facts", [])}

@app.tool()
def reflect() -> dict:
    store = _load()
    eps = store.get("episodes", [])
    if not eps:
        return {"ok": True, "updated": 0, "facts": store.get("facts", [])}
    buckets = cluster_topics(eps)
    new_facts = []
    for topic, group in buckets.items():
        fact = synthesize_fact(topic, group)
        if fact:
            existing = next((f for f in store["facts"] if f.get("proposition") == fact["proposition"]), None)
            if existing:
                existing["support"] = max(existing.get("support", 0), fact["support"])
                existing["confidence"] = round(max(existing.get("confidence", 0.0), fact["confidence"]), 2)
                existing["last_updated"] = int(time.time())
            else:
                new_facts.append(fact)
    store["facts"].extend(new_facts)
    _save(store)
    return {"ok": True, "updated": len(new_facts), "facts": store["facts"]}

@app.tool()
def prune(before_ts: int | None = None) -> dict:
    store = _load()
    stm = store.get("stm", [])
    if before_ts:
        stm = [it for it in stm if it.get("t", 0) >= int(before_ts)]
    else:
        cut = int(len(stm) * 0.75)
        stm = stm[cut:]
    store["stm"] = stm
    _save(store)
    return {"ok": True, "stm_size": len(store["stm"])}

# -------- NEW: search / get / delete / list --------

@app.tool()
def search(query: str, tier: str | None = None, k: int = 5) -> dict:
    """
    TF-IDF search across memory.
    Args:
      query: text to search
      tier: one of {"stm","episodes","facts"} or None for all
      k: number of results
    Returns: {"results":[{"id","tier","text","ts","score","matched"}]}
    """
    store = _load()
    docs = _collect_docs(store, tier=tier)
    ranked = _tfidf_rank(query, docs, k=k)
    results = [{"id": _id, "tier": _tier, "text": text, "ts": ts, "score": round(score,3), "matched": matched}
               for (_id, _tier, text, ts, score, matched) in ranked]
    return {"results": results}

@app.tool()
def get(item_id: str) -> dict:
    """
    Fetch a single item by id from any tier.
    """
    s = _load()
    for it in s.get("stm", []):
        if it.get("id") == item_id:
            return {"tier": "stm", "item": it}
    for ep in s.get("episodes", []):
        if ep.get("episode_id") == item_id:
            return {"tier": "episodes", "item": ep}
    for f in s.get("facts", []):
        if f.get("fact_id") == item_id:
            return {"tier": "facts", "item": f}
    return {"tier": None, "item": None}

@app.tool()
def delete_by_id(item_id: str, tier: str | None = None) -> dict:
    """
    Delete a single item by id. If tier is None, searches all tiers.
    Returns {"ok": bool, "removed_from": <tier>|None}
    """
    s = _load()
    removed_from = None
    if tier in (None, "stm"):
        before = len(s["stm"])
        s["stm"] = [it for it in s["stm"] if it.get("id") != item_id]
        if len(s["stm"]) != before: removed_from = "stm"
    if not removed_from and tier in (None, "episodes"):
        before = len(s["episodes"])
        s["episodes"] = [e for e in s["episodes"] if e.get("episode_id") != item_id]
        if len(s["episodes"]) != before: removed_from = "episodes"
    if not removed_from and tier in (None, "facts"):
        before = len(s["facts"])
        s["facts"] = [f for f in s["facts"] if f.get("fact_id") != item_id]
        if len(s["facts"]) != before: removed_from = "facts"
    if removed_from:
        _save(s)
        return {"ok": True, "removed_from": removed_from}
    return {"ok": False, "removed_from": None}

@app.tool()
def list_items(tier: str, k: int = 10) -> dict:
    """
    List last k items in a tier.
    tier ∈ {"stm","episodes","facts"}
    """
    s = _load()
    if tier == "stm":
        return {"items": s.get("stm", [])[-k:]}
    if tier == "episodes":
        return {"items": s.get("episodes", [])[-k:]}
    if tier == "facts":
        return {"items": s.get("facts", [])[-k:]}
    return {"items": []}

# -------- Diagnostics --------

@app.tool()
def stats() -> dict:
    s = _load()
    return {
        "stm": len(s.get("stm", [])),
        "episodes": len(s.get("episodes", [])),
        "facts": len(s.get("facts", [])),
        "file": FILE,
        "created": s.get("meta", {}).get("created"),
        "version": s.get("meta", {}).get("version", "1.3.0"),
    }

@app.tool()
def health() -> dict:
    try:
        s = _load()
        return {"status": "ok", "stm": len(s.get("stm", [])), "episodes": len(s.get("episodes", [])), "facts": len(s.get("facts", [])), "time": time.time(), "version": "1.3.0"}
    except Exception as e:
        return {"status": "error", "error": str(e), "time": time.time()}

@app.tool()
def version() -> dict:
    return {"name": "memory-server", "version": "1.3.0", "tiers": ["stm","episodes","facts"], "file": FILE}

@app.tool()
def get_emotion_arc(k: int = 10) -> dict:
    """
    Get the emotion trajectory (arc) for the last k events.
    Returns: {"trajectory": [...], "direction": "escalating|de-escalating|volatile|stable", "summary": str}
    """
    store = _load()
    trajectory, direction = get_emotion_trajectory(store, k=k)

    if not trajectory:
        return {"trajectory": [], "direction": "unknown", "summary": "No emotion history"}

    # Create readable summary
    emotions = [t["primary_label"] for t in trajectory]
    summary = " → ".join(emotions[-5:]) if len(emotions) >= 5 else " → ".join(emotions)

    return {
        "trajectory": trajectory,
        "direction": direction,
        "summary": summary
    }

if __name__ == "__main__":
    app.run()  # serves MCP over stdio
