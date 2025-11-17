# 🧠 Strategic Needs Detection Framework

## Theoretical Foundation

Based on **Self-Determination Theory** (Ryan & Deci, 2000) + **Maslow's Hierarchy of Needs**

### 5 Core Psychological Needs

1. **⚖️ AUTONOMY** - Control, choice, self-direction
2. **🗣️ CONNECTION** - Belonging, relationships, being seen
3. **🛡️ SECURITY** - Safety, clarity, predictability
4. **🛌 REST** - Recovery, boundaries, capacity limits
5. **✨ RECOGNITION** - Validation, competence, mattering

---

## Detection Strategy: 5 Context Dimensions

### 1. BARRIERS (→ Autonomy)
**What's blocking the need?**
- Keywords: `can't`, `won't let`, `prevented`, `blocked`, `restricted`, `controlled`, `forced`
- Example: "my boss won't let me make decisions"
- Signal: Loss of agency/control

### 2. DEFICITS (→ Connection)
**What's missing?**
- Keywords: `nobody`, `no one`, `alone`, `lonely`, `isolated`, `left out`, `excluded`, `without me`
- Example: "my friends do things without me"
- Signal: Relationship gaps/exclusion

### 3. THREATS (→ Security)
**What's at risk?**
- Keywords: `unsafe`, `unstable`, `unpredictable`, `uncertain`, `don't know`, `what if`, `losing`
- Example: "everything's so unpredictable"
- Signal: Loss of safety/clarity

### 4. OVERLOAD (→ Rest)
**What's too much?**
- Keywords: `overwhelmed`, `exhausted`, `too much`, `can't handle`, `burnt out`, `crowded`
- Example: "I'm so overwhelmed and can't say no"
- Signal: Capacity exceeded

### 5. DISMISSAL (→ Recognition)
**What's being ignored?**
- Keywords: `unappreciated`, `invisible`, `taken for granted`, `overlooked`, `not good enough`, `inadequate`
- Example: "they don't give me projects I know I can do"
- Signal: Value/competence not seen

---

## Technical Implementation Discussion

### Current Approach: Regex Pattern Matching

**Status:** Initial implementation complete, ~70% accuracy on test cases

**Architecture:**
- 24 context patterns organized by need dimension
- 24 inference rules (emotion + context → need)
- Confidence scoring with boosting
- Pure Python, <100ms latency

**Advantages:**
- ✅ **Fast:** <100ms execution time
- ✅ **Interpretable:** Can show exactly what matched (Constitutional AI)
- ✅ **No dependencies:** Pure Python regex, no ML models
- ✅ **Transparent:** Judges can understand the logic
- ✅ **Demo-friendly:** Easy to explain and debug live

**Limitations:**
- ❌ **Brittle:** Different phrasings of same meaning require separate rules
- ❌ **No grammar understanding:** Can't parse sentence structure
- ❌ **Context-blind:** "stuck in traffic" vs "stuck creatively" → different needs
- ❌ **Negation handling:** "not happy" vs "not NOT happy" ambiguity
- ❌ **Requires exhaustive patterns:** Must enumerate variations

**Current Test Results:**
- "boss won't let me decide" → ⚖️ Autonomy (80%) ✓
- "friends don't invite me" → 🗣️ Connection (75%) ✓
- "overwhelmed, too much" → 🛌 Rest (85%) ✓
- "no one considers my needs" → ❌ Miss (needs "considers" pattern)
- "stuck in traffic standstill" → ❌ Miss (needs situational inference)
- "so boring I could die" → ❌ Miss (needs intensity understanding)

---

### Future Enhancement Options

#### Option 1: Enhanced Regex (RECOMMENDED FOR HACKATHON)
**Timeline:** 2-4 hours
**Latency Impact:** None (<100ms maintained)

**Enhancements:**
1. **Negation Handling**
   ```python
   # Check 10 chars before match for negation words
   if re.search(r'\b(not|no|never|don\'t)\b', before_match):
       skip_this_match()
   ```

2. **Structured Pattern Intensities**
   ```python
   "blocked": {
       "strong": r"(won't let|prevented|blocked)",  # +0.15 confidence
       "moderate": r"(can't|have to)",              # +0.10 confidence
       "weak": r"(doesn't give)"                    # +0.05 confidence
   }
   ```

3. **Situational Context Expansion**
   - Add "stuck in traffic" → powerless
   - Add "like always" → unstable (security)
   - Add "so boring" → underutilized
   - Add "pain again" → threatened

