"""
Intervention Lexicon: Need-based actionable suggestions
Maps psychological needs to concrete, evidence-based interventions.
SIMPLIFIED VERSION - Focus on architecture, not content
"""

from typing import List, Dict

# Simple intervention strategies for each need
INTERVENTIONS = {
    "autonomy": {
        "label": "Autonomy/Control",
        "icon": "⚖️",
        "strategies": [
            {
                "action": "Set a boundary",
                "prompt": "What would it sound like to say 'no' here?",
                "context": "blocked, powerless, micromanaged",
                "evidence": "Self-Determination Theory",
            },
            {
                "action": "Reclaim one decision",
                "prompt": "What's one choice that's yours to make right now?",
                "context": "dismissed, underutilized",
                "evidence": "Locus of control research",
            },
            {
                "action": "Name what you need",
                "prompt": "If you could ask for one thing to change, what would it be?",
                "context": "powerless, micromanaged",
                "evidence": "Assertiveness training",
            },
        ],
    },
    "connection": {
        "label": "Connection/Belonging",
        "icon": "🗣️",
        "strategies": [
            {
                "action": "Reach out to someone you trust",
                "prompt": "Who's someone who usually gets you?",
                "context": "isolated, rejected, misunderstood",
                "evidence": "Social support research",
            },
            {
                "action": "Share what you're feeling",
                "prompt": "What would you want someone to know about how this feels?",
                "context": "misunderstood, disconnected",
                "evidence": "Emotional disclosure benefits",
            },
            {
                "action": "Remember past connection",
                "prompt": "When did connection feel strong? What made that different?",
                "context": "isolated, rejected",
                "evidence": "Positive psychology",
            },
        ],
    },
    "security": {
        "label": "Security/Clarity",
        "icon": "🛡️",
        "strategies": [
            {
                "action": "Get more information",
                "prompt": "What's one question that would help you feel more grounded?",
                "context": "uncertain, unstable",
                "evidence": "Information-seeking coping",
            },
            {
                "action": "Make a backup plan",
                "prompt": "If the worst happened, what would you do next?",
                "context": "threatened, unstable",
                "evidence": "CBT anxiety reduction",
            },
            {
                "action": "Identify what you can control",
                "prompt": "What's one thing that's yours to decide or influence?",
                "context": "uncertain, threatened",
                "evidence": "Control theory",
            },
        ],
    },
    "rest": {
        "label": "Rest/Boundaries",
        "icon": "🛌",
        "strategies": [
            {
                "action": "Say 'no' to something",
                "prompt": "What's one thing you could decline or delegate?",
                "context": "overwhelmed, overextended",
                "evidence": "Boundary research",
            },
            {
                "action": "Take a real break",
                "prompt": "What would help you actually rest, even for 10 minutes?",
                "context": "exhausted, overwhelmed",
                "evidence": "Recovery research",
            },
            {
                "action": "Lower one expectation",
                "prompt": "What's one thing that could be 'good enough' instead of perfect?",
                "context": "overwhelmed, boundary_violated",
                "evidence": "Perfectionism research",
            },
        ],
    },
    "recognition": {
        "label": "Recognition/Value",
        "icon": "✨",
        "strategies": [
            {
                "action": "Acknowledge yourself",
                "prompt": "What did you actually accomplish today, even if small?",
                "context": "unappreciated, inadequate",
                "evidence": "Self-compassion research",
            },
            {
                "action": "Share your work",
                "prompt": "Who could you show what you've done?",
                "context": "overlooked, unappreciated",
                "evidence": "Recognition at work research",
            },
            {
                "action": "Ask for feedback",
                "prompt": "What would help you know if you're on the right track?",
                "context": "inadequate, overlooked",
                "evidence": "Feedback-seeking behavior",
            },
        ],
    },
}


def get_interventions(
    need_type: str, contexts: List[str] = None, limit: int = 3
) -> List[Dict]:
    """
    Get contextually relevant interventions for a detected need.

    Args:
        need_type: The type of need (autonomy, connection, security, rest, recognition)
        contexts: List of matched contexts (e.g., ["isolated", "rejected"])
        limit: Maximum number of interventions to return

    Returns:
        List of intervention strategies
    """
    if need_type not in INTERVENTIONS:
        return []

    strategies = INTERVENTIONS[need_type]["strategies"]

    # If contexts provided, prioritize matching interventions
    if contexts:
        scored_strategies = []
        for strategy in strategies:
            # Count how many user contexts match this strategy's contexts
            strategy_contexts = set(strategy["context"].split(", "))
            user_contexts = set(contexts)
            matches = len(strategy_contexts & user_contexts)
            scored_strategies.append((matches, strategy))

        # Sort by match count (descending), then take top N
        scored_strategies.sort(key=lambda x: x[0], reverse=True)
        return [s[1] for s in scored_strategies[:limit]]

    # No contexts - return first N strategies
    return strategies[:limit]


def should_show_interventions(
    confidence: float,
    message_count: int,
    emotional_intensity: float = None,
    min_messages: int = 2,
    min_confidence: float = 0.70,
    min_arousal: float = 0.40,
) -> bool:
    """
    SIMPLIFIED for demo: Show interventions when there's a clear need.

    Args:
        confidence: Confidence in the detected need (0-1)
        message_count: Number of messages in conversation
        emotional_intensity: Arousal level (0-1)
        min_messages: Minimum messages (default: 2)
        min_confidence: Minimum confidence (default: 0.70)
        min_arousal: Minimum arousal (default: 0.40)

    Returns:
        True if interventions should be displayed
    """
    # Simple checks - if there's a strong need and emotions, show help
    if message_count < min_messages:
        return False

    if confidence < min_confidence:
        return False

    if emotional_intensity is not None and emotional_intensity < min_arousal:
        return False

    return True


def format_interventions(
    need_type: str,
    interventions: List[Dict],
    confidence: float,
    emotion_arc: Dict = None,
    user_text: str = None,
) -> str:
    """
    Format interventions for display in the UI.

    Args:
        need_type: The detected need type
        interventions: List of intervention strategies
        confidence: Confidence score for the need
        emotion_arc: Optional emotion history for personalization
        user_text: Optional current user message for entity extraction

    Returns:
        Formatted intervention text
    """
    if not interventions:
        return ""

    need_info = INTERVENTIONS.get(need_type, {})
    icon = need_info.get("icon", "💡")
    label = need_info.get("label", need_type)

    # Build the intervention display
    lines = [
        "\n\n---\n",
        f"💡 Based on your need for {icon} {label}:\n",
    ]

    for intervention in interventions:
        lines.append(f"\n• {intervention['action']}")
        lines.append(f"  ↳ {intervention['prompt']}")

    return "".join(lines)
