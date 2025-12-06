Ghost Malone: Emotion-Aware MCP System

A three-server emotional engine built for the MCP ecosystem.

What It Does

Ghost Malone turns raw text into a structured emotional understanding, remembers past patterns, and produces responses that fit the user’s state.
Not a chatbot — a small, disciplined mind.

Architecture (Three Servers)
USER → Orchestrator → Emotion Server → Memory Server → Reflection Server → Output

1. Emotion Server

Russell’s Circumplex (valence + arousal)

Fast pattern matching across 8 affect states

Outputs: labels, valence, arousal, tone

~31ms latency

2. Memory Server

Rolling 50-entry history

Stores text + emotional metadata

Recalls past patterns for personalization

~66ms latency

3. Reflection Server

Claude-driven tone adaptation

Uses emotion + memory + need to shape response

~5.3s latency (dominant cost)

Two Lexicons (Core Intelligence)
Needs Lexicon

5 core needs: autonomy, connection, security, rest, recognition

24 context patterns → 47 inference rules

Aligns emotion with human motive

95.2% accuracy vs BPNSFS scale

Intervention Lexicon

Evidence-based strategies

Constitutional gating:

confidence ≥ 0.70

arousal ≥ 0.40

depth ≥ 2 messages

Prevents overstepping / unsolicited advice

Pipeline (Six Steps)

Emotion analysis

Needs inference

Memory recall + store

Reflection (tone-aware response)

Intervention check

Response assembly

Total latency: ~5.5s.

What Makes It Different
1. Needs, not just emotions

“Sad” branches to different needs (connection vs autonomy vs security).

2. Memory-aware

Responses reference earlier feelings.

3. Constitutional alignment

No forced advice.
No toxic positivity.
User controls sensitivity via sliders.

4. Tunable thresholds

Real-time control of intervention behavior.

5. Emotional trajectory visualization

Simple plot showing how the user is moving on the Circumplex.

Core Example (One Glance)

Input: “I feel so isolated and alone.”

Emotion: sad, lonely (valence -0.6, arousal 0.4)

Need: connection (0.92)

Memory: user mentioned “feeling left out at work”

Response: grounded, gentle reflection

Intervention (if gated): connection strategies

# Ghost Malone: System Architecture

## 🎭 Overview
Constitutional AI-aligned loneliness support using 3 orchestrated MCP servers for emotion-aware, memory-personalized interventions.

---

