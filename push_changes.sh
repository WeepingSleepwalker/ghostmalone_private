#!/bin/bash

# Push current working version to private GitHub repo
# Ghost Malone - Mirror-first reflection updates

set -e  # Exit on error

echo "📦 Staging changes..."
git add .

echo "💬 Committing..."
git commit -m "Update reflection: mirror-first, more concise responses

- Reduced word limit from 80 to 60 words
- Explicit instruction sequence: mirror → validate → (optional) anchor
- No premature solutions or therapy-speak
- Stronger emotion arc integration in system prompts
- Working baseline with Claude Sonnet 4.5 integration"

echo "🚀 Pushing to GitHub..."
git push origin main

echo "✅ Done! Changes pushed to https://github.com/WeepingSleepwalker/ghostmalone_private"
