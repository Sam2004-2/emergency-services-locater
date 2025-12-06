# ES Locator - Cordova Mobile App

This is the Cordova wrapper for the Emergency Services Locator application, enabling native mobile app distribution for iOS and Android.

## Prerequisites

- Node.js 18+ and npm
- Cordova CLI: `npm install -g cordova`
- For iOS: macOS with Xcode 15+
- For Android: Android Studio with SDK 34+

## Setup

1. **Install dependencies:**
   ```bash
   cd cordova
   npm install
   ```

2. **Configure API URL:**
   Edit `www/js/app.js` and update `API_BASE_URL` to point to your production server:
   ```javascript
   const API_BASE_URL = 'https://your-server.com';
   ```

3. **Add platforms:**
   ```bash
   cordova platform add ios
   cordova platform add android
   ```

4. **Install plugins:**
   ```bash
   cordova plugin add cordova-plugin-device
   cordova plugin add cordova-plugin-geolocation
   cordova plugin add cordova-plugin-network-information
   cordova plugin add cordova-plugin-statusbar
   cordova plugin add cordova-plugin-splashscreen
   cordova plugin add cordova-plugin-whitelist
   ```

## Development

### Run in Browser
```bash
cordova serve
# Open http://localhost:8000
```

### Run on iOS Simulator
```bash
cordova emulate ios
```

### Run on Android Emulator
```bash
cordova emulate android
```

### Run on Connected Device
```bash
cordova run ios --device
cordova run android --device
```

## Building for Release

### iOS
1. Open `platforms/ios/ES Locator.xcworkspace` in Xcode
2. Configure signing with your Apple Developer account
3. Archive and distribute through App Store Connect

### Android
```bash
cordova build android --release
```

The release APK will be at:
`platforms/android/app/build/outputs/apk/release/app-release-unsigned.apk`

Sign the APK:
```bash
jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 \
  -keystore your-keystore.jks \
  app-release-unsigned.apk your-alias
zipalign -v 4 app-release-unsigned.apk es-locator.apk
```

## App Icons and Splash Screens

Place your icons and splash screens in the `res/` directory:

```
res/
├── icon/
│   ├── android/
│   │   └── mipmap-*/ic_launcher.png
│   └── ios/
│       └── icon-*.png
└── screen/
    ├── android/
    │   └── splash-*.png
    └── ios/
        └── Default@2x~universal~anyany.png
```

Use a tool like [cordova-res](https://github.com/ionic-team/cordova-res) to generate all sizes:
```bash
npm install -g cordova-res
cordova-res ios --skip-config --copy
cordova-res android --skip-config --copy
```

## Features

- **JWT Authentication**: Secure token-based login with automatic refresh
- **Offline Support**: Network status detection with reconnection handling
- **Geolocation**: Real-time user location tracking
- **Push Notifications**: (Future) Firebase Cloud Messaging integration
- **Native Feel**: Platform-specific status bar and splash screen

## Backend Requirements

The Django backend must have:
1. CORS headers enabled for the mobile app origin
2. JWT endpoints: `/api/auth/token/` and `/api/auth/token/refresh/`
3. HTTPS in production (required for iOS App Transport Security)

## Troubleshooting

### iOS Build Issues
- Ensure CocoaPods is installed: `sudo gem install cocoapods`
- Run `pod install` in `platforms/ios/`

### Android Build Issues
- Ensure ANDROID_HOME is set
- Accept SDK licenses: `sdkmanager --licenses`

### Network Issues
- For development with localhost, enable cleartext traffic in `config.xml`
- In production, always use HTTPS