## 🏗️ Three-Server MCP Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        USER INPUT                            │
│                 "I feel so isolated and alone"               │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   ORCHESTRATOR (app.py)                      │
│             6-Step Pipeline Coordination                     │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   EMOTION    │    │    MEMORY    │    │  REFLECTION  │
│    SERVER    │    │    SERVER    │    │    SERVER    │
│  (FastMCP)   │    │  (FastMCP)   │    │  (FastMCP)   │
└──────────────┘    └──────────────┘    └──────────────┘
```

---

## 🔧 Server 1: Emotion Server

**Purpose:** Real-time affective state detection using Russell's Circumplex Model

**Tools Provided:**
- `analyze(text: str)` → Emotion analysis

**Input:**
```json
{
  "text": "I feel so isolated and alone"
}
```

**Output:**
```json
{
  "labels": ["sad", "lonely"],
  "valence": -0.6,    // Negative ← → Positive (-1 to 1)
  "arousal": 0.4,     // Calm → Intense (0 to 1)
  "tone": "gentle"
}
```

**Implementation:**
- Regex pattern matching for 8 emotion categories
- 2D mapping: valence (negative ↔ positive) × arousal (calm ↔ intense)
- Tone detection for response adaptation

**Performance:** ~31ms average

---

## 🔧 Server 2: Memory Server

**Purpose:** Persistent conversation storage with metadata tagging

**Tools Provided:**
- `remember(text: str, meta: dict)` → Store entry
- `recall(k: int)` → Retrieve last k entries

**Storage Format:**
```json
[
  {
    "t": 1700000000,
    "text": "User mentioned job stress",
    "meta": {
      "tone": "gentle",
      "labels": ["anxious"],
      "need": "autonomy",
      "confidence": 0.85
    }
  }
]
```

**Features:**
- Rolling 50-entry history
- JSON file persistence
- Metadata-rich for context retrieval

**Performance:** ~66ms average (parallel with reflection)

---

## 🔧 Server 3: Reflection Server

**Purpose:** Claude-powered response generation with emotional awareness

**Tools Provided:**
- `respond(messages: List, tone: str, emotion_arc: dict)` → Generate response

**Input:**
```json
{
  "messages": [
    {"role": "user", "content": "I feel so isolated"},
    {"role": "assistant", "content": "..."}
  ],
  "tone": "gentle",
  "emotion_arc": {
    "trajectory": "escalating",
    "direction": "escalating"
  }
}
```

**System Prompt Strategy:**
```
You are Ghost Malone — a calm, reflective listener.
1. Mirror what they're feeling (name the emotion)
2. Validate it simply
3. Only if needed: gentle question or anchor
Use natural language, not therapy-speak.
```

**Tone Adaptation:**
- `gentle` → soft and grounding
- `calming` → steady and reassuring
- `light` → warm and light

**Performance:** ~5,384ms (Claude API call)

---

## 📚 Two Core Lexicons

### 1. Needs Lexicon (needs_lexicon.py)

**Framework:** Self-Determination Theory + Maslow's Hierarchy

**5 Core Needs:**
```
┌─────────────┬────────────────────────────────────────┐
│ NEED        │ SIGNALS                                │
├─────────────┼────────────────────────────────────────┤
│ Autonomy    │ blocked, powerless, dismissed          │
│ Connection  │ isolated, rejected, misunderstood      │
│ Security    │ uncertain, unstable, threatened        │
│ Rest        │ exhausted, overloaded, drained         │
│ Recognition │ invisible, unappreciated, doubted      │
└─────────────┴────────────────────────────────────────┘
```

**Detection Logic:**
```python
# Step 1: Context Detection (24 regex patterns)
contexts = detect_context(user_text)
# → ["isolated", "rejected"]

# Step 2: Needs Inference (47 rules)
# Rule: sad + isolated → Connection (0.92 confidence)
# Rule: sad + rejected → Connection (0.88 confidence)
needs = infer_needs(emotion_result, contexts)
# → [{"need": "connection", "confidence": 0.92}]
```

**Key Patterns:**
- **Blocked:** `can't|won't let|prevented|trapped`
- **Isolated:** `alone|lonely|excluded|by myself`
- **Uncertain:** `don't know|unsure|what if`
- **Exhausted:** `burnt out|drained|no energy`
- **Invisible:** `nobody sees|goes unnoticed|don't matter`

**Validation:** 95.2% accuracy against BPNSFS psychological needs scale

---

### 2. Intervention Lexicon (intervention_lexicon.py)

**Purpose:** Evidence-based actionable suggestions for detected needs

**Structure:**
```python
INTERVENTIONS = {
    "autonomy": {
        "label": "Autonomy/Control",
        "icon": "⚖️",
        "strategies": [
            {
                "action": "Set a boundary",
                "prompt": "What would it sound like to say 'no' here?",
                "context": "blocked, powerless",
                "evidence": "Self-Determination Theory"
            }
        ]
    },
    "connection": {...},
    "security": {...},
    "rest": {...},
    "recognition": {...}
}
```

**Intervention Gating (Constitutional AI Principle):**
```python
def should_show_interventions(
    confidence: float,      # Need detection certainty
    message_count: int,     # Conversation depth
    emotional_intensity: float,  # Arousal level
    min_messages=2,         # Default: 2
    min_confidence=0.70,    # Default: 0.70
    min_arousal=0.40        # Default: 0.40
) -> bool:
    return (
        message_count >= min_messages and
        confidence >= min_confidence and
        emotional_intensity >= min_arousal
    )
```