**Expected Improvement:** 70% → 85% accuracy
**Risk:** Low (incremental refinement)

---

#### Option 2: Dependency Parsing with spaCy
**Timeline:** 4-6 hours (includes testing)
**Latency Impact:** +300-500ms per message

**Implementation:**
```python
import spacy
nlp = spacy.load("en_core_web_sm")

doc = nlp("my boss doesn't give me projects I can do")

# Extract grammatical structure
subject = "boss"
negation = True
action = "give"
object = "projects"
relative_clause = "I can do"

# Inference: Subject blocks Object → Autonomy need
```

**Advantages:**
- ✅ Handles grammatical variations naturally
- ✅ Proper negation understanding
- ✅ Subject-verb-object relationship extraction
- ✅ Understands "I know I can do" (capability assertion)

**Disadvantages:**
- ❌ Adds 500MB+ dependency (spaCy model)
- ❌ Slower execution (300-500ms)
- ❌ More complex debugging
- ❌ Less interpretable (ML-based parsing)

**Expected Improvement:** 70% → 90% accuracy
**Risk:** Medium (new dependency, more complexity)

---

#### Option 3: Semantic Embeddings (sentence-transformers)
**Timeline:** 6-8 hours
**Latency Impact:** +400-700ms per message

**Implementation:**
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')

# Reference patterns for each need
autonomy_refs = [
    "my boss controls everything",
    "I have no choice",
    "they won't let me decide"
]

# Compare user message to references
msg_embedding = model.encode(user_message)
similarities = cosine_similarity(msg_embedding, autonomy_refs)

# High similarity → Autonomy need
```

**Advantages:**
- ✅ Handles paraphrasing ("micromanages" ≈ "controls everything")
- ✅ No need to enumerate every variation
- ✅ Semantic meaning understanding
- ✅ Can learn from examples

**Disadvantages:**
- ❌ "Black box" - can't explain WHY it matched
- ❌ 80MB+ model download
- ❌ Slower (300-700ms)
- ❌ Not Constitutional AI compliant (not interpretable)
- ❌ Requires curated reference examples

**Expected Improvement:** 70% → 88% accuracy
**Risk:** High (opaque, harder to debug, interpretability loss)

---

#### Option 4: Hybrid (Regex + LLM Fallback)
**Timeline:** 3-4 hours
**Latency Impact:** +2-3s only when regex fails

**Implementation:**
```python
# First: Try fast regex
needs = regex_detect(text, emotions)

# If nothing matched: Ask Claude
if not needs:
    prompt = f"""
    Analyze for psychological needs (Autonomy/Connection/Security/Rest/Recognition):
    Message: "{text}"
    Emotion: {emotion}

    What need is most likely? Explain reasoning.
    """
    needs = await claude.analyze(prompt)
