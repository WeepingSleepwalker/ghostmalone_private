"""
Implicit Needs Detection for Ghost Malone
Maps emotional patterns + context keywords to underlying psychological needs.

STRATEGIC FRAMEWORK:
Based on Self-Determination Theory (Ryan & Deci) + Maslow's Hierarchy

5 Core Needs:
1. AUTONOMY - Control, choice, self-direction
2. CONNECTION - Belonging, relationships, being seen
3. SECURITY - Safety, clarity, predictability
4. REST - Recovery, boundaries, capacity
5. RECOGNITION - Validation, competence, mattering

Context Detection Strategy:
- BARRIERS: What's blocking the need? (can't, won't let, prevented)
- DEFICITS: What's missing? (nobody, nothing, no one)
- THREATS: What's at risk? (unsafe, unstable, unpredictable)
- OVERLOAD: What's too much? (overwhelmed, exhausted, too many)
- DISMISSAL: What's being ignored? (dismissed, invisible, unappreciated)

Constitutional AI Principle: Respects human dignity by treating emotions as signals
of legitimate needs, not surface-level problems.
"""

from typing import List, Dict
import re

# STRATEGIC CONTEXT PATTERNS - organized by psychological dimension
CONTEXT_PATTERNS = {
    # ===== AUTONOMY CONTEXTS =====
    # Barriers to self-direction
    "blocked": r"(can't|won't let|prevented|stopped|blocked|restricted|controlled|controlling me|forced|have to|must|don't give|won't give|not letting|not allowed|doesn't give|pressured to|feel pressured)",
    "powerless": r"(powerless|helpless|trapped|stuck|no choice|no control|out of.{0,15}control|feels.{0,15}out of control|don't have the tools|not much opportunity|no say)",
    "dismissed": r"(ignored|dismissed|disregarded|invalidated|didn't listen|brushed off|shut down|talked over|doesn't consider|don't consider|nobody trusts|don't trust|people ignore|ignore me|cut me off|looked.{0,15}through me|right through me)",
    "underutilized": r"(know i can|i can do|capable of|able to do|qualified|skills|talent|waste|potential|not enough challenge|bored|underused|so boring|below my ability|way below|could do.{0,15}more|living up to)",
    "micromanaged": r"(micromanag|hovering|checking|breathing down|second-guess|don't trust me|checks every|watching every)",
    # ===== CONNECTION CONTEXTS =====
    # Deficits in belonging/relationships
    "isolated": r"(alone|lonely|isolated|by myself|left out|excluded|without me|on my own|don't have anyone|no one to talk|invisible to|no one there|nobody there)",
    "rejected": r"(rejected|abandoned|left me|left behind|they left|ghosted|dumped|unwanted|unloved|won't talk|ignoring|avoiding me|cut off|don't.{0,15}respond|doesn't.{0,15}respond|won't.{0,15}respond|not.{0,15}respond(?:ed|ing)?|hasn't.{0,15}respond|didn't.{0,15}respond|not.{0,15}reply|not.{0,15}repl(?:ied|ying)|not.{0,15}answer(?:ed|ing)?|avoid me|seem to avoid|wasn't invited|didn't invite|unanswered|go unanswered|make excuses|not texting.{0,15}back|won't text)",
    "misunderstood": r"(misunderstood|don't get it|don't understand|not listening|not hearing|missing the point|doesn't.{0,15}listen|won't.{0,15}listen|different language|speaking a different|doesn't.{0,15}hear|misinterpret|nobody.{0,15}understands|nobody.{0,15}knows|nobody.{0,15}interested|doesn't.{0,15}share|doesn't.{0,15}talk|won't.{0,15}talk|doesn't.{0,15}open up)",
    "singled_out": r"(everyone else|everybody else|talks to everyone|except me|only me|just me|do things without|left behind|don't invite|didn't invite|don't call me|leaves me out|not included|don't pass|doesn't pass|won't pass|outsider|feel like.{0,15}outsider|make plans without|plans without including|always the one reaching out|don't include)",
    "disconnected": r"(disconnected|distant|drift|growing apart|not close|lost touch|pulling away|pull away|hard to.{0,15}connection|hard to connect|can't connect)",
    # ===== SECURITY CONTEXTS =====
    # Threats to safety/clarity
    "uncertain": r"(don't know|uncertain|unsure|unclear|confused|no idea|what if|can't tell|ambiguous|what to do|where do i go|what next|what do i do|can't predict|unpredictable|what's going to happen|what will happen|going to happen)",
    "unstable": r"(unstable|unpredictable|chaotic|all over|everything's changing|up in the air|falling apart|like always|never on time|unreliable|keeps changing|constantly changing|shifts again|everything shifts|stays stable|nothing.{0,15}stable|shifting ground|constantly shifting)",
    "threatened": r"(threatened|unsafe|danger|risk|scared|scary|vulnerable|exposed|at risk|pain again|go through that|rot in hell|worried|worrying|something bad|threats|not protected|not secure|don't feel.{0,15}secure)",
    "loss": r"(losing|lost|losing grip|slipping away|falling apart|coming undone)",
    # ===== REST CONTEXTS =====
    # Overload on capacity
    "overwhelmed": r"(overwhelmed|too much|can't handle|drowning|swamped|buried|crowded|crowd|too many people|overstimulat|too much work|coming at me|at me all at once)",
    "exhausted": r"(exhausted|drained|burnt out|can't anymore|running on empty|wiped|spent|depleted|freaking tired|so tired|running on fumes|on fumes|no energy|don't have.{0,15}energy)",
    "overextended": r"(overextended|overstretched|spread thin|doing too much|no time|juggling|can't keep up|keep up with)",
    "boundary_violated": r"(always asking|never stops|can't say no|taking advantage|demanding|intrusive|available 24|expect.{0,15}available|need space|won't give.{0,15}space|boundaries.{0,15}ignored|kept.{0,15}insisting|kept.{0,15}texting|kept.{0,15}calling|i said no|asked for.{0,15}boundaries)",
    # ===== RECOGNITION CONTEXTS =====
    # Dismissal of value/competence
    "unappreciated": r"(unappreciated|taken for granted|not valued|not recognized|invisible|thankless|nobody appreciates|no one appreciates|zero recognition|get.{0,15}recognition|work.{0,15}hard|not appreciated|don't feel appreciated|no.{0,15}recognition|no sense of recognition)",
    "inadequate": r"(not good enough|inadequate|failing|not enough|disappointing|falling short|incompetent|doubt.{0,15}have what it takes|don't feel capable|never enough|nothing.{0,15}enough)",
    "overlooked": r"(overlooked|passed over|ignored|not noticed|nobody notices|no one notices|credit|someone else|didn't acknowledge)",
    "criticized": r"(criticized|judged|attacked|picked apart|nothing right|always wrong|nitpick|point out.{0,15}mistake|only.{0,15}mistake|compared.{0,15}unfavorably|compared to others|offended|offensive|rude|disrespected)",
}

