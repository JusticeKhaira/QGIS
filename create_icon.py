"""
Create a professional icon for Proximity Feature Finder plugin
Run this script to generate icon.png
"""

try:
    from PIL import Image, ImageDraw, ImageFont
    import math
    
    # Create 256x256 image for high quality
    size = 256
    img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Define colors
    primary_color = (102, 126, 234)      # Purple-blue
    secondary_color = (118, 75, 162)     # Dark purple
    accent_color = (46, 204, 113)        # Green
    white = (255, 255, 255)
    
    # Draw background circle with gradient effect
    center = size // 2
    
    # Outer circle (shadow)
    draw.ellipse([10, 10, size-10, size-10], fill=secondary_color)
    
    # Main circle
    draw.ellipse([20, 20, size-20, size-20], fill=primary_color)
    
    # Draw concentric circles (representing buffer zones)
    circle_sizes = [180, 140, 100, 60]
    for i, circle_size in enumerate(circle_sizes):
        offset = (size - circle_size) // 2
        alpha = 100 - (i * 20)  # Decreasing opacity
        color = primary_color + (alpha,)
        draw.ellipse(
            [offset, offset, offset + circle_size, offset + circle_size],
            outline=white,
            width=3
        )
    
    # Draw center point (source location)
    center_size = 30
    center_offset = (size - center_size) // 2
    draw.ellipse(
        [center_offset, center_offset, 
         center_offset + center_size, center_offset + center_size],
        fill=accent_color,
        outline=white,
        width=3
    )
    
    # Draw small dots around (representing found features)
    dot_positions = [
        (center + 50, center - 30),
        (center + 60, center + 20),
        (center - 40, center + 40),
        (center - 50, center - 20),
        (center + 20, center - 60),
        (center - 30, center - 50),
    ]
    
    for pos in dot_positions:
        dot_size = 12
        draw.ellipse(
            [pos[0] - dot_size//2, pos[1] - dot_size//2,
             pos[0] + dot_size//2, pos[1] + dot_size//2],
            fill=accent_color,
            outline=white,
            width=2
        )
    
    # Draw connecting lines (showing proximity relationships)
    line_color = white + (150,)  # Semi-transparent white
    for pos in dot_positions:
        draw.line([center, center, pos[0], pos[1]], 
                  fill=line_color, width=2)
    
    # Add distance measurement symbol (ruler-like lines)
    ruler_y = center + 80
    ruler_start = center - 40
    ruler_end = center + 40
    
    # Horizontal line
    draw.line([ruler_start, ruler_y, ruler_end, ruler_y], 
              fill=white, width=3)
    
    # Tick marks
    for x in [ruler_start, center, ruler_end]:
        draw.line([x, ruler_y - 5, x, ruler_y + 5], 
                  fill=white, width=3)
    
    # Resize to 64x64 for final icon
    icon_64 = img.resize((64, 64), Image.LANCZOS)
    
    # Save both sizes
    icon_64.save('icon.png')
    img.save('icon_large.png')
    
    print("✅ Icons created successfully!")
    print("   - icon.png (64x64) - Use this for the plugin")
    print("   - icon_large.png (256x256) - High resolution version")
    
except ImportError:
    print("⚠️  PIL/Pillow not installed. Creating simple icon...")
    
    # Fallback: Create simple icon without PIL
    # Create SVG icon instead
    svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <!-- Background circle -->
  <circle cx="32" cy="32" r="30" fill="#667eea" opacity="0.9"/>
  
  <!-- Buffer rings -->
  <circle cx="32" cy="32" r="24" fill="none" stroke="#ffffff" stroke-width="2" opacity="0.6"/>
  <circle cx="32" cy="32" r="18" fill="none" stroke="#ffffff" stroke-width="2" opacity="0.5"/>
  <circle cx="32" cy="32" r="12" fill="none" stroke="#ffffff" stroke-width="2" opacity="0.4"/>
  
  <!-- Center point -->
  <circle cx="32" cy="32" r="6" fill="#2ecc71" stroke="#ffffff" stroke-width="2"/>
  
  <!-- Feature points -->
  <circle cx="44" cy="24" r="3" fill="#2ecc71" stroke="#ffffff" stroke-width="1.5"/>
  <circle cx="48" cy="36" r="3" fill="#2ecc71" stroke="#ffffff" stroke-width="1.5"/>
  <circle cx="22" cy="42" r="3" fill="#2ecc71" stroke="#ffffff" stroke-width="1.5"/>
  <circle cx="20" cy="26" r="3" fill="#2ecc71" stroke="#ffffff" stroke-width="1.5"/>
  
  <!-- Connection lines -->
  <line x1="32" y1="32" x2="44" y2="24" stroke="#ffffff" stroke-width="1.5" opacity="0.4"/>
  <line x1="32" y1="32" x2="48" y2="36" stroke="#ffffff" stroke-width="1.5" opacity="0.4"/>
  <line x1="32" y1="32" x2="22" y2="42" stroke="#ffffff" stroke-width="1.5" opacity="0.4"/>
  <line x1="32" y1="32" x2="20" y2="26" stroke="#ffffff" stroke-width="1.5" opacity="0.4"/>
  
  <!-- Distance indicator -->
  <line x1="22" y1="50" x2="42" y2="50" stroke="#ffffff" stroke-width="2"/>
  <line x1="22" y1="48" x2="22" y2="52" stroke="#ffffff" stroke-width="2"/>
  <line x1="42" y1="48" x2="42" y2="52" stroke="#ffffff" stroke-width="2"/>
</svg>'''
    
    with open('icon.svg', 'w') as f:
        f.write(svg_content)
    
    print("✅ SVG icon created: icon.svg")
    print("   Convert to PNG using online tool or GIMP")
    print("   Recommended: https://convertio.co/svg-png/")

print("\n📍 Icon Design:")
print("   - Purple-blue gradient background")
print("   - Concentric circles (buffer zones)")
print("   - Green center point (source location)")
print("   - Green dots (found features)")
print("   - White connection lines (proximity relationships)")
print("   - Distance measurement indicator")