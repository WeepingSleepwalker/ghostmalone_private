# servers/reflection_server.py
from fastmcp import FastMCP, tool
from typing import List, Dict, Any, Optional
import os

# Optional: load .env if you want this server runnable standalone
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

app = FastMCP("reflection-server")

_SYSTEM_BASE = (
    "You are Ghost Malone — a calm, humorous listener. "
    "Be sincere, brief (<80 words), and reflective. "
    "If the user seems distressed, be gentle and grounding."
)

def _system_prompt(tone: Optional[str], emotion_arc: Optional[dict] = None) -> str:
    base = (
        "You are Ghost Malone — a calm, humorous listener. "
        "Be sincere, brief (<80 words), and reflective. "
        "If the user seems distressed, be gentle and grounding."
    )

    tone_map = {
        "gentle": "Your tone is gentle and reassuring.",
        "calming": "Your tone is calming and steady.",
        "light": "Your tone is light and encouraging.",
        "neutral": "Keep a neutral, warm tone.",
    }
    tone_hint = tone_map.get(tone.lower() if tone else "", "Keep a neutral, warm tone.")

    # NEW: Add emotional trajectory awareness
    arc_hint = ""
    if emotion_arc and emotion_arc.get("trajectory"):
        direction = emotion_arc.get("direction", "stable")
        if direction == "escalating":
            arc_hint = " Notice they're escalating—validate and ground gently."
        elif direction == "de-escalating":
            arc_hint = " Great news: they're calming down—reinforce that momentum."
        elif direction == "volatile":
            arc_hint = " They're experiencing emotional shifts—steady support helps."

    return f"{base} {tone_hint}{arc_hint}"

def _to_claude_messages(context: Optional[List[Dict[str, str]]], user_text: str, tone: Optional[str]):
    """Convert to Claude message format (system separate, no duplicate system messages)."""
    msgs: List[Dict[str, str]] = []
    if context:
        # Expecting list of {"role": "...", "content": "..."} dicts
        for m in context[-8:]:  # last few turns
            role = m.get("role", "user")
            if role == "system":
                continue  # Claude doesn't support system in message list
            content = m.get("content", "")
            msgs.append({"role": role, "content": content})
    msgs.append({"role": "user", "content": user_text})
    return msgs

@tool
def generate(
    text: str,
    context: Optional[List[Dict[str, str]]] = None,
    tone: Optional[str] = None,
    emotion_arc: Optional[dict] = None,
    model: str = "claude-3-5-sonnet-20241022",
    max_tokens: int = 200,
) -> Dict[str, Any]:
    """
    Generate a Ghost Malone reply using Claude.
    Args:
      text:        user message
      context:     prior messages as [{"role":"user|assistant|system", "content":"..."}]
      tone:        optional tone hint: 'gentle'|'calming'|'light'|'neutral'
      emotion_arc: optional emotion trajectory {"trajectory":[...], "direction": str}
      model:       Claude model id (default claude-3-5-sonnet-20241022)
      max_tokens:  output length cap
    Returns: {"reply": "...", "model": model, "tone": tone}
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        return {"reply": f"👻 (dev-reflection) I hear you: {text}", "model": "dev", "tone": tone or "neutral"}

    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)
        system_prompt = _system_prompt(tone, emotion_arc)
        messages = _to_claude_messages(context, text, tone)

        resp = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages
        )
        reply = resp.content[0].text
        return {"reply": reply, "model": model, "tone": tone or "neutral"}
    except Exception as e:
        return {"reply": f"👻 (reflection error) {e}\nI still hear you: {text}", "model": model, "tone": tone or "neutral"}
if __name__ == "__main__":
    app.run()  # MCP over stdio
