# Cordova Mobile App for Emergency Services Locator

This directory contains the Apache Cordova project for building native iOS and Android apps.

## Prerequisites

1. **Node.js** (v16 or later)
2. **Cordova CLI**: `npm install -g cordova`
3. **For Android:**
   - Android Studio
   - Android SDK (API level 24+)
   - Java JDK 11+
4. **For iOS:**
   - macOS with Xcode 14+
   - iOS development certificate

## Setup

```bash
cd cordova

# Install dependencies
npm install

# Add platforms
cordova platform add android
cordova platform add ios

# Install plugins (should be automatic, but if needed)
cordova plugin add cordova-plugin-geolocation
cordova plugin add cordova-plugin-network-information
cordova plugin add cordova-plugin-statusbar
cordova plugin add cordova-plugin-splashscreen
cordova plugin add cordova-plugin-device
```

## Configuration

Edit `www/index.html` and update the `API_BASE` constant to point to your production server:

```javascript
const API_BASE = 'https://your-production-url.com';
```

## Build Commands

### Android

```bash
# Debug build
cordova build android

# Release build (requires signing key)
cordova build android --release

# Run on connected device
cordova run android

# Run on emulator
cordova emulate android
```

### iOS

```bash
# Debug build
cordova build ios

# Release build
cordova build ios --release

# Run on simulator
cordova emulate ios

# Open in Xcode for device deployment
open platforms/ios/ES\ Locator.xcworkspace
```

## Project Structure

```
cordova/
├── config.xml          # Cordova configuration (plugins, preferences, icons)
├── package.json        # NPM dependencies and scripts
├── www/                # Web assets (copied to platforms)
│   └── index.html      # Main app entry point
├── res/                # Platform-specific resources
│   ├── icon/           # App icons (various sizes)
│   └── screen/         # Splash screens
└── platforms/          # Generated platform projects (gitignored)
    ├── android/
    └── ios/
```

## Features

- **Geolocation**: Uses device GPS for accurate location
- **Offline Detection**: Shows banner when network unavailable
- **Native UI**: Mobile-optimized interface with touch gestures
- **Map Integration**: Leaflet maps with marker clustering
- **API Integration**: Connects to Django REST API backend

## Customization

### App Icons

Replace the placeholder icons in `res/icon/` with your actual app icons. Required sizes:

**Android:**
- 36x36 (ldpi), 48x48 (mdpi), 72x72 (hdpi)
- 96x96 (xhdpi), 144x144 (xxhdpi), 192x192 (xxxhdpi)

**iOS:**
- 29x29, 40x40, 57x57, 60x60, 72x72, 76x76
- @2x and @3x variants
- 1024x1024 (App Store)

### Splash Screens

Create splash screens in `res/screen/` for both orientations and various densities.

## Signing for Release

### Android

Create a signing key:
```bash
keytool -genkey -v -keystore es-locator.keystore -alias es-locator -keyalg RSA -keysize 2048 -validity 10000
```

Build signed APK:
```bash
cordova build android --release -- --keystore=es-locator.keystore --alias=es-locator
```

### iOS

Use Xcode to manage certificates and provisioning profiles, then archive for App Store submission.

## Troubleshooting

### Android build fails
- Ensure ANDROID_HOME is set
- Run `cordova requirements android`
- Update Android SDK and build tools

### iOS build fails
- Ensure Xcode command line tools: `xcode-select --install`
- Run `cordova requirements ios`
- Check code signing in Xcode

### Geolocation not working
- Check app permissions in device settings
- Ensure HTTPS for production (required for geolocation)
