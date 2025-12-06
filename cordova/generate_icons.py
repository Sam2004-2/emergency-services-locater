#!/usr/bin/env python3
"""Generate placeholder icons for Cordova app"""
import os

# SVG template for the icon
SVG_TEMPLATE = '''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">
  <rect width="{size}" height="{size}" fill="#0077B6"/>
  <text x="50%" y="55%" text-anchor="middle" fill="white" font-size="{font_size}" font-family="Arial, sans-serif" font-weight="bold">ES</text>
</svg>'''

# iOS icons
ios_icons = [
    ("icon-60@3x.png", 180),
    ("icon-60.png", 60),
    ("icon-60@2x.png", 120),
    ("icon-76.png", 76),
    ("icon-76@2x.png", 152),
    ("icon-40.png", 40),
    ("icon-40@2x.png", 80),
    ("icon-57.png", 57),
    ("icon-57@2x.png", 114),
    ("icon-72.png", 72),
    ("icon-72@2x.png", 144),
    ("icon-83.5@2x.png", 167),
    ("icon-small.png", 29),
    ("icon-small@2x.png", 58),
    ("icon-small@3x.png", 87),
    ("icon-1024.png", 1024),
]

# Android icons
android_icons = [
    ("mipmap-ldpi/ic_launcher.png", 36),
    ("mipmap-mdpi/ic_launcher.png", 48),
    ("mipmap-hdpi/ic_launcher.png", 72),
    ("mipmap-xhdpi/ic_launcher.png", 96),
    ("mipmap-xxhdpi/ic_launcher.png", 144),
    ("mipmap-xxxhdpi/ic_launcher.png", 192),
]

def create_svg(path, size):
    font_size = max(12, size // 3)
    svg_content = SVG_TEMPLATE.format(size=size, font_size=font_size)
    svg_path = path.replace('.png', '.svg')
    with open(svg_path, 'w') as f:
        f.write(svg_content)
    print(f"Created: {svg_path}")

# Create iOS icons
for name, size in ios_icons:
    path = f"res/icon/ios/{name}"
    create_svg(path, size)

# Create Android icons
for name, size in android_icons:
    path = f"res/icon/android/{name}"
    create_svg(path, size)

# Create splash screen placeholder
splash_svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="2732" height="2732" viewBox="0 0 2732 2732">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#0077B6"/>
      <stop offset="100%" style="stop-color:#023E8A"/>
    </linearGradient>
  </defs>
  <rect width="2732" height="2732" fill="url(#grad)"/>
  <text x="50%" y="45%" text-anchor="middle" fill="white" font-size="200" font-family="Arial, sans-serif" font-weight="bold">ES Locator</text>
  <text x="50%" y="55%" text-anchor="middle" fill="rgba(255,255,255,0.8)" font-size="80" font-family="Arial, sans-serif">Emergency Services</text>
</svg>'''

with open("res/screen/ios/Default@2x~universal~anyany.svg", 'w') as f:
    f.write(splash_svg)
print("Created splash screen")

print("\nDone! Note: These are SVG placeholders.")
print("For production, convert to PNG using: brew install librsvg && rsvg-convert")