# Needs taxonomy (based on Maslow + Self-Determination Theory)
NEEDS = {
    "autonomy": {
        "label": "Autonomy/Control",
        "icon": "⚖️",
        "description": "Need for self-direction and agency over one's life",
        "interventions": [
            "Set a boundary",
            "Say 'no'",
            "Take back decision-making power",
        ],
    },
    "connection": {
        "label": "Connection/Belonging",
        "icon": "🗣️",
        "description": "Need for meaningful relationships and social bonds",
        "interventions": [
            "Reach out to someone you trust",
            "Share what you're feeling",
            "Ask for support",
        ],
    },
    "security": {
        "label": "Security/Clarity",
        "icon": "🛡️",
        "description": "Need for safety, predictability, and understanding",
        "interventions": [
            "Get more information",
            "Make a plan",
            "Identify what you can control",
        ],
    },
    "rest": {
        "label": "Rest/Boundaries",
        "icon": "🛌",
        "description": "Need for recuperation and limits on demands",
        "interventions": [
            "Take a break",
            "Delegate something",
            "Give yourself permission to rest",
        ],
    },
    "recognition": {
        "label": "Recognition/Validation",
        "icon": "✨",
        "description": "Need to be seen, valued, and acknowledged",
        "interventions": [
            "Acknowledge your own effort",
            "Ask for feedback",
            "Celebrate small wins",
        ],
    },
}