```

**Advantages:**
- ✅ Best of both: fast regex + smart fallback
- ✅ Still interpretable (show Claude's reasoning)
- ✅ Handles edge cases naturally
- ✅ No new dependencies (already using Claude)

**Disadvantages:**
- ❌ Inconsistent latency (fast vs slow path)
- ❌ Different detection styles (regex vs LLM)
- ❌ More API costs for fallback cases
- ❌ Requires prompt engineering

**Expected Improvement:** 70% → 92% accuracy
**Risk:** Medium (inconsistent UX, API dependency)

---

### Decision Framework

**Choose Enhanced Regex IF:**
- ⏱️ Want quick wins (2-4 hours)
- 🎯 Current 70% accuracy acceptable for demo
- 🔍 Prioritize interpretability/transparency
- ⚡ Need <100ms latency
- 📊 Can demonstrate clear matching logic to judges

**Choose spaCy Dependency Parsing IF:**
- ⏱️ Have 4-6 hours to invest
- 🎯 Need 90%+ accuracy for credibility
- 🧠 Want grammatical sophistication
- ⚡ 300-500ms latency acceptable
- 🎓 Want to discuss NLP techniques in interviews

**Choose Semantic Embeddings IF:**
- ⏱️ Have 6-8 hours for implementation + testing
- 🎯 Need to handle creative paraphrasing
- 🤖 Comfortable with ML black boxes
- ⚡ 400-700ms latency acceptable
- 🎪 Judges care about ML sophistication over interpretability

**Choose Hybrid Fallback IF:**
- ⏱️ Have 3-4 hours
- 🎯 Want 90%+ accuracy without dependencies
- 💰 Comfortable with API costs
- ⚡ Variable latency acceptable
- 🔬 Want best of both approaches

---

### Recommended Timeline (2 weeks available)

**Week 1: Core Validation**
- Day 1-2: Test current regex system thoroughly (100 test cases)
- Day 3: Implement Enhanced Regex (negation + intensities)
- Day 4-5: Integrate needs detection into main app
- Day 6-7: Performance optimization (async, caching)

**Week 2: Polish & Advanced Features**
- Day 8-9: Add spaCy dependency parsing (if needed based on Week 1 accuracy)
- Day 10-11: UI polish, visualization improvements
- Day 12-13: Generate test suite, documentation
- Day 14: Buffer for bugs, rehearse demo

**Decision Point:** After Day 2 testing
- If accuracy >80%: Stick with Enhanced Regex, focus on other features
- If accuracy 60-80%: Implement spaCy
- If accuracy <60%: Consider Hybrid approach

---

### Next Session Action Items

1. ✅ **Test standalone app comprehensively**
   - Run 20-30 diverse test cases
   - Document hit rate and miss patterns
   - Identify most common failure modes

2. ✅ **Measure baseline accuracy**
   - Calculate % correctly detected needs
   - Find threshold for "good enough"

3. 🔄 **Choose enhancement path**
   - Based on accuracy results
   - Based on time available
   - Based on interpretability requirements

4. 🔄 **Implement chosen approach**
   - Enhanced Regex: 2-4 hours
   - spaCy: 4-6 hours
   - Hybrid: 3-4 hours

---

## Inference Rules: Emotion + Context → Need

### Pattern Structure
```python
{
    "emotions": ["primary_emotion", "secondary_emotion"],
    "contexts": ["context_pattern_1", "context_pattern_2"],
    "need": "need_id",
    "confidence_base": 0.75,  # Base confidence score
    "reasoning": "Why this pattern indicates this need"
}
```

### Confidence Boosting
- **+0.10** for each additional matching emotion
- **+0.10** for each additional matching context
- **+0.10** for high emotional intensity (arousal > 0.7)
- **Max confidence:** 0.95

---

## Coverage Map

### AUTONOMY (4 contexts, 4 rules)
**Contexts:**
- `blocked` - Direct barriers to action
- `powerless` - Feeling trapped/helpless
- `dismissed` - Being ignored/invalidated
- `underutilized` - Capabilities wasted
- `micromanaged` - Over-controlled

**Primary Emotions:** Anger, Frustration
**Example:** "they don't give me projects at work that I know I can do"

---

### CONNECTION (5 contexts, 6 rules)
**Contexts:**
- `isolated` - Alone/excluded
- `rejected` - Actively pushed away
- `misunderstood` - Not being heard
- `singled_out` - Everyone else but me
- `disconnected` - Drifting apart

**Primary Emotions:** Sadness, Loneliness, Hurt
**Secondary:** Anger (from rejection)
**Example:** "my friends do things without me"

---

### SECURITY (4 contexts, 5 rules)
**Contexts:**
- `uncertain` - Lack of clarity
- `unstable` - Unpredictable environment
- `threatened` - Unsafe/vulnerable
- `loss` - Losing grip/control

**Primary Emotions:** Anxiety, Fear, Worry
**Example:** "everything's so unpredictable, I don't know what's going to happen"

---

### REST (4 contexts, 5 rules)
**Contexts:**
- `overwhelmed` - Too much input
- `exhausted` - Energy depleted
- `overextended` - Spread too thin
- `boundary_violated` - Can't say no

**Primary Emotions:** Tired, Exhausted, Drained
**Secondary:** Anxiety (from overwhelm)
**Example:** "I don't like going to places that are too crowded"

---

### RECOGNITION (4 contexts, 5 rules)
**Contexts:**
- `unappreciated` - Taken for granted
- `inadequate` - Not good enough
- `overlooked` - Passed over/ignored
- `criticized` - Attacked without acknowledgment

**Primary Emotions:** Sad, Inadequate, Hurt
**Secondary:** Anger (at being unseen)
**Example:** "everyone takes me for granted"

---

## Design Principles

1. **Interpretability** - All patterns are regex-based and human-auditable
2. **Psychological Grounding** - Based on validated need theories
3. **Constitutional AI** - Respects dignity by treating emotions as signals, not problems
4. **Multi-need Detection** - Can detect multiple needs simultaneously (e.g., autonomy + recognition)
5. **Confidence Scoring** - Transparent scoring allows for nuanced responses

---

## Test Coverage Strategy

### High-Priority Test Cases (20 each need = 100 total)

**AUTONOMY:**
- Boss blocking decisions
- Micromanagement
- Skills underutilized
- Being controlled/forced

**CONNECTION:**
- Social exclusion
- Rejection/ghosting
- Feeling misunderstood
- Friends doing things without me

**SECURITY:**
- Unpredictable situations
- Job/relationship instability
- Fear/vulnerability
- Loss of control

**REST:**
- Overwhelm/burnout
- Boundary violations
- Sensory overload (crowds)
- Can't say no

**RECOGNITION:**
- Unappreciated effort
- Feeling invisible
- Criticism without acknowledgment
- Credit taken by others

---

## 📍 Current Session State (End of Nov 14, 2025)

### ✅ Completed Today:
1. **Needs detection core implemented**
   - 24 context patterns (5 categories: Autonomy, Connection, Security, Rest, Recognition)
   - 24 inference rules (emotion + context → need)
   - Confidence scoring with boosting
   - File: `utils/needs_lexicon.py` (454 lines)

2. **Standalone testing app created**
   - Gradio interface on port 7864
   - Manual controls (text, emotions, valence, arousal)
   - History tracker showing last 20 detections
   - 7 built-in test cases
   - File: `test_needs_detector.py` (~200 lines)

3. **Pattern refinements based on testing**
   - Removed strict word boundaries (`\b`) for better matching
   - Added situational patterns: "don't invite", "stuck in", "so boring", "like always"
   - Added indirect context signals: "doesn't consider", "pain again", "stand still"
   - Current accuracy: ~70% on manual tests

4. **Documentation completed**
   - Strategic framework documented (this file)
   - Technical implementation options analyzed
   - Performance optimization roadmap (HACKATHON_PLAN.md)
   - Ryan & Deci SDT summary provided

### 🔄 In Progress:
- **Testing standalone app** - Validating pattern accuracy
- **Identifying missing patterns** - Cases where detection fails
  - "no one considers my needs" → Miss (needs "considers" pattern) ✅ FIXED
  - "stuck in traffic" → Miss (needs situational inference) ✅ FIXED
  - "so boring" → Miss (needs intensity understanding) ✅ FIXED

### ⏳ Next Session Priorities (Nov 15, 3 PM):
1. **Continue validation testing** - Run 20-30 diverse cases, measure accuracy
2. **Choose enhancement path** based on accuracy:
   - If >80%: Integrate into main app
   - If 60-80%: Implement Enhanced Regex (negation handling)
   - If <60%: Consider spaCy dependency parsing
3. **Integration decision** - Determine when to add to emotion_server.py
4. **Performance optimization** - Start with parallelization if needed

### 🎯 Known Issues to Address:
- Some indirect expressions still not caught (need more testing)
- Negation handling not yet implemented (e.g., "not happy" vs "not NOT happy")
- Intensity/strength levels not differentiated (all matches weighted equally)
- False negatives on situational descriptions without explicit emotion words

### 📊 Success Metrics to Track:
- Pattern accuracy: Target >85% for integration
- False positive rate: Keep <10%
- Confidence score calibration: 70-95% range appropriate
- Latency: Confirmed <100ms (NOT a bottleneck)

### 🔧 Technical Context:
- **Main app latency:** 9 seconds total (needs detection adds <0.1s)
- **Bottleneck:** Claude API (5-6s) + sequential MCP calls (2-3s)
- **Optimization priority:** Streaming + parallelization, NOT needs detection
- **Timeline:** 2 weeks until deadline

### 💡 Key Decisions Made:
1. **Stick with regex for now** - Fast, interpretable, Constitutional AI aligned
2. **Table advanced NLP** - spaCy/embeddings available if accuracy insufficient
3. **Focus on validation** - Get baseline accuracy before choosing enhancement
4. **Keep needs detection fast** - Don't sacrifice speed for marginal accuracy gains

---

## Next Steps

1. ✅ **Strategic framework implemented** (24 contexts, 24 rules)
2. ⏳ **Test standalone** - Validate patterns with test_needs_detector.py
3. ⏳ **Generate test suite** - 100 cases covering all patterns
4. ⏳ **Integrate into emotion_server** - Add needs to analysis pipeline
5. ⏳ **Add UI visualization** - Display needs in main Ghost Malone app
6. ⏳ **Update reflection prompts** - Claude acknowledges detected needs

---

## Validation Checklist

For each test case, verify:
- ✅ Correct need detected
- ✅ Confidence score is appropriate (70-95%)
- ✅ Matched contexts are accurate
- ✅ Matched emotions align
- ✅ Reasoning makes psychological sense
- ✅ Suggested interventions are helpful
