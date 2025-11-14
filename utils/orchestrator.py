# utils/orchestrator.py
# Coordinates emotion, memory, and reflection servers together
from typing import Dict, Any, Optional
from utils.mcp_client import MCPMux

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
        await self.mux.connect_stdio("emotion", "python", args=["servers/emotion_server.py"])

        # Connect to memory server
        await self.mux.connect_stdio("memory", "python", args=["servers/memory_server.py"])

        # Connect to reflection server
        await self.mux.connect_stdio("reflection", "python", args=["servers/reflection_server.py"])

        self.initialized = True

    async def process_message(
        self,
        user_text: str,
        conversation_context: Optional[list] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Full pipeline: emotion → memory → reflection

        Returns: {
            "user_text": str,
            "emotion": dict (emotion analysis),
            "emotion_arc": dict (trajectory),
            "response": str (assistant reply),
            "tone": str
        }
        """
        if not self.initialized:
            await self.initialize()

        # Step 1: Analyze emotion
        emotion_data = await self.mux.call("analyze", {
            "text": user_text,
            "user_id": user_id
        })

        # Parse emotion response (it comes as JSON string from MCP)
        if isinstance(emotion_data, str):
            import json
            emotion_dict = json.loads(emotion_data)
        else:
            emotion_dict = emotion_data

        # Step 2: Get emotion arc from memory
        emotion_arc = await self.mux.call("get_emotion_arc", {"k": 10})
        if isinstance(emotion_arc, str):
            import json
            emotion_arc = json.loads(emotion_arc)

        # Step 3: Remember this event
        event = {
            "text": user_text,
            "emotion": emotion_dict,
            "role": "user",
            "user_id": user_id
        }
        await self.mux.call("remember_event", {"event": event})

        # Step 4: Generate reflection using emotion + arc
        tone = emotion_dict.get("tone", "neutral")
        reflection_response = await self.mux.call("generate", {
            "text": user_text,
            "context": conversation_context,
            "tone": tone,
            "emotion_arc": emotion_arc
        })

        if isinstance(reflection_response, str):
            import json
            try:
                response_dict = json.loads(reflection_response)
                reply = response_dict.get("reply", reflection_response)
            except Exception:
                reply = reflection_response
        else:
            reply = str(reflection_response)

        return {
            "user_text": user_text,
            "emotion": emotion_dict,
            "emotion_arc": emotion_arc,
            "response": reply,
            "tone": tone
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