# STRATEGIC NEED INFERENCE RULES
# Organized by primary need, with emotion+context combinations
# Using ONLY the 7 actual detected emotions: happy, sad, angry, anxious, tired, love, fear
NEED_RULES = [
    # ========== AUTONOMY RULES ==========
    # Primary emotion: Anger (blocked goals/control)
    {
        "emotions": ["angry"],
        "contexts": ["blocked", "powerless", "dismissed", "micromanaged"],
        "need": "autonomy",
        "confidence_base": 0.80,
        "reasoning": "Anger signals blocked goals or loss of control",
    },
    {
        "emotions": ["angry", "sad"],
        "contexts": ["powerless", "trapped", "stuck"],
        "need": "autonomy",
        "confidence_base": 0.85,
        "reasoning": "Anger + sadness at powerlessness indicates autonomy deficit",
    },
    {
        "emotions": ["angry"],
        "contexts": ["underutilized", "dismissed"],
        "need": "autonomy",
        "confidence_base": 0.75,
        "reasoning": "Anger at not being allowed to use your capabilities",
    },
    # HIGH PRIORITY: Underutilized should map to autonomy strongly
    {
        "emotions": ["sad", "angry", "anxious", "tired"],
        "contexts": ["underutilized"],
        "need": "autonomy",
        "confidence_base": 0.88,
        "reasoning": "Skills/potential being wasted is autonomy issue",
    },
    {
        "emotions": ["sad"],
        "contexts": ["powerless", "trapped"],
        "need": "autonomy",
        "confidence_base": 0.70,
        "reasoning": "Sadness from lack of control",
    },
    {
        "emotions": ["sad"],
        "contexts": ["blocked", "micromanaged", "dismissed"],
        "need": "autonomy",
        "confidence_base": 0.75,
        "reasoning": "Sadness from being controlled or blocked",
    },
    {
        "emotions": ["tired"],
        "contexts": ["blocked", "powerless", "micromanaged"],
        "need": "autonomy",
        "confidence_base": 0.65,
        "reasoning": "Fatigue from lack of autonomy",
    },
    {
        "emotions": ["anxious"],
        "contexts": ["powerless", "blocked"],
        "need": "autonomy",
        "confidence_base": 0.70,
        "reasoning": "Anxiety from lack of control",
    },
    # ========== CONNECTION RULES ==========
    # Primary emotion: Sadness (relationship deficits)
    # HIGH PRIORITY: "Invisible to people" is connection, not recognition
    {
        "emotions": ["sad", "angry", "anxious"],
        "contexts": ["isolated"],
        "need": "connection",
        "confidence_base": 0.92,
        "reasoning": "Feeling invisible or isolated from people indicates connection deficit",
    },
    {
        "emotions": ["sad"],
        "contexts": ["isolated", "rejected", "misunderstood", "disconnected"],
        "need": "connection",
        "confidence_base": 0.85,
        "reasoning": "Sadness with isolation indicates connection needs",
    },
    {
        "emotions": ["sad"],
        "contexts": ["singled_out"],
        "need": "connection",
        "confidence_base": 0.90,
        "reasoning": "Being excluded from the group",
    },
    # Secondary emotion: Anger (rejection/exclusion)
    {
        "emotions": ["angry"],
        "contexts": ["rejected", "singled_out", "dismissed"],
        "need": "connection",
        "confidence_base": 0.75,
        "reasoning": "Anger from rejection signals need for belonging",
    },
    {
        "emotions": ["angry"],
        "contexts": ["misunderstood", "disconnected"],
        "need": "connection",
        "confidence_base": 0.75,
        "reasoning": "Anger from being misunderstood or disconnected",
    },
    {
        "emotions": ["angry"],
        "contexts": ["isolated"],
        "need": "connection",
        "confidence_base": 0.70,
        "reasoning": "Anger at being isolated",
    },
    {
        "emotions": ["fear"],
        "contexts": ["rejected", "abandoned"],
        "need": "connection",
        "confidence_base": 0.75,
        "reasoning": "Fear of abandonment signals connection needs",
    },
    {
        "emotions": ["anxious"],
        "contexts": ["isolated", "rejected", "misunderstood"],
        "need": "connection",
        "confidence_base": 0.70,
        "reasoning": "Anxiety from social isolation or rejection",
    },
    {
        "emotions": ["tired"],
        "contexts": ["isolated", "disconnected"],
        "need": "connection",
        "confidence_base": 0.60,
        "reasoning": "Fatigue from lack of social connection",
    },
    # ========== SECURITY RULES ==========
    # Primary emotions: Anxiety/Fear (threat/uncertainty)
    {
        "emotions": ["anxious"],
        "contexts": ["uncertain", "unstable", "threatened", "loss"],
        "need": "security",
        "confidence_base": 0.85,
        "reasoning": "Anxiety with uncertainty signals need for clarity/safety",
    },
    {
        "emotions": ["fear"],
        "contexts": ["threatened", "unsafe", "vulnerable"],
        "need": "security",
        "confidence_base": 0.90,
        "reasoning": "Fear indicates immediate security/safety needs",
    },
    {
        "emotions": ["anxious"],
        "contexts": ["uncertain", "unstable"],
        "need": "security",
        "confidence_base": 0.80,
        "reasoning": "Worry about unpredictability or lack of clarity",
    },
    # HIGH PRIORITY: "Can't predict" with blocked is still security (uncertainty primary)
    {
        "emotions": ["anxious", "fear", "sad"],
        "contexts": ["uncertain"],
        "need": "security",
        "confidence_base": 0.94,
        "reasoning": "Uncertainty and unpredictability are core security concerns",
    },
    # HIGH PRIORITY: "Things keep changing" with overextended is security (instability primary)
    {
        "emotions": ["anxious", "tired", "sad"],
        "contexts": ["unstable"],
        "need": "security",
        "confidence_base": 0.94,
        "reasoning": "Constant change and instability are security issues",
    },
    {
        "emotions": ["sad", "anxious"],
        "contexts": ["loss"],
        "need": "security",
        "confidence_base": 0.75,
        "reasoning": "Grief + anxiety about losing stability",
    },
    {
        "emotions": ["angry"],
        "contexts": ["uncertain"],
        "need": "security",
        "confidence_base": 0.65,
        "reasoning": "Anger from lack of clarity",
    },
    {
        "emotions": ["sad"],
        "contexts": ["uncertain", "unstable", "loss"],
        "need": "security",
        "confidence_base": 0.75,
        "reasoning": "Sadness from instability or uncertainty",
    },
    {
        "emotions": ["tired"],
        "contexts": ["unstable", "threatened"],
        "need": "security",
        "confidence_base": 0.65,
        "reasoning": "Exhaustion from constant instability",
    },
    # ========== REST RULES ==========
    # Primary emotion: Tired (capacity overload)
    # HIGH PRIORITY: "Can't say no", "need space", "boundaries ignored" → rest (not autonomy)
    {
        "emotions": ["sad", "angry", "anxious", "tired"],
        "contexts": ["boundary_violated"],
        "need": "rest",
        "confidence_base": 0.95,
        "reasoning": "Boundary violations primarily indicate need for rest/space, not control",
    },
    {
        "emotions": ["tired"],
        "contexts": ["overwhelmed", "exhausted", "overextended"],
        "need": "rest",
        "confidence_base": 0.85,
        "reasoning": "Exhaustion + overwhelm indicates need for rest/boundaries",
    },
    {
        "emotions": ["tired"],
        "contexts": ["exhausted"],
        "need": "rest",
        "confidence_base": 0.95,
        "reasoning": "Explicit exhaustion is clearest rest signal",
    },
    {
        "emotions": ["angry"],
        "contexts": ["exhausted", "overwhelmed"],
        "need": "rest",
        "confidence_base": 0.75,
        "reasoning": "Anger from being exhausted or overwhelmed",
    },
    {
        "emotions": ["anxious", "tired"],
        "contexts": ["overwhelmed", "overextended"],
        "need": "rest",
        "confidence_base": 0.80,
        "reasoning": "Anxiety + tiredness suggests overextension",
    },
    {
        "emotions": ["anxious"],
        "contexts": ["overwhelmed", "crowded"],
        "need": "rest",
        "confidence_base": 0.70,
        "reasoning": "Sensory/social overwhelm signals need for space",
    },
    {
        "emotions": ["angry", "tired"],
        "contexts": ["boundary_violated", "overextended"],
        "need": "rest",
        "confidence_base": 0.75,
        "reasoning": "Anger and fatigue from violated boundaries",
    },
    # HIGH PRIORITY: Boundary violations should map to rest when not autonomy-blocking
    {
        "emotions": ["sad", "angry", "anxious", "tired"],
        "contexts": ["boundary_violated"],
        "need": "rest",
        "confidence_base": 0.82,
        "reasoning": "Boundary violations primarily indicate need for rest/space",
    },
    {
        "emotions": ["sad"],
        "contexts": ["overwhelmed", "exhausted", "overextended"],
        "need": "rest",
        "confidence_base": 0.70,
        "reasoning": "Sadness from depletion and overwhelm",
    },
    {
        "emotions": ["fear"],
        "contexts": ["overwhelmed", "boundary_violated"],
        "need": "rest",
        "confidence_base": 0.65,
        "reasoning": "Fear from being overwhelmed or boundaries violated",
    },
    # ========== RECOGNITION RULES ==========
    # Primary emotions: Sad/Angry (value not seen)
    # HIGH PRIORITY: "Nobody notices/appreciates" is recognition, not connection
    {
        "emotions": ["sad", "angry", "anxious", "tired"],
        "contexts": ["overlooked", "unappreciated"],
        "need": "recognition",
        "confidence_base": 0.90,
        "reasoning": "Being overlooked or unappreciated is primarily about recognition/validation",
    },
    # HIGH PRIORITY: "Don't feel capable" is recognition (inadequate), not autonomy
    {
        "emotions": ["sad", "anxious", "fear"],
        "contexts": ["inadequate"],
        "need": "recognition",
        "confidence_base": 0.92,
        "reasoning": "Self-doubt about capability is core recognition/validation issue",
    },
    {
        "emotions": ["sad"],
        "contexts": ["unappreciated"],
        "need": "recognition",
        "confidence_base": 0.87,
        "reasoning": "Sadness from not being appreciated or valued",
    },
    {
        "emotions": ["sad", "angry"],
        "contexts": ["unappreciated", "inadequate", "overlooked"],
        "need": "recognition",
        "confidence_base": 0.75,
        "reasoning": "Feeling unseen or inadequate signals need for validation",
    },
    {
        "emotions": ["angry"],
        "contexts": ["underutilized", "unappreciated", "overlooked"],
        "need": "recognition",
        "confidence_base": 0.80,
        "reasoning": "Your capabilities aren't being seen or valued",
    },
    {
        "emotions": ["sad"],
        "contexts": ["inadequate"],
        "need": "recognition",
        "confidence_base": 0.85,
        "reasoning": "Self-doubt about competence",
    },
    {
        "emotions": ["sad"],
        "contexts": ["criticized"],
        "need": "recognition",
        "confidence_base": 0.70,
        "reasoning": "Criticism without acknowledgment damages sense of value",
    },
    {
        "emotions": ["angry"],
        "contexts": ["overlooked"],
        "need": "recognition",
        "confidence_base": 0.75,
        "reasoning": "Anger at not being seen or credited",
    },
    {
        "emotions": ["angry"],
        "contexts": ["criticized"],
        "need": "recognition",
        "confidence_base": 0.75,
        "reasoning": "Anger at being criticized, offended, or disrespected",
    },
    {
        "emotions": ["anxious"],
        "contexts": ["inadequate", "criticized"],
        "need": "recognition",
        "confidence_base": 0.75,
        "reasoning": "Anxiety from self-doubt or criticism",
    },
    {
        "emotions": ["tired"],
        "contexts": ["unappreciated", "overlooked"],
        "need": "recognition",
        "confidence_base": 0.65,
        "reasoning": "Fatigue from lack of appreciation",
    },
    {
        "emotions": ["fear"],
        "contexts": ["inadequate", "criticized"],
        "need": "recognition",
        "confidence_base": 0.70,
        "reasoning": "Fear of failure or judgment",
    },
]