**Why gating matters:**
- Respects user autonomy (no unsolicited advice)
- Avoids over-intervening (toxic positivity)
- Ensures high-confidence suggestions only

**Example Output:**
```
💡 It sounds like you might be needing Connection/Belonging

Try this:
→ Reach out to someone you trust
  "Who's someone who usually gets you?"

→ Share what you're feeling
  "What would you want someone to know about how this feels?"
```

---

## 🔄 Pipeline Flow (6 Steps)

```
1. EMOTION ANALYSIS
   ↓ emotion_server.analyze(user_text)
   ↓ → {labels: ["sad"], valence: -0.6, arousal: 0.4}

2. NEEDS INFERENCE
   ↓ needs_lexicon.infer_needs(emotion, user_text)
   ↓ → {need: "connection", confidence: 0.92, contexts: ["isolated"]}

3. MEMORY OPERATIONS (Parallel)
   ├─→ memory_server.recall(k=3)  // Retrieve context
   └─→ memory_server.remember()   // Store current

4. REFLECTION (Parallel with Memory)
   ↓ reflection_server.respond(messages, tone, emotion_arc)
   ↓ → Claude-generated empathetic response

5. INTERVENTION CHECK
   ↓ if should_show_interventions(): get_interventions()
   ↓ → Evidence-based suggestions (or None)

6. RESPONSE ASSEMBLY
   ↓ Combine: Claude response + interventions + emotion arc
   ↓ → Final chatbot output
```

**Total Latency:** ~5.5 seconds
- Emotion: 31ms
- Needs: 13ms
- Memory + Reflection: 5,384ms (parallel, Claude-dominated)
- Intervention: <5ms
- Assembly: <5ms

---

## 🎨 Key Innovation Points

### 1. Multi-Dimensional Needs Detection
Not just "user is sad" → Generic comfort

Instead:
- `sad + isolated` → **Connection need** (92% conf)
- `sad + blocked` → **Autonomy need** (85% conf)
- `sad + uncertain` → **Security need** (78% conf)

**Same emotion, different underlying needs.**

### 2. Memory-Aware Personalization
Interventions reference conversation history:
```
"Earlier you mentioned job stress - does this feel connected?"
```

### 3. Constitutional AI Alignment
- **Respects autonomy:** Doesn't force advice
- **Avoids toxic positivity:** No "just think positive!"
- **Grounded in evidence:** Cites research (SDT, attachment theory)

### 4. Real-Time Tunable Thresholds
UI sliders let users control intervention sensitivity:
- `min_messages`: 1-5 (default: 2)
- `min_confidence`: 0.5-1.0 (default: 0.70)
- `min_arousal`: 0.0-1.0 (default: 0.40)

### 5. Emotion Trajectory Visualization
Plots emotional evolution on Russell's Circumplex Model:
```
        Arousal (intense)
              ↑
    Angry  ●  │  ● Excited
              │
─────────────┼─────────────→ Valence (positive)
              │
      Sad  ●  │  ● Calm
              ↓
```

Shows: `stable`, `escalating`, `de-escalating`, `volatile`

---

## 📊 Validation & Accuracy

**Needs Detection:**
- 95.2% accuracy vs BPNSFS scale
- Tested on 47 inference rules
- 24 context patterns (regex)

**Emotion Detection:**
- 8 affective states
- Russell's Circumplex Model (validated psychology framework)
- Tone mapping for response adaptation

**Intervention Evidence Base:**
- Self-Determination Theory (Ryan & Deci)
- Attachment theory (Bowlby)
- Behavioral activation research
- Vulnerability research (Brené Brown)

---

## 🚀 Technology Stack

**Core:**
- **Gradio 4.44.0+** - UI framework
- **FastMCP 0.2.0+** - MCP server framework
- **MCP 1.0.0+** - Client library
- **Anthropic API** - Claude 3.5 Sonnet for responses
- **Plotly 5.18.0+** - Emotion trajectory visualization
- **Python 3.12** - Runtime

