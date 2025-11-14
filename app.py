#!/usr/bin/env python3
"""Ghost Malone: MCP-powered emotional intelligence chatbot"""

import json
import asyncio
from dotenv import load_dotenv
import gradio as gr

from utils.mcp_client import MCPMux

load_dotenv()

mux = MCPMux()
_event_loop = None

async def _boot_mcp():
    """Bootstrap MCP connections to emotion, memory, and reflection servers."""
    await mux.connect_stdio("emotion", "python", args=["servers/emotion_server.py"])
    await mux.connect_stdio("memory", "python", args=["servers/memory_server.py"])
    await mux.connect_stdio("reflect", "python", args=["servers/reflection_server.py"])
    tools = await mux.list_all_tools()
    print(f"🧰 MCP tools discovered: {tools}")

# Create a persistent event loop for MCP
_event_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_event_loop)
_event_loop.run_until_complete(_boot_mcp())

def _run(coro):
    """Run async coroutine in the persistent event loop."""
    return _event_loop.run_until_complete(coro)

def _parse_json_maybe(s: str):
    try:
        return json.loads(s)
    except Exception:
        return None

def chat(user_msg: str, messages: list[dict] | None):
    messages = messages or []
    messages.append({"role": "user", "content": user_msg})

    tone = "neutral"
    emo_meta = {"tone": tone, "labels": ["neutral"], "valence": 0.0, "arousal": 0.5}
    try:
        emo_raw = _run(mux.call("analyze", {"text": user_msg}))
        print(f"DEBUG emotion.analyze raw response: {emo_raw}")
        parsed = _parse_json_maybe(emo_raw) if isinstance(emo_raw, str) else emo_raw
        if isinstance(parsed, dict):
            emo_meta.update(parsed)
            tone = parsed.get("tone", tone)
    except Exception as e:
        print(f"⚠️ emotion.analyze failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

    try:
        _ = _run(mux.call("remember", {"text": user_msg, "meta": emo_meta}))
    except Exception as e:
        print(f"⚠️ memory.remember failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

    # Get emotion arc trajectory for context
    emotion_arc = None
    arc_str = ""
    try:
        arc_raw = _run(mux.call("get_emotion_arc", {"k": 10}))
        emotion_arc = _parse_json_maybe(arc_raw) if isinstance(arc_raw, str) else arc_raw
        if isinstance(emotion_arc, dict):
            trajectory = emotion_arc.get("trajectory", [])
            direction = emotion_arc.get("direction", "stable")
            arc_str = f"[emotion_arc: {direction}, trajectory_length={len(trajectory)}]"
    except Exception as e:
        print(f"⚠️ memory.get_emotion_arc failed: {e}")

    try:
        gen_raw = _run(mux.call("generate", {
            "text": user_msg,
            "context": messages[:-1],
            "tone": tone,
            "emotion_arc": emotion_arc or {},
            "model": "claude-sonnet-4-5",
            "max_tokens": 200
        }))
        gen = _parse_json_maybe(gen_raw) if isinstance(gen_raw, str) else gen_raw
        reply = gen.get("reply") if isinstance(gen, dict) else str(gen_raw)
    except Exception as e:
        reply = f"👻 (client-reflection error) {e}\nI still hear you: {user_msg}"

    messages.append({"role": "assistant", "content": reply})
    return messages, messages, "", arc_str

with gr.Blocks(title="Ghost Malone") as demo:
    gr.Markdown("## 👻 Ghost Malone\n*A calm AI that listens before it talks.*")
    chatbot = gr.Chatbot(type="messages", height=420)
    emotion_arc_md = gr.Markdown("📊 *Emotion arc will appear here*")
    state = gr.State([])
    msg = gr.Textbox(placeholder="Tell Ghost Malone what's on your mind...", label="Message")
    msg.submit(chat, [msg, state], [chatbot, state, msg, emotion_arc_md])

    with gr.Accordion("🧰 MCP Tools (manual)", open=False):
        tool_name = gr.Textbox(label="Tool name (e.g., analyze, remember)")
        tool_args = gr.Textbox(label='Args JSON (e.g., {"text":"hello"})')
        run_btn = gr.Button("Run tool")
        async def run_tool(name: str, args_text: str, messages: list[dict] | None):
            messages = messages or []
            try:
                args = json.loads(args_text) if args_text.strip() else {}
            except json.JSONDecodeError as e:
                messages.append({"role":"assistant","content":f"🛠️ Invalid JSON: {e}"})
                return messages, messages
            try:
                out = await mux.call(name, args)
                messages.append({"role":"assistant","content":f"🛠️ `{name}` →\n{out}"})
            except Exception as e:
                messages.append({"role":"assistant","content":f"🛠️ `{name}` error → {e}"})
            return messages, messages
        run_btn.click(run_tool, [tool_name, tool_args, state], [chatbot, state])

if __name__ == "__main__":
    print("🚀 starting Ghost Malone server…")
    demo.launch(server_name="127.0.0.1", server_port=7863, share=True)
