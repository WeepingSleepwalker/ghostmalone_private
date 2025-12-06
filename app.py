#!/usr/bin/env python3
"""Ghost Malone: MCP-powered emotional intelligence chatbot"""

import json
import asyncio
import os
from dotenv import load_dotenv
import gradio as gr
import plotly.graph_objects as go

from utils.orchestrator import get_orchestrator

load_dotenv()

# Clear memory on startup for fresh conversations
if os.path.exists("memory.json"):
    os.remove("memory.json")
    print("🧹 Cleared previous memory for fresh start")

_event_loop = None
_orchestrator = None


async def _boot_orchestrator():
    """Bootstrap the orchestrator with all MCP servers."""
    global _orchestrator
    _orchestrator = await get_orchestrator()
    print("🧰 Ghost Malone orchestrator initialized")


# Create a persistent event loop
_event_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_event_loop)
_event_loop.run_until_complete(_boot_orchestrator())


def _run(coro):
    """Run async coroutine in the persistent event loop."""
    return _event_loop.run_until_complete(coro)


def create_emotion_plot(emotion_arc):
    """Create a Plotly scatter plot showing emotions on valence/arousal grid."""
    if not emotion_arc or not emotion_arc.get("trajectory"):
        # Empty plot with quadrant labels
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=[0],
                y=[0.5],
                mode="markers",
                marker=dict(size=1, color="lightgray"),
                showlegend=False,
            )
        )

        # Add quadrant labels
        fig.add_annotation(
            x=0.5,
            y=0.75,
            text="Excited",
            showarrow=False,
            font=dict(size=10, color="gray"),
        )
        fig.add_annotation(
            x=-0.5,
            y=0.75,
            text="Anxious",
            showarrow=False,
            font=dict(size=10, color="gray"),
        )
        fig.add_annotation(
            x=0.5,
            y=0.25,
            text="Calm",
            showarrow=False,
            font=dict(size=10, color="gray"),
        )
        fig.add_annotation(
            x=-0.5,
            y=0.25,
            text="Sad",
            showarrow=False,
            font=dict(size=10, color="gray"),
        )

        fig.update_layout(
            title="Emotion Trajectory (Valence × Arousal)",
            xaxis=dict(title="Valence", range=[-1.2, 1.2], zeroline=True),
            yaxis=dict(title="Arousal", range=[-0.1, 1.1], zeroline=False),
            height=500,
            showlegend=False,
        )
        return fig

    trajectory = emotion_arc.get("trajectory", [])

    # Extract valence and arousal from trajectory
    x_vals = [item.get("valence", 0) for item in trajectory]
    y_vals = [item.get("arousal", 0.5) for item in trajectory]
    labels = [item.get("primary_label", "neutral") for item in trajectory]

    # Color points from oldest (light) to newest (dark)
    colors = list(range(len(x_vals)))

    fig = go.Figure()

    # Add trajectory line
    if len(x_vals) > 1:
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=y_vals,
                mode="lines",
                line=dict(color="lightblue", width=1, dash="dot"),
                showlegend=False,
                hoverinfo="skip",
            )
        )

    # Add emotion points
    fig.add_trace(
        go.Scatter(
            x=x_vals,
            y=y_vals,
            mode="markers+text",
            marker=dict(
                size=12,
                color=colors,
                colorscale="Blues",
                showscale=False,
                line=dict(width=1, color="white"),
            ),
            text=labels,
            textposition="top center",
            textfont=dict(size=8),
            hovertemplate="<b>%{text}</b><br>Valence: %{x:.2f}<br>Arousal: %{y:.2f}<extra></extra>",
            showlegend=False,
        )
    )

    # Add quadrant labels
    fig.add_annotation(
        x=0.5,
        y=0.75,
        text="Excited",
        showarrow=False,
        font=dict(size=10, color="lightgray"),
    )
    fig.add_annotation(
        x=-0.5,
        y=0.75,
        text="Anxious",
        showarrow=False,
        font=dict(size=10, color="lightgray"),
    )
    fig.add_annotation(
        x=0.5,
        y=0.25,
        text="Calm",
        showarrow=False,
        font=dict(size=10, color="lightgray"),
    )
    fig.add_annotation(
        x=-0.5,
        y=0.25,
        text="Sad",
        showarrow=False,
        font=dict(size=10, color="lightgray"),
    )

    # Add quadrant lines
    fig.add_hline(y=0.5, line=dict(color="lightgray", width=1, dash="dash"))
    fig.add_vline(x=0, line=dict(color="lightgray", width=1, dash="dash"))

    direction = emotion_arc.get("direction", "stable")
    fig.update_layout(
        title=f"Emotion Trajectory: {direction}",
        xaxis=dict(title="Valence (negative ← → positive)", range=[-1.2, 1.2]),
        yaxis=dict(title="Arousal (calm ← → intense)", range=[-0.1, 1.1]),
        height=500,
        showlegend=False,
        plot_bgcolor="#fafafa",
    )

    return fig


