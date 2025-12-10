#!/bin/bash
# Quick deploy to Netlify

set -e

API_URL=${1:-"https://your-api.onrender.com/api/v1"}

echo "🌐 Deploying to Netlify"
echo "📡 API URL: $API_URL"
echo ""

# Check if netlify CLI is installed
if ! command -v netlify &> /dev/null; then
    echo "Installing Netlify CLI..."
    npm install -g netlify-cli
fi

# Build
cd mobile
echo "🔨 Building Flutter web app..."
flutter build web --release --dart-define=API_URL=$API_URL

# Deploy
echo "🚀 Deploying to Netlify..."
cd build/web
netlify deploy --prod

echo ""
echo "✅ Deployment complete!"
echo "Visit your site at the URL shown above"
