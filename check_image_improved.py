#!/usr/bin/env python3
"""
Improved Image Checker
Checks if an image has been processed by visual-reasoning-tool-bm
"""

import sys
import piexif
from PIL import Image

def check_image(image_path):
    """Check if an image was processed by visual-reasoning-tool-bm"""
    try:
        print(f"Checking image: {image_path}")
        print("-" * 50)
        
        # Load EXIF data
        exif_dict = piexif.load(image_path)
        print(f"EXIF data found: {exif_dict}")
        
        # Check if there's any EXIF data at all
        if not exif_dict or all(not section for section in exif_dict.values() if section is not None):
            print("❌ No EXIF metadata found in image")
            return False
        
        # Check for the specific keyword in ImageDescription
        if "0th" in exif_dict and piexif.ImageIFD.ImageDescription in exif_dict["0th"]:
            description = exif_dict["0th"][piexif.ImageIFD.ImageDescription].decode('utf-8')
            print(f"Found ImageDescription: {description}")
            if description == "visual-reasoning-tool-bm-processed-image":
                print("✅ Matched ImageDescription keyword!")
                return True
        
        # Check software tag
        if "0th" in exif_dict and piexif.ImageIFD.Software in exif_dict["0th"]:
            software = exif_dict["0th"][piexif.ImageIFD.Software].decode('utf-8')
            print(f"Found Software: {software}")
            if software == "visual-reasoning-tool-bm":
                print("✅ Matched Software keyword!")
                return True
        
        # Check artist tag
        if "0th" in exif_dict and piexif.ImageIFD.Artist in exif_dict["0th"]:
            artist = exif_dict["0th"][piexif.ImageIFD.Artist].decode('utf-8')
            print(f"Found Artist: {artist}")
            if artist == "visual-reasoning-tool-bm":
                print("✅ Matched Artist keyword!")
                return True
        
        # Check copyright tag
        if "0th" in exif_dict and piexif.ImageIFD.Copyright in exif_dict["0th"]:
            copyright_info = exif_dict["0th"][piexif.ImageIFD.Copyright].decode('utf-8')
            print(f"Found Copyright: {copyright_info}")
            if "visual-reasoning-tool-bm" in copyright_info:
                print("✅ Matched Copyright keyword!")
                return True
        
        print("❌ No matching keywords found")
        return False
        
    except Exception as e:
        print(f"❌ Error checking image: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_image_improved.py <image_path>")
        print("Example: python check_image_improved.py my_photo.jpg")
        sys.exit(1)
    
    image_path = sys.argv[1]
    result = check_image(image_path)
    
    print("\n" + "=" * 50)
    if result:
        print("✅ This image WAS processed by visual-reasoning-tool-bm")
    else:
        print("❌ This image was NOT processed by visual-reasoning-tool-bm") 