def detect_context(text: str) -> Dict[str, bool]:
    """Detect which situational contexts are present in the text."""
    text_lower = text.lower()
    detected = {}

    for context_name, pattern in CONTEXT_PATTERNS.items():
        detected[context_name] = bool(re.search(pattern, text_lower))

    return detected


def infer_needs(
    emotion_labels: List[str], text: str, valence: float = 0.0, arousal: float = 0.5
) -> List[Dict]:
    """
    Infer psychological needs from emotions + text context.

    Args:
        emotion_labels: Primary emotions detected (e.g., ["angry", "sad"])
        text: User's message text
        valence: Emotional valence (-1 to 1)
        arousal: Emotional arousal (0 to 1)

    Returns:
        List of inferred needs with confidence scores:
        [
            {
                "need": "autonomy",
                "label": "Autonomy/Control",
                "icon": "⚖️",
                "confidence": 0.82,
                "reasoning": "Anger often signals blocked goals...",
                "interventions": ["Set a boundary", ...]
            },
            ...
        ]
    """
    # Detect situational contexts
    contexts = detect_context(text)
    active_contexts = [ctx for ctx, present in contexts.items() if present]

    # Match rules
    inferred = []
    seen_needs = set()

    for rule in NEED_RULES:
        # Check if emotions match (any overlap)
        emotion_match = any(emo in emotion_labels for emo in rule["emotions"])

        # Check if contexts match (any overlap)
        context_match = any(ctx in active_contexts for ctx in rule["contexts"])

        if emotion_match and context_match:
            need_key = rule["need"]

            # Avoid duplicates
            if need_key in seen_needs:
                continue
            seen_needs.add(need_key)

            # Calculate confidence
            # Base confidence from rule
            confidence = rule["confidence_base"]

            # Boost if multiple emotions match
            emotion_overlap = sum(
                1 for emo in rule["emotions"] if emo in emotion_labels
            )
            if emotion_overlap > 1:
                confidence += 0.05

            # Boost if multiple contexts match
            context_overlap = sum(
                1 for ctx in rule["contexts"] if ctx in active_contexts
            )
            if context_overlap > 1:
                confidence += 0.05

            # Adjust by emotional intensity (valence magnitude + arousal)
            intensity = (abs(valence) + arousal) / 2.0
            if intensity > 0.6:
                confidence += 0.05

            confidence = min(1.0, confidence)  # Cap at 1.0

            need_info = NEEDS[need_key]
            inferred.append(
                {
                    "need": need_key,
                    "label": need_info["label"],
                    "icon": need_info["icon"],
                    "confidence": round(confidence, 2),
                    "reasoning": rule["reasoning"],
                    "description": need_info["description"],
                    "interventions": need_info["interventions"],
                    "matched_contexts": [
                        ctx for ctx in rule["contexts"] if ctx in active_contexts
                    ],
                    "matched_emotions": [
                        emo for emo in rule["emotions"] if emo in emotion_labels
                    ],
                }
            )

    # Sort by confidence (highest first)
    inferred.sort(key=lambda x: x["confidence"], reverse=True)

    return inferred


