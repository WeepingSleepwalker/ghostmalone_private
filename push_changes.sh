#!/bin/bash

# Push current working version to private GitHub repo
# Ghost Malone - Emotion trajectory visualization

set -e  # Exit on error

echo "📦 Staging changes..."
git add .

echo "💬 Committing..."
git commit -m "Add emotion trajectory visualization & state persistence

Visual Features:
- Plotly scatter plot showing emotions on valence/arousal grid
- Real-time trajectory tracking with directional analysis
- Text summary displaying emotion arc (escalating/stable/etc.)
- Quadrant labels: Excited, Anxious, Calm, Sad

Emotion Intelligence:
- State persistence: neutral messages inherit previous emotion
- Enhanced emotion detection patterns (pissy, infuriating, frustrated)
- Emotion decay over time for realistic continuity
- Memory cleared on startup for fresh conversations

Reflection Improvements:
- Mirror-first approach (60 word limit)
- No premature solutions or therapy-speak
- Emotion arc context passed to Claude Sonnet 4.5

Technical:
- Fixed emotion trajectory data structure (primary_label)
- Plotly integration with Gradio
- Improved MCP tool coordination"

echo "🚀 Pushing to GitHub..."
git push origin main

echo "✅ Done! Changes pushed to https://github.com/WeepingSleepwalker/ghostmalone_private"
