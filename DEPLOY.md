# Deploying Ghost Malone to HuggingFace Spaces

## Prerequisites

1. HuggingFace account
2. Anthropic API key

## Steps

### 1. Create a new Space

1. Go to https://huggingface.co/spaces
2. Click "Create new Space"
3. Name: `ghost-malone`
4. License: MIT
5. SDK: **Gradio**
6. Hardware: CPU Basic (free) - should be enough
7. Click "Create Space"

### 2. Add your API key as a Secret

⚠️ **CRITICAL:** Don't commit your API key to the repo!

1. In your Space settings, go to "Repository secrets"
2. Add a new secret:
   - Name: `ANTHROPIC_API_KEY`
   - Value: Your Anthropic API key (sk-ant-...)
3. Save

### 3. Upload Files

You can either:

**Option A: Git push**
```bash
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/ghost-malone
git push hf main
```

**Option B: Web upload**
1. Upload these files via the web interface:
   - `app.py`
   - `requirements.txt`
   - `servers/` folder (all 3 server files)
   - `utils/` folder (all utility files)
   - `.env` is NOT needed (using Secrets instead)

### 4. Files to Upload

```
ghost-malone/
├── app.py                          ← Main Gradio app
├── requirements.txt                ← Dependencies
├── servers/
│   ├── __init__.py
│   ├── emotion_server.py
│   ├── memory_server.py
│   └── reflection_server.py
└── utils/
    ├── __init__.py
    ├── mcp_client.py
    ├── orchestrator.py
    ├── needs_lexicon.py
    └── intervention_lexicon.py
```

**DO NOT upload:**
- `.env` (has your API key!)
- `memory.json` (gets created at runtime)
- `test_*.py` files
- `__pycache__/` folders
- `.venv/` folder

### 5. Environment Variable Setup

HuggingFace Spaces automatically makes secrets available as environment variables, so your existing code will work:

```python
# app.py already has this:
load_dotenv()  # Falls back to environment variables
```

The `ANTHROPIC_API_KEY` from Secrets will be available automatically!

### 6. Verify Deployment

1. Wait for Space to build (2-3 minutes)
2. Check the logs for errors
3. Test with: "i feel so lonely there's no one to talk to"
4. Should see interventions on message 2!

## Common Issues

### "ANTHROPIC_API_KEY not found"
- Make sure you added it in Repository secrets
- Restart the Space after adding secrets

### "Module not found"
- Check `requirements.txt` has all dependencies
- Current version includes: gradio, fastmcp, mcp, anthropic, python-dotenv, plotly

### Slow responses
- Free tier CPU is slower than local
- Claude API calls take 5-6 seconds (normal)
- Loading indicator shows progress

### Memory persists between users
- Each deployment clears `memory.json`
- Consider adding user sessions if needed (future enhancement)

## Resource Limits (Free Tier)

- **CPU:** Basic (enough for this app)
- **RAM:** 16GB
- **Storage:** Temporary (memory.json cleared on restart)
- **Uptime:** Sleep after inactivity, wakes on access

## Cost Optimization

Your Anthropic API calls are the only cost:
- **Free tier:** 5 requests/minute
- **Demo usage:** ~3 messages = 3 API calls
- **Should be fine for hackathon demo**

If you hit rate limits, add this to `app.py`:

```python
import time
# Add rate limiting
time.sleep(12)  # 5 req/min = 12s between calls
```

## Demo Tips

1. **Test locally first:** Make sure everything works
2. **Clear memory.json** before deploying (fresh start)
3. **Use demo script phrases** for guaranteed success
4. **Monitor logs** during demo to catch issues

## Hackathon Submission

Include in your submission:
- **Live URL:** https://huggingface.co/spaces/YOUR_USERNAME/ghost-malone
- **GitHub repo:** Your private repo (or make public)
- **Demo video:** Record using the DEMO_SCRIPT.md phrases
- **Architecture diagram:** Show 3-server MCP design

Good luck! 🚀
