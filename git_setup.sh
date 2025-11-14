#!/bin/bash
# Git setup script for Ghost Malone

echo "🔧 Initializing Git repository..."
git init

echo "📦 Adding files..."
git add .

echo "💾 Creating initial commit..."
git commit -m "Initial commit: Ghost Malone with emotion arc tracking"

echo "🌿 Setting main branch..."
git branch -M main

echo "🔗 Adding remote origin..."
git remote add origin https://github.com/WeepingSleepwalker/ghostmalone_private.git

echo "🚀 Pushing to GitHub..."
git push -u origin main

echo "✅ Done! Your code is now in the private repo."