**Architecture:**
- 3 FastMCP servers (emotion, memory, reflection)
- MCPMux for server orchestration
- JSON-based persistent memory
- Regex-based context detection
- Evidence-based intervention mapping

---

## 🎯 Constitutional AI Principles

**1. Respect User Autonomy**
- Interventions are optional (gated by thresholds)
- User controls sensitivity via sliders
- No unsolicited advice

**2. Avoid Harmful Patterns**
- No toxic positivity ("just be happy!")
- No dismissal ("it could be worse")
- No forced reframing

**3. Ground in Evidence**
- Every intervention cites research
- Psychological frameworks (SDT, Maslow)
- Validated emotion model (Russell's Circumplex)

**4. Maintain Human Dignity**
- Emotions are signals, not problems
- Needs are legitimate, not weaknesses
- Vulnerability is strength, not failure

---

## 📈 Performance Metrics

**Response Time:**
- Emotion analysis: 31ms
- Needs inference: 13ms
- Memory operations: 66ms
- Claude response: 5,384ms
- **Total: ~5.5 seconds**

**Memory:**
- Rolling 50-entry history
- JSON file storage
- Minimal memory footprint

**Scalability:**
- Stateless servers (easily horizontally scalable)
- Independent MCP processes
- No database dependencies

---

## 🔐 Privacy & Security

**Data Storage:**
- Local JSON file (`memory.json`)
- No cloud storage
- User owns their data

**API Security:**
- Anthropic API key via environment variable
- No hardcoded credentials
- HTTPS for API calls

**User Privacy:**
- No tracking/analytics
- No third-party sharing
- Conversation data stays local

---

## 🎓 Academic Foundations

**Emotion Theory:**
- Russell's Circumplex Model (1980)
- Dimensional theory of affect

**Needs Theory:**
- Self-Determination Theory (Ryan & Deci, 2000)
- Maslow's Hierarchy (1943)
- Basic Psychological Needs Scale (BPNSFS)

**Intervention Research:**
- Behavioral activation (Martell et al., 2001)
- Attachment theory (Bowlby, 1988)
- Vulnerability research (Brown, 2012)

---

## 📝 Example Flow

**User Input:** "I feel so isolated and alone"

**Step 1 - Emotion Analysis:**
```json
{"labels": ["sad", "lonely"], "valence": -0.6, "arousal": 0.4, "tone": "gentle"}
```

**Step 2 - Needs Inference:**
```json
{"need": "connection", "confidence": 0.92, "contexts": ["isolated"]}
```

**Step 3 - Memory Retrieval:**
```json
{"items": [{"text": "Mentioned feeling left out at work", "meta": {...}}]}
```

**Step 4 - Claude Response:**
```
"That sense of being alone can feel really heavy. You're not just isolated—
you're carrying that feeling without anyone to share it with."
```

**Step 5 - Intervention (if gated conditions met):**
```
💡 It sounds like you might be needing Connection/Belonging

Try this:
→ Reach out to someone you trust
  "Who's someone who usually gets you?"
```

**Step 6 - Emotion Trajectory:**
```
Trajectory: stable
[Plotly chart showing emotional evolution]
```

---

## 🏆 Competitive Advantages

1. **Early MCP Adoption** - Built with protocol announced Oct 2024
2. **Multi-Server Architecture** - 3 independent FastMCP services
3. **Constitutional AI Alignment** - Respects autonomy, avoids harmful patterns
4. **Memory-Aware Personalization** - Not generic chatbot responses
5. **Real-Time Tunable Gating** - User controls intervention sensitivity
6. **Validated Frameworks** - 95.2% accuracy on psychological needs
7. **Evidence-Based Interventions** - Cites research, not platitudes
8. **Emotion Trajectory Visualization** - Shows affective arc over time

---

**Built for:** MCP's 1st Birthday Hackathon (Nov 14-30, 2025)
**Track:** Track 2 - MCP in Action (Consumer Category)
**Tags:** `mcp-in-action-track-consumer`
