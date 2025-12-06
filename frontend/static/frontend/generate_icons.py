#!/usr/bin/env python3
"""
Generate PWA icons for Emergency Services Locator

This script creates simple placeholder icons. For production, replace with 
professionally designed icons using tools like Figma, Adobe Illustrator, or 
online icon generators like https://www.pwabuilder.com/imageGenerator

Requires: Pillow (PIL)
Install: pip install Pillow
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Icon sizes to generate
SIZES = [72, 96, 128, 144, 152, 192, 384, 512]
MASKABLE_SIZES = [192, 512]

# Colors
BG_COLOR = '#0077B6'  # Ocean blue
FG_COLOR = '#FFFFFF'  # White

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def create_icon(size, is_maskable=False):
    """Create an emergency services icon"""
    # Create base image
    img = Image.new('RGB', (size, size), hex_to_rgb(BG_COLOR))
    draw = ImageDraw.Draw(img)
    
    # Calculate safe zone for maskable icons (80% of size)
    if is_maskable:
        padding = int(size * 0.1)
    else:
        padding = int(size * 0.15)
    
    # Draw location pin
    pin_width = size - (padding * 2)
    pin_height = int(pin_width * 1.4)
    pin_top = padding
    pin_left = padding
    
    # Pin body (teardrop shape)
    pin_center_x = pin_left + pin_width // 2
    pin_center_y = pin_top + pin_width // 2
    
    # Draw pin circle
    circle_radius = pin_width // 2
    draw.ellipse(
        [
            pin_center_x - circle_radius,
            pin_center_y - circle_radius,
            pin_center_x + circle_radius,
            pin_center_y + circle_radius
        ],
        fill=hex_to_rgb(FG_COLOR)
    )
    
    # Draw pin point (triangle)
    point_height = int(pin_width * 0.6)
    draw.polygon(
        [
            (pin_center_x, pin_center_y + circle_radius + point_height),
            (pin_center_x - circle_radius // 2, pin_center_y + circle_radius),
            (pin_center_x + circle_radius // 2, pin_center_y + circle_radius)
        ],
        fill=hex_to_rgb(FG_COLOR)
    )
    
    # Draw cross (emergency symbol)
    cross_size = int(circle_radius * 0.6)
    cross_width = cross_size // 5
    
    # Horizontal bar
    draw.rectangle(
        [
            pin_center_x - cross_size // 2,
            pin_center_y - cross_width // 2,
            pin_center_x + cross_size // 2,
            pin_center_y + cross_width // 2
        ],
        fill=hex_to_rgb(BG_COLOR)
    )
    
    # Vertical bar
    draw.rectangle(
        [
            pin_center_x - cross_width // 2,
            pin_center_y - cross_size // 2,
            pin_center_x + cross_width // 2,
            pin_center_y + cross_size // 2
        ],
        fill=hex_to_rgb(BG_COLOR)
    )
    
    return img

def main():
    """Generate all icon sizes"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    icons_dir = os.path.join(script_dir, 'icons')
    
    # Create icons directory if it doesn't exist
    os.makedirs(icons_dir, exist_ok=True)
    
    print("Generating PWA icons...")
    
    # Generate regular icons
    for size in SIZES:
        img = create_icon(size, is_maskable=False)
        filename = f'icon-{size}x{size}.png'
        filepath = os.path.join(icons_dir, filename)
        img.save(filepath, 'PNG')
        print(f"✓ Created {filename}")
    
    # Generate maskable icons
    for size in MASKABLE_SIZES:
        img = create_icon(size, is_maskable=True)
        filename = f'icon-{size}x{size}-maskable.png'
        filepath = os.path.join(icons_dir, filename)
        img.save(filepath, 'PNG')
        print(f"✓ Created {filename} (maskable)")
    
    print("\n✅ All icons generated successfully!")
    print(f"📁 Location: {icons_dir}")
    print("\n💡 Tip: For production, consider using professionally designed icons.")
    print("   Visit https://www.pwabuilder.com/imageGenerator for better quality.")

if __name__ == '__main__':
    try:
        main()
    except ImportError:
        print("❌ Error: Pillow is required to generate icons.")
        print("Install it with: pip install Pillow")
        exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)
