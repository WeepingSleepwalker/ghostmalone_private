# utils/orchestrator.py
# Coordinates emotion, memory, and reflection servers together
from typing import Dict, Any, Optional
import asyncio
import time
from utils.mcp_client import MCPMux
from utils.needs_lexicon import infer_needs
from utils.intervention_lexicon import (
    get_interventions,
    should_show_interventions,
    format_interventions,
)


class GhostMaloneMux:
    """Orchestrator for Ghost Malone's three servers: emotion, memory, reflection"""

    def __init__(self):
        self.mux = MCPMux()
        self.initialized = False

    async def initialize(self):
        """Connect to all three MCP servers"""
        if self.initialized:
            return

        # Connect to emotion server
        await self.mux.connect_stdio(
            "emotion", "python", args=["servers/emotion_server.py"]
        )

        # Connect to memory server
        await self.mux.connect_stdio(
            "memory", "python", args=["servers/memory_server.py"]
        )

        # Connect to reflection server
        await self.mux.connect_stdio(
            "reflection", "python", args=["servers/reflection_server.py"]
        )

        self.initialized = True

    async def process_message(
        self,
        user_text: str,
        conversation_context: list[dict] | None = None,
        user_id: str = "user_001",
        intervention_thresholds: dict | None = None,
    ) -> dict:
        """
        Process a user message through the full pipeline:
        1. Emotion analysis
        2. Needs inference
        3. Memory operations (parallel)
        4. Reflection generation
        5. Intervention generation (if thresholds met)

        Args:
            user_text: The user's message
            conversation_context: Previous messages
            user_id: User identifier
            intervention_thresholds: Optional dict with min_messages, min_confidence, min_arousal

        Returns dict with:
            "user_text": str,
            "emotion": dict (emotion analysis),
            "inferred_needs": list (psychological needs detected),
            "emotion_arc": dict (trajectory),
            "response": str (assistant reply),
            "tone": str
        }
        """
        if not self.initialized:
            await self.initialize()

        # Extract intervention thresholds (SIMPLIFIED defaults for demo)
        thresholds = intervention_thresholds or {}
        min_messages = thresholds.get("min_messages", 2)  # Just need one exchange
        min_confidence = thresholds.get("min_confidence", 0.70)  # Lower bar
        min_arousal = thresholds.get("min_arousal", 0.40)  # Catch more cases

        start_time = time.time()

        # Initialize toolbox log
        toolbox_log = []

        # Step 1: Analyze emotion
        t1 = time.time()
        toolbox_log.append(
            "🔧 **emotion_server.analyze()** - Detecting emotions from text"
        )
        emotion_data = await self.mux.call(
            "analyze", {"text": user_text, "user_id": user_id}
        )
        elapsed = (time.time() - t1) * 1000
        print(f"⏱️  Emotion analysis: {elapsed:.0f}ms")

        # Parse emotion response (it comes as JSON string from MCP)
        if isinstance(emotion_data, str):
            import json

            emotion_dict = json.loads(emotion_data)
        else:
            emotion_dict = emotion_data

        toolbox_log.append(
            f"   ✅ Found: {emotion_dict.get('labels', [])} ({elapsed:.0f}ms)"
        )

        # Step 2: Infer psychological needs from emotion + context (fast, <100ms)
        t2 = time.time()
        toolbox_log.append(
            "\n📖 **needs_lexicon.infer_needs()** - Detecting psychological needs"
        )
        emotion_labels = emotion_dict.get("labels", [])
        valence = emotion_dict.get("valence", 0.0)
        arousal = emotion_dict.get("arousal", 0.0)
        inferred_needs = infer_needs(emotion_labels, user_text, valence, arousal)
        elapsed = (time.time() - t2) * 1000
        print(f"⏱️  Needs inference: {elapsed:.0f}ms")

        if inferred_needs:
            need_summary = ", ".join(
                [f"{n['label']} ({n['confidence']:.0%})" for n in inferred_needs]
            )
            toolbox_log.append(f"   ✅ Detected: {need_summary} ({elapsed:.0f}ms)")
        else:
            toolbox_log.append(f"   ℹ️  No strong needs detected ({elapsed:.0f}ms)")

        # Debug: Print detected needs
        print(f"🎯 Inferred needs: {inferred_needs}")
        if inferred_needs:
            for need in inferred_needs:
                print(f"   - {need['icon']} {need['label']} ({need['confidence']:.0%})")

        # Step 3 & 4: Parallelize memory operations (they don't depend on each other)
        t3 = time.time()
        toolbox_log.append("\n🧠 **memory_server** - Parallel operations:")
        toolbox_log.append("   📥 get_emotion_arc() - Retrieving emotion history")
        toolbox_log.append("   💾 remember_event() - Storing current message")

        emotion_arc_task = self.mux.call("get_emotion_arc", {"k": 10})

        event = {
            "text": user_text,
            "emotion": emotion_dict,
            "role": "user",
            "user_id": user_id,
        }
        remember_task = self.mux.call("remember_event", {"event": event})

        # Run both memory operations in parallel
        emotion_arc, _ = await asyncio.gather(emotion_arc_task, remember_task)
        elapsed = (time.time() - t3) * 1000
        print(f"⏱️  Memory operations (parallel): {elapsed:.0f}ms")
        toolbox_log.append(f"   ✅ Completed ({elapsed:.0f}ms)")

        if isinstance(emotion_arc, str):
            import json

            emotion_arc = json.loads(emotion_arc)

        # Step 5: Generate reflection using emotion + arc
        t4 = time.time()
        toolbox_log.append(
            "\n🤖 **reflection_server.generate()** - Claude response generation"
        )
        tone = emotion_dict.get("tone", "neutral")
        reflection_response = await self.mux.call(
            "generate",
            {
                "text": user_text,
                "context": conversation_context,
                "tone": tone,
                "emotion_arc": emotion_arc,
            },
        )
        elapsed = (time.time() - t4) * 1000
        print(f"⏱️  Reflection generation (Claude): {elapsed:.0f}ms")
        toolbox_log.append(f"   ✅ Response generated ({elapsed:.0f}ms)")

        if isinstance(reflection_response, str):
            import json

            try:
                response_dict = json.loads(reflection_response)
                reply = response_dict.get("reply", reflection_response)
            except Exception:
                reply = reflection_response
        else:
            reply = str(reflection_response)

        # Step 6: Generate interventions (SIMPLIFIED FOR DEMO)
        toolbox_log.append(
            "\n💡 **intervention_lexicon** - Checking intervention criteria"
        )
        message_count = len(conversation_context) + 1 if conversation_context else 1
        arousal = emotion_dict.get("arousal", 0.5)

        intervention_text = ""

        # Simple rule: If we detected a need, check if we should show interventions
        if inferred_needs and should_show_interventions(
            confidence=inferred_needs[0]["confidence"],
            message_count=message_count,
            emotional_intensity=arousal,
            min_messages=min_messages,
            min_confidence=min_confidence,
            min_arousal=min_arousal,
        ):
            toolbox_log.append(
                f"   ✅ Thresholds met (msg≥{min_messages}, conf≥{min_confidence:.0%}, arousal≥{min_arousal:.1f})"
            )
            need_type = inferred_needs[0]["need"]
            contexts = inferred_needs[0].get("matched_contexts", [])
            interventions = get_interventions(need_type, contexts, limit=3)

            if interventions:
                toolbox_log.append(
                    f"   📋 get_interventions() - Retrieved {len(interventions)} strategies for {need_type}"
                )
                intervention_text = format_interventions(
                    need_type,
                    interventions,
                    inferred_needs[0]["confidence"],
                    emotion_arc=emotion_arc,
                    user_text=user_text,
                )
                print(f"💡 Showing {len(interventions)} interventions for {need_type}")
        else:
            reasons = []
            if not inferred_needs:
                reasons.append("no needs detected")
            else:
                if message_count < min_messages:
                    reasons.append(f"msg count {message_count}<{min_messages}")
                if inferred_needs[0]["confidence"] < min_confidence:
                    reasons.append(
                        f"confidence {inferred_needs[0]['confidence']:.0%}<{min_confidence:.0%}"
                    )
                if arousal < min_arousal:
                    reasons.append(f"arousal {arousal:.1f}<{min_arousal:.1f}")
            toolbox_log.append(f"   ℹ️  No interventions ({', '.join(reasons)})")

        # Combine empathetic response + interventions
        full_response = reply + intervention_text

        total_time = time.time() - start_time
        print(f"⏱️  TOTAL pipeline time: {total_time*1000:.0f}ms ({total_time:.1f}s)")
        toolbox_log.append(f"\n⏱️  **Total pipeline:** {total_time*1000:.0f}ms")

        # Format toolbox log
        toolbox_log_str = "🧰 **Toolbox Activity:**\n\n" + "\n".join(toolbox_log)

        return {
            "user_text": user_text,
            "emotion": emotion_dict,
            "inferred_needs": inferred_needs,
            "emotion_arc": emotion_arc,
            "response": full_response,
            "tone": tone,
            "has_interventions": bool(intervention_text),
            "toolbox_log": toolbox_log_str,
        }

    async def close(self):
        """Close all server connections"""
        await self.mux.close()


# Global instance
_orchestrator = None


async def get_orchestrator() -> GhostMaloneMux:
    """Get or create the global orchestrator"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = GhostMaloneMux()
        await _orchestrator.initialize()
    return _orchestrator
