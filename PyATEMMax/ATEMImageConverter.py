#!/usr/bin/env python3
# coding: utf-8
"""
ATEMImageConverter: Convert images to ATEM format (UYVY 4:2:2)
Part of the PyATEMMax library.
"""


def convertImageToATEMFormat(image, width: int = 1920, height: int = 1080):
    """Convert a PIL Image to ATEM format (UYVY 4:2:2)
    
    Args:
        image: PIL Image object (or any object with similar interface)
        width (int): Target width (default 1920 for 1080p)
        height (int): Target height (default 1080 for 1080p)
    
    Returns:
        bytes: Image data in UYVY 4:2:2 format
    
    The ATEM switcher uses UYVY 4:2:2 format with 10-bit precision:
    - Each pair of pixels is encoded in 8 bytes
    - Format: A1 U1 Y1 | A2 V2 Y2 (10 bits each, packed)
    """
    
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        raise ImportError("PIL (Pillow) is required for image conversion. Install with: pip install Pillow")
    
    # Convert to RGBA if needed
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # Resize/crop to exact dimensions
    # First, crop if image is larger
    if image.width > width:
        left = (image.width - width) // 2
        image = image.crop((left, 0, left + width, image.height))
    
    if image.height > height:
        top = (image.height - height) // 2
        image = image.crop((0, top, image.width, top + height))
    
    # If image is smaller, create a blank canvas and paste in center
    if image.width < width or image.height < height:
        blank = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        x_offset = (width - image.width) // 2
        y_offset = (height - image.height) // 2
        blank.paste(image, (x_offset, y_offset))
        image = blank
    
    # Convert pixels to UYVY 4:2:2 format
    pixels = image.load()
    data = bytearray(width * height * 4)
    
    for y in range(height):
        for x in range(0, width, 2):
            # Get two adjacent pixels
            r1, g1, b1, a1 = pixels[x, y]
            r2, g2, b2, a2 = pixels[x + 1, y]
            
            # Scale alpha to 10-bit (0-1023)
            alpha1 = int(a1 * 3.7)  # 255 * 3.7 ≈ 943, leaving headroom
            alpha2 = int(a2 * 3.7)
            
            # RGB to YUV conversion (ITU-R BT.601)
            # Y = 0.299*R + 0.587*G + 0.114*B
            # U = -0.14713*R - 0.28886*G + 0.436*B + 128
            # V = 0.615*R - 0.51499*G - 0.10001*B + 128
            # Scaled to 10-bit (0-1023)
            
            y1 = int(((66 * r1 + 129 * g1 + 25 * b1 + 128) >> 8) + 16) * 4 - 1
            u1 = int(((-38 * r1 - 74 * g1 + 112 * b1 + 128) >> 8) + 128) * 4 - 1
            y2 = int(((66 * r2 + 129 * g2 + 25 * b2 + 128) >> 8) + 16) * 4 - 1
            v2 = int(((112 * r2 - 94 * g2 - 18 * b2 + 128) >> 8) + 128) * 4 - 1
            
            # Clamp to 10-bit range
            alpha1 = max(0, min(1023, alpha1))
            alpha2 = max(0, min(1023, alpha2))
            y1 = max(0, min(1023, y1))
            u1 = max(0, min(1023, u1))
            y2 = max(0, min(1023, y2))
            v2 = max(0, min(1023, v2))
            
            # Pack into bytes (10 bits each, 8 bytes total for 2 pixels)
            # Format: A1(10) U1(10) Y1(10) A2(10) V2(10) Y2(10)
            # Byte layout:
            # [0]: A1[9:2]
            # [1]: A1[1:0] U1[9:6]
            # [2]: U1[5:0] Y1[9:8]
            # [3]: Y1[7:0]
            # [4]: A2[9:2]
            # [5]: A2[1:0] V2[9:6]
            # [6]: V2[5:0] Y2[9:8]
            # [7]: Y2[7:0]
            
            idx = (y * width + x) * 4
            
            data[idx + 0] = (alpha1 >> 4) & 0xFF
            data[idx + 1] = (((alpha1 & 0x0F) << 4) | ((u1 >> 6) & 0x0F)) & 0xFF
            data[idx + 2] = (((u1 & 0x3F) << 2) | ((y1 >> 8) & 0x03)) & 0xFF
            data[idx + 3] = y1 & 0xFF
            
            data[idx + 4] = (alpha2 >> 4) & 0xFF
            data[idx + 5] = (((alpha2 & 0x0F) << 4) | ((v2 >> 6) & 0x0F)) & 0xFF
            data[idx + 6] = (((v2 & 0x3F) << 2) | ((y2 >> 8) & 0x03)) & 0xFF
            data[idx + 7] = y2 & 0xFF
    
    return bytes(data)


def loadAndConvertImage(filepath: str, width: int = 1920, height: int = 1080) -> bytes:
    """Load an image file and convert it to ATEM format
    
    Args:
        filepath (str): Path to image file
        width (int): Target width (default 1920 for 1080p)
        height (int): Target height (default 1080 for 1080p)
    
    Returns:
        bytes: Image data in UYVY 4:2:2 format
    """
    
    try:
        from PIL import Image
    except ImportError:
        raise ImportError("PIL (Pillow) is required for image conversion. Install with: pip install Pillow")
    
    image = Image.open(filepath)
    return convertImageToATEMFormat(image, width, height)
