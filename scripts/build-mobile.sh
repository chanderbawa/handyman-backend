#!/bin/bash
# Build mobile apps for release

set -e

API_URL=${1:-"https://your-api.onrender.com/api/v1"}

echo "🚀 Building HandyMan Mobile Apps"
echo "📡 API URL: $API_URL"
echo ""

cd mobile

# Build Android APK
echo "📱 Building Android APK..."
flutter build apk --release --dart-define=API_URL=$API_URL
echo "✅ Android APK: mobile/build/app/outputs/flutter-apk/app-release.apk"
echo ""

# Build Android App Bundle (for Play Store)
echo "📦 Building Android App Bundle..."
flutter build appbundle --release --dart-define=API_URL=$API_URL
echo "✅ App Bundle: mobile/build/app/outputs/bundle/release/app-release.aab"
echo ""

# Build Web
echo "🌐 Building Web App..."
flutter build web --release --dart-define=API_URL=$API_URL
echo "✅ Web Build: mobile/build/web"
echo ""

echo "✨ All builds complete!"
echo ""
echo "Next steps:"
echo "  - Android APK: Share directly or upload to Play Store"
echo "  - Android Bundle: Upload to Play Console"
echo "  - Web: Deploy build/web to Netlify/Vercel"