def chat(
    user_msg: str,
    messages: list[dict] | None,
    min_msgs: int,
    min_conf: float,
    min_arous: float,
):
    messages = messages or []
    messages.append({"role": "user", "content": user_msg})

    # Show thinking indicator (must return 6 values: chatbot, state, msg, emotion_arc_md, plot, debug_panel, toolbox)
    thinking_msg = {"role": "assistant", "content": "👻 *Ghost Malone is listening...*"}
    toolbox_log = "🧰 **Toolbox Activity:**\n\n⏳ Initializing pipeline..."
    yield messages + [
        thinking_msg
    ], messages, user_msg, "📊 *Analyzing emotions and needs...*", None, "🔍 DEBUG: Processing...", toolbox_log

    # Use orchestrator for full pipeline with custom thresholds
    try:
        result = _run(
            _orchestrator.process_message(
                user_text=user_msg,
                conversation_context=messages[:-1],
                intervention_thresholds={
                    "min_messages": int(min_msgs),
                    "min_confidence": float(min_conf),
                    "min_arousal": float(min_arous),
                },
            )
        )

        # Extract data from result
        emotion = result.get("emotion", {})
        inferred_needs = result.get("inferred_needs", [])
        emotion_arc = result.get("emotion_arc", {})
        reply = result.get("response", "👻 I'm here, listening...")
        toolbox_activity = result.get("toolbox_log", "")

    except Exception as e:
        print(f"⚠️ orchestrator.process_message failed: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()

        emotion = {
            "tone": "neutral",
            "labels": ["neutral"],
            "valence": 0.0,
            "arousal": 0.5,
        }
        inferred_needs = []
        emotion_arc = None
        reply = f"👻 (processing error) I still hear you: {user_msg}"
        toolbox_activity = "⚠️ Error during processing"

    messages.append({"role": "assistant", "content": reply})

    # Format emotion arc display
    arc_str = "📊 *Emotion arc will appear here*"
    if isinstance(emotion_arc, dict) and emotion_arc.get("trajectory"):
        direction = emotion_arc.get("direction", "stable")
        summary = emotion_arc.get("summary", "")
        arc_str = f"**📊 Emotion Arc: {direction}**\n\n{summary}"

    # Format needs display
    needs_str = ""
    if inferred_needs:
        needs_list = [
            f"{n['icon']} **{n['label']}** ({int(n['confidence']*100)}%)"
            for n in inferred_needs
        ]
        needs_str = "\n\n**🎯 Detected Needs:**\n" + " | ".join(needs_list)

    # Combine arc and needs
    context_display = arc_str + needs_str

    # Create emotion plot
    emotion_plot = create_emotion_plot(emotion_arc)

    # Debug display for needs
    debug_needs = ""
    if inferred_needs:
        debug_needs = "**🔍 DEBUG - Detected Needs:**\n\n"
        for need in inferred_needs:
            debug_needs += (
                f"- {need['icon']} **{need['label']}** ({need['confidence']:.1%})\n"
            )
            debug_needs += f"  - Need type: `{need['need']}`\n"
            if need.get("contexts"):
                debug_needs += f"  - Contexts: {', '.join(need['contexts'])}\n"
            if need.get("emotions"):
                debug_needs += f"  - Emotions: {', '.join(need['emotions'])}\n"
            debug_needs += "\n"
    else:
        debug_needs = "🔍 DEBUG: No needs detected"

    # Final yield with complete response
    yield messages, messages, "", context_display, emotion_plot, debug_needs, toolbox_activity


with gr.Blocks(title="Ghost Malone") as demo:
    gr.Markdown("## 👻 Ghost Malone\n*I just want to hear you talk.*")

    with gr.Row():
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(type="messages", height=500)
            emotion_arc_md = gr.Markdown("📊 *Emotion arc will appear here*")

        with gr.Column(scale=1):
            emotion_plot = gr.Plot(label="Emotion Trajectory")

    state = gr.State([])

    with gr.Row():
        msg = gr.Textbox(
            placeholder="Tell Ghost Malone what's on your mind...",
            label="Message",
            scale=4,
        )
        clear_btn = gr.Button("🔄 Clear Conversation", scale=1, size="sm")

    # Toolbox activity log
    toolbox_panel = gr.Markdown(
        "🧰 **Toolbox Activity:**\n\nWaiting for first message...",
        label="MCP Tools & Lexicons",
    )

    # Debug panel for needs detection
    debug_panel = gr.Markdown("🔍 DEBUG: No needs detected", label="Needs Debug Info")

    # Intervention controls (SIMPLIFIED for demo)
    gr.Markdown("### 💡 Intervention Controls (for tuning)")
    with gr.Row():
        min_messages = gr.Slider(
            minimum=1,
            maximum=5,
            value=2,
            step=1,
            label="Min Messages",
            info="Wait this many messages before showing interventions",
        )
        min_confidence = gr.Slider(
            minimum=0.5,
            maximum=1.0,
            value=0.70,
            step=0.05,
            label="Min Confidence",
            info="How sure we need to be about the detected need",
        )
        min_arousal = gr.Slider(
            minimum=0.0,
            maximum=1.0,
            value=0.40,
            step=0.05,
            label="Min Arousal",
            info="How intense emotions need to be (0.4 = moderate)",
        )

    msg.submit(
        chat,
        [msg, state, min_messages, min_confidence, min_arousal],
        [chatbot, state, msg, emotion_arc_md, emotion_plot, debug_panel, toolbox_panel],
    )

    def clear_conversation():
        """Reset conversation without restarting MCP servers"""
        return (
            [],  # chatbot
            [],  # state
            "",  # msg
            "📊 *Emotion arc will appear here*",  # emotion_arc_md
            create_emotion_plot({}),  # emotion_plot (empty)
            "🔍 DEBUG: No needs detected",  # debug_panel
            "🧰 **Toolbox Activity:**\n\nWaiting for first message...",  # toolbox_panel
        )

    clear_btn.click(
        clear_conversation,
        None,
        [chatbot, state, msg, emotion_arc_md, emotion_plot, debug_panel, toolbox_panel],
    )

    with gr.Accordion("🧰 MCP Tools (manual)", open=False):
        tool_name = gr.Textbox(label="Tool name (e.g., analyze, remember)")
        tool_args = gr.Textbox(label='Args JSON (e.g., {"text":"hello"})')
        run_btn = gr.Button("Run tool")

        async def run_tool(name: str, args_text: str, messages: list[dict] | None):
            messages = messages or []
            try:
                args = json.loads(args_text) if args_text.strip() else {}
            except json.JSONDecodeError as e:
                messages.append(
                    {"role": "assistant", "content": f"🛠️ Invalid JSON: {e}"}
                )
                return messages, messages
            try:
                out = await _orchestrator.mux.call(name, args)
                messages.append(
                    {"role": "assistant", "content": f"🛠️ `{name}` →\n{out}"}
                )
            except Exception as e:
                messages.append(
                    {"role": "assistant", "content": f"🛠️ `{name}` error → {e}"}
                )
            return messages, messages

        run_btn.click(run_tool, [tool_name, tool_args, state], [chatbot, state])

if __name__ == "__main__":
    print("🚀 starting Ghost Malone server…")
    demo.launch(server_name="127.0.0.1", server_port=7863, share=True)
