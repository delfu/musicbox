#!/usr/bin/env python3
"""
Test script for USB eject functionality
Demonstrates the USB eject/reenable feature without requiring GPIO
"""

import time
import sys
from music_player import MusicPlayer

def main():
    print("=" * 50)
    print("USB Eject Feature Test")
    print("=" * 50)
    print()
    
    # Create player instance (no display for testing)
    player = MusicPlayer(display_enabled=False)
    
    # Check if USB is mounted and has media
    print("Checking for media...")
    if not player.is_media_available():
        print("✗ No media found at", player.music_directory)
        print("\nPlease ensure:")
        print("  1. USB drive is connected")
        print("  2. Drive is mounted at /mnt/usbdrive")
        print("  3. MP3 files are present on the drive")
        return 1
    
    print("✓ Media found!")
    
    # Load playlist
    print("\nLoading playlist...")
    if not player.load_playlist():
        print("✗ Failed to load playlist")
        return 1
    
    print(f"✓ Loaded {len(player.playlist)} tracks")
    
    # Start playing
    print("\nStarting playback...")
    player.play_file(player.playlist[0])
    print(f"♪ Playing: {player.playlist[0]}")
    
    # Let it play for a few seconds
    print("\nPlaying for 3 seconds...")
    for i in range(3):
        time.sleep(1)
        print(f"  {i+1}...")
    
    # Test ejection
    print("\n" + "=" * 50)
    print("TESTING USB EJECTION")
    print("=" * 50)
    
    success = player.eject_usb()
    
    if success:
        print("\n✓ USB ejected successfully!")
        print("  • Playback stopped")
        print("  • Filesystem synced")
        print("  • USB drive unmounted")
        print("  • Safe to remove drive")
        
        # Wait a moment
        print("\nWaiting 3 seconds...")
        time.sleep(3)
        
        # Test re-enable
        print("\n" + "=" * 50)
        print("TESTING USB RE-ENABLE")
        print("=" * 50)
        
        player.reenable_usb()
        print("\n✓ USB re-enabled!")
        print("  • Ready for auto-mount")
        print("  • Will auto-play when USB is reconnected")
        
    else:
        print("\n✗ USB ejection failed")
        print("Check error messages above")
        return 1
    
    print("\n" + "=" * 50)
    print("Test completed successfully!")
    print("=" * 50)
    
    # Cleanup
    player.cleanup()
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