def format_needs_summary(needs: List[Dict], max_display: int = 2) -> str:
    """
    Format needs as a human-readable summary.

    Args:
        needs: List of inferred needs from infer_needs()
        max_display: Maximum number of needs to show

    Returns:
        Formatted string like:
        "⚖️ Autonomy/Control (85%) | 🗣️ Connection/Belonging (72%)"
    """
    if not needs:
        return "No specific needs detected"

    top_needs = needs[:max_display]
    parts = [
        f"{n['icon']} {n['label']} ({int(n['confidence']*100)}%)" for n in top_needs
    ]
    return " | ".join(parts)


# Example usage for testing
if __name__ == "__main__":
    # Test case 1: Autonomy need
    test1 = infer_needs(
        emotion_labels=["angry"],
        text="my boss won't let me make my own decisions",
        valence=-0.5,
        arousal=0.7,
    )
    print("Test 1 (Autonomy):")
    print(format_needs_summary(test1))
    print(test1[0] if test1 else "No needs detected")
    print()

    # Test case 2: Connection need
    test2 = infer_needs(
        emotion_labels=["sad"],
        text="i feel so alone, nobody understands what i'm going through",
        valence=-0.6,
        arousal=0.4,
    )
    print("Test 2 (Connection):")
    print(format_needs_summary(test2))
    print(test2[0] if test2 else "No needs detected")
    print()

    # Test case 3: Rest need
    test3 = infer_needs(
        emotion_labels=["tired", "anxious"],
        text="i'm so overwhelmed, there's just too much to handle",
        valence=-0.4,
        arousal=0.6,
    )
    print("Test 3 (Rest):")
    print(format_needs_summary(test3))
    print(test3[0] if test3 else "No needs detected")
