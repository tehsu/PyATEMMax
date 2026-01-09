#!/usr/bin/env python3
# coding: utf-8
"""
PyATEMMax example: Upload image to media pool

This example demonstrates how to upload an image to the ATEM media pool.
"""

import sys
import time
import argparse
from pathlib import Path

# Add parent directory to path to import PyATEMMax
sys.path.insert(0, str(Path(__file__).parent.parent))

import PyATEMMax


def upload_image(switcher_ip: str, image_path: str, slot: int = 0, media_player: int = None):
    """Upload an image to the ATEM media pool
    
    Args:
        switcher_ip: IP address of the ATEM switcher
        image_path: Path to the image file to upload
        slot: Media pool slot number (0-19, default 0)
        media_player: Optional media player to set (0 or 1)
    """
    
    print(f"Connecting to ATEM at {switcher_ip}...")
    
    # Create ATEM instance and connect
    switcher = PyATEMMax.ATEMMax()
    switcher.connect(switcher_ip)
    switcher.waitForConnection()
    
    if not switcher.connected:
        print("ERROR: Could not connect to ATEM switcher")
        return False
    
    print(f"Connected to: {switcher.atemModel}")
    
    # Check if media pool lock is available
    lock_id = 0  # 0 = media pool stills
    if lock_id in switcher.mediaPoolLock and switcher.mediaPoolLock[lock_id].locked:
        print(f"ERROR: Media pool lock {lock_id} is already held")
        print("Please wait for the lock to be released or use the ATEM Software Control to release it")
        switcher.disconnect()
        return False
    
    # Acquire media pool lock
    print(f"Acquiring media pool lock for slot {slot}...")
    if not switcher.acquireMediaPoolLock(lock_id, slot):
        print("ERROR: Failed to acquire media pool lock")
        switcher.disconnect()
        return False
    
    # Wait for lock to be acquired
    time.sleep(0.5)
    
    # Check if lock was acquired
    max_wait = 5
    waited = 0
    while waited < max_wait:
        if lock_id in switcher.mediaPoolLock and switcher.mediaPoolLock[lock_id].locked:
            break
        time.sleep(0.1)
        waited += 0.1
    
    if lock_id not in switcher.mediaPoolLock or not switcher.mediaPoolLock[lock_id].locked:
        print("ERROR: Lock was not acquired within timeout")
        switcher.disconnect()
        return False
    
    print("Lock acquired")
    
    # Get video format to determine resolution
    video_format = switcher.atem.videoModeFormats.byValue(switcher.videoMode.format.value)
    print(f"Video format: {video_format.name}")
    
    # Determine resolution based on video format
    # Most common formats
    resolution_map = {
        "525i59.94NTSC": (720, 486),
        "625i50PAL": (720, 576),
        "720p50": (1280, 720),
        "720p59.94": (1280, 720),
        "1080i50": (1920, 1080),
        "1080i59.94": (1920, 1080),
        "1080p23.98": (1920, 1080),
        "1080p24": (1920, 1080),
        "1080p25": (1920, 1080),
        "1080p29.97": (1920, 1080),
        "1080p50": (1920, 1080),
        "1080p59.94": (1920, 1080),
        "2160p23.98": (3840, 2160),
        "2160p24": (3840, 2160),
        "2160p25": (3840, 2160),
        "2160p29.97": (3840, 2160),
    }
    
    width, height = resolution_map.get(video_format.name, (1920, 1080))
    print(f"Target resolution: {width}x{height}")
    
    # Load and convert image
    print(f"Loading and converting image: {image_path}")
    try:
        image_data = PyATEMMax.loadAndConvertImage(image_path, width, height)
    except Exception as e:
        print(f"ERROR: Failed to load/convert image: {e}")
        switcher.releaseMediaPoolLock(lock_id)
        switcher.disconnect()
        return False
    
    print(f"Image converted ({len(image_data)} bytes)")
    
    # Upload image
    image_name = Path(image_path).stem
    print(f"Uploading '{image_name}' to slot {slot}...")
    
    try:
        transfer_id = switcher.uploadImageToMediaPool(slot, image_name, image_data)
        print(f"Upload initiated (transfer ID: {transfer_id})")
        
        # Wait for upload to complete
        max_wait = 30
        waited = 0
        while waited < max_wait:
            if not switcher.fileTransfer.transferActive:
                break
            if waited % 2 == 0:
                remaining = len(switcher.fileTransfer.transferData)
                total = len(image_data)
                percent = ((total - remaining) / total * 100) if total > 0 else 100
                print(f"Upload progress: {percent:.1f}% ({total - remaining}/{total} bytes)")
            time.sleep(0.5)
            waited += 0.5
        
        if switcher.fileTransfer.transferActive:
            print("WARNING: Upload did not complete within timeout")
        else:
            print("Upload completed successfully")
        
    except Exception as e:
        print(f"ERROR: Upload failed: {e}")
        switcher.releaseMediaPoolLock(lock_id)
        switcher.disconnect()
        return False
    
    # Set media player to use uploaded image (if requested)
    if media_player is not None and media_player in [0, 1]:
        print(f"Setting media player {media_player + 1} to still {slot}")
        switcher.setMediaPlayerSourceType(media_player, "still")
        switcher.setMediaPlayerSourceStillIndex(media_player, slot)
        time.sleep(0.2)
    
    # Release lock
    print("Releasing media pool lock...")
    switcher.releaseMediaPoolLock(lock_id)
    time.sleep(0.5)
    
    # Disconnect
    print("Disconnecting...")
    switcher.disconnect()
    
    print("Done!")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Upload an image to ATEM media pool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload image to slot 0
  python upload-image.py 192.168.1.100 image.png
  
  # Upload to slot 5
  python upload-image.py 192.168.1.100 image.jpg --slot 5
  
  # Upload and set media player 1 to use it
  python upload-image.py 192.168.1.100 image.png --media-player 1
        """
    )
    
    parser.add_argument("ip", help="ATEM switcher IP address")
    parser.add_argument("image", help="Path to image file")
    parser.add_argument("--slot", type=int, default=0, 
                       help="Media pool slot (0-19, default: 0)")
    parser.add_argument("--media-player", type=int, choices=[1, 2],
                       help="Set media player to use uploaded image (1 or 2)")
    
    args = parser.parse_args()
    
    # Validate inputs
    if not Path(args.image).exists():
        print(f"ERROR: Image file not found: {args.image}")
        sys.exit(1)
    
    if args.slot < 0 or args.slot > 19:
        print("ERROR: Slot must be between 0 and 19")
        sys.exit(1)
    
    # Convert media player number to 0-based index
    media_player = args.media_player - 1 if args.media_player else None
    
    # Upload image
    success = upload_image(args.ip, args.image, args.slot, media_player)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
