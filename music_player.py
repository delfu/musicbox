#!/usr/bin/env python3
"""
MP3 Player for Raspberry Pi with MAX98357A I2S Amplifiers
Plays MP3 files from USB-mounted SD card at /mnt/usbdrive
Supports physical buttons and volume control
"""

import os
import time
import subprocess
from pathlib import Path
from typing import List, Optional, Callable
import signal
import sys
import threading
from enum import Enum
import argparse

from music_display import MusicDisplay

try:
    from gpiozero import Button, RotaryEncoder
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("Warning: gpiozero not available - physical controls disabled")

class PlayerState(Enum):
    """Player state enumeration"""
    STOPPED = 0
    PLAYING = 1
    PAUSED = 2

class MusicPlayer:
    def __init__(self, display_enabled: bool = True, music_directory: str = "/mnt/usbdrive"):
        """
        Initialize the music player
        
        Args:
            music_directory: Directory where USB drive is mounted
        """
        self.music_directory = music_directory
        self.current_process = None
        self.playlist = []
        self.current_index = 0
        self.state = PlayerState.STOPPED
        self.display = None
        self.volume = 30  
        self.set_volume(30) # Volume percentage (0-100)
        if display_enabled:
            try:
                self.display = MusicDisplay(270)
                self.display.show_splash()
            except Exception as e:
                print(f"Display initialization failed: {e}")
                self.display = None

        
        # Threading for physical controls
        self.control_thread = None
        self.running = True
        
        # Callback functions for physical controls
        self.button_callbacks = {}
        
        # Setup signal handlers for clean exit
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)
        
    def find_music_files(self) -> List[str]:
        """
        Find all MP3 files in /mnt/usbdrive
        
        Returns:
            List of paths to MP3 files
        """
        mp3_files = []
        
        if not os.path.exists(self.music_directory):
            print(f"Mount point {self.music_directory} does not exist!")
            print("Create it with: sudo mkdir -p /mnt/usbdrive")
            print("Mount USB with: sudo mount /dev/sda1 /mnt/usbdrive")
            return []
        
        # Search for MP3 files
        for root, dirs, files in os.walk(self.music_directory):
            for file in files:
                if file.lower().endswith('.mp3') and not file.lower().startswith("._"):
                    full_path = os.path.join(root, file)
                    mp3_files.append(full_path)
                    
        return sorted(mp3_files)

    def update_display(self):
        current = self.playlist[self.current_index] if self.playlist else ""
        if self.display:
            print("display: updating now playing", current, self.state.name)
            self.display.update_now_playing(
                current,
                state=self.state.name,
                volume=self.volume,
                current_index=self.current_index,
                total_tracks=len(self.playlist)
            )
    
    def set_volume(self, volume: int):
        """
        Set system volume (0-100)
        
        Args:
            volume: Volume percentage
        """
        self.volume = max(0, min(100, volume))
        try:
            # Use amixer to set volume
            subprocess.run(
                ['amixer', 'set', 'PCM', f'{self.volume}%'],
                capture_output=True,
                check=False
            )
            print(f"Volume: {self.volume}%")
            self.update_display()
        except Exception as e:
            print(f"Error setting volume: {e}")
    
    def volume_up(self, step: int = 5):
        """Increase volume by step"""
        self.set_volume(self.volume + step)
    
    def volume_down(self, step: int = 5):
        """Decrease volume by step"""
        self.set_volume(self.volume - step)
    
    def play_file(self, filepath: str):
        """
        Play a single MP3 file using mpg123
        
        Args:
            filepath: Path to the MP3 file
        """
        if self.current_process:
            self.stop()
            
        print(f"Playing: {os.path.basename(filepath)}")
        
        try:
            # Use mpg123 for playback
            self.current_process = subprocess.Popen(
                ['mpg123', '-q', filepath],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.state = PlayerState.PLAYING
            self.update_display()
            
        except FileNotFoundError:
            print("Error: mpg123 not found. Install it with: sudo apt-get install mpg123")
            self.state = PlayerState.STOPPED
        except Exception as e:
            print(f"Error playing file: {e}")
            self.state = PlayerState.STOPPED
    
    def stop(self):
        """Stop current playback"""
        if self.current_process:
            self.current_process.terminate()
            try:
                self.current_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.current_process.kill()
            self.current_process = None
            self.state = PlayerState.STOPPED
            print("Playback stopped")
    
    def play_next(self):
        """Play next song in playlist"""
        if self.playlist:
            self.current_index = (self.current_index + 1) % len(self.playlist)
            self.play_file(self.playlist[self.current_index])
    
    def play_previous(self):
        """Play previous song in playlist"""
        if self.playlist:
            self.current_index = (self.current_index - 1) % len(self.playlist)
            self.play_file(self.playlist[self.current_index])
    
    def load_playlist(self):
        """Load all MP3 files from /mnt/usbdrive into playlist"""
        print(f"Loading music from: {self.music_directory}")
        
        # Find all MP3 files
        self.playlist = self.find_music_files()
        
        if not self.playlist:
            print(f"No MP3 files found in {self.music_directory}")
            return False
        
        print(f"Found {len(self.playlist)} MP3 files")
        for i, song in enumerate(self.playlist[:5], 1):  # Show first 5
            print(f"  {i}. {os.path.basename(song)}")
        if len(self.playlist) > 5:
            print(f"  ... and {len(self.playlist) - 5} more")
        
        return True
    
    def is_process_running(self):
        """Check if the current playback process is still running"""
        if self.current_process:
            return self.current_process.poll() is None
        return False
    
    def play_all(self):
        """Play all songs in playlist sequentially"""
        if not self.playlist:
            if not self.load_playlist():
                return
        
        print(f"\nPlaying {len(self.playlist)} songs...")
        print("Press Ctrl+C to stop\n")
        
        for i, song in enumerate(self.playlist):
            self.current_index = i
            self.play_file(song)
            
            # Wait for current song to finish
            while self.is_process_running():
                time.sleep(0.5)
            
            # Small gap between songs
            time.sleep(0.5)
    
    def interactive_mode(self):
        """Run interactive mode with keyboard controls"""
        if not self.playlist:
            if not self.load_playlist():
                return
        
        print("\n=== Music Player Controls ===")
        print("  n - Next song")
        print("  p - Previous song") 
        print("  s - Stop playback")
        print("  l - List all songs")
        print("  + - Volume up")
        print("  - - Volume down")
        print("  [1-9] - Play song by number")
        print("  q - Quit")
        print("=============================\n")
        
        
        # Start playing first song
        self.play_file(self.playlist[0])
        
        while True:
            # Check if current song finished
            if not self.is_process_running() and self.state == PlayerState.PLAYING:
                self.play_next()
            
            # Non-blocking input check
            try:
                import select
                import sys
                
                # Check if input is available
                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    command = input().strip().lower()
                    
                    if command == 'q':
                        break
                    elif command == 'n':
                        self.play_next()
                    elif command == 'p':
                        self.play_previous()
                    elif command == 's':
                        self.stop()
                    elif command == 'l':
                        self.list_songs()
                    elif command == '+':
                        self.volume_up()
                    elif command == '-':
                        self.volume_down()
                    elif command.isdigit():
                        index = int(command) - 1
                        if 0 <= index < len(self.playlist):
                            self.current_index = index
                            self.play_file(self.playlist[self.current_index])
                        else:
                            print(f"Invalid song number (1-{len(self.playlist)})")
            except:
                pass
            
            time.sleep(0.1)
    
    def list_songs(self):
        """List all songs in playlist"""
        print("\n=== Playlist ===")
        for i, song in enumerate(self.playlist, 1):
            name = os.path.basename(song)
            if i == self.current_index + 1:
                print(f"  ▶ {i}. {name}")
            else:
                print(f"    {i}. {name}")
        print("================\n")
    
    def cleanup(self, signum=None, frame=None):
        """Clean up on exit"""
        print("\nShutting down...")
        self.running = False
        self.stop()
        if self.display:
            self.display.cleanup()
        # gpiozero handles cleanup automatically, no explicit cleanup needed
        sys.exit(0)
    
    # ==================== GPIO CONTROL METHODS ====================
    
    def setup_gpio_controls(self, 
                           play_pause_pin: int = 27,
                           next_pin: int = 17,
                           prev_pin: int = 22,
                           encoder_a_pin: int = 6,
                           encoder_b_pin: int = 5,
                           encoder_sw_pin: int = 13,
                           debounce_time: float = 0.2):
        """
        Setup GPIO pins for physical controls using gpiozero
        
        Args:
            play_pause_pin: GPIO pin for play/pause button
            next_pin: GPIO pin for next track button  
            prev_pin: GPIO pin for previous track button
            encoder_a_pin: GPIO pin for rotary encoder A signal
            encoder_b_pin: GPIO pin for rotary encoder B signal
            encoder_sw_pin: GPIO pin for rotary encoder push button
            debounce_time: Debounce time in seconds (default 0.2s)
        """
        if not GPIO_AVAILABLE:
            print("GPIO not available - physical controls disabled")
            return False
        
        print("Setting up GPIO controls with gpiozero...")
        
        # Setup buttons with pull-up resistors (active-low)
        # gpiozero Button uses pull_up=True by default, which is what we want
        self.play_pause_button = Button(play_pause_pin, pull_up=True, bounce_time=debounce_time)
        self.next_button = Button(next_pin, pull_up=True, bounce_time=debounce_time)
        self.prev_button = Button(prev_pin, pull_up=True, bounce_time=debounce_time)
        self.encoder_button = Button(encoder_sw_pin, pull_up=True, bounce_time=debounce_time)
        
        # Setup rotary encoder for volume control
        # RotaryEncoder handles A and B pins automatically with proper quadrature decoding
        self.encoder = RotaryEncoder(encoder_a_pin, encoder_b_pin, bounce_time=0.001, max_steps=100)
        
        # Setup button callbacks
        self.play_pause_button.when_pressed = self._play_pause_callback
        self.next_button.when_pressed = lambda: self.play_next()
        self.prev_button.when_pressed = lambda: self.play_previous()
        self.encoder_button.when_pressed = self._encoder_button_callback
        
        # Setup encoder callback for volume control
        self.encoder.when_rotated_clockwise = lambda: self.volume_up(step=2)
        self.encoder.when_rotated_counter_clockwise = lambda: self.volume_down(step=2)
        
        print("GPIO controls ready!")
        print("  • Play/Pause button on GPIO", play_pause_pin)
        print("  • Next button on GPIO", next_pin)
        print("  • Previous button on GPIO", prev_pin)
        print("  • Encoder A pin connected to GPIO", encoder_a_pin)
        print("  • Encoder B pin connected to GPIO", encoder_b_pin)
        print("  • Encoder button connected to GPIO", encoder_sw_pin)
        return True
    
    def _encoder_button_callback(self):
        """Handle encoder push button press - toggle mute or reset volume"""
        print("Encoder button pressed - resetting volume to 80%")
        self.set_volume(self.volume)
    
    def _play_pause_callback(self):
        """Handle play/pause button press"""
        if self.state == PlayerState.PLAYING:
            self.pause()
        elif self.state == PlayerState.PAUSED:
            self.resume()
        else:
            if self.playlist:
                self.play_file(self.playlist[self.current_index])
    
    def pause(self):
        """Pause playback"""
        if self.current_process and self.state == PlayerState.PLAYING:
            try:
                self.current_process.send_signal(signal.SIGSTOP)
                self.state = PlayerState.PAUSED
                self.update_display()
                print("Paused")
            except:
                pass
    
    def resume(self):
        """Resume playback"""
        if self.current_process and self.state == PlayerState.PAUSED:
            try:
                self.current_process.send_signal(signal.SIGCONT)
                self.state = PlayerState.PLAYING
                self.update_display()
                print("Resumed")
            except:
                pass

def main():
    """Main entry point"""
    print("=================================")
    print("  Raspberry Pi MP3 Player")
    print("  For MAX98357A I2S Amplifiers")
    print("=================================\n")

    parser = argparse.ArgumentParser(
                    prog='MusicPlayer',
                    description='A Raspberrypi based music player')
    parser.add_argument('-i', '--interactive', help='load up in interactive mode, using keyboard', action=argparse.BooleanOptionalAction)
    args = parser.parse_args()

    keyboard_mode = args.interactive

    # Check if running on Raspberry Pi
    is_pi = os.path.exists('/proc/device-tree/model')
    if not is_pi:
        print("Warning: Not running on Raspberry Pi?")
    
    # Create player instance
    player = MusicPlayer()
    
    # Setup GPIO controls if on Pi
    if is_pi and GPIO_AVAILABLE:
        player.setup_gpio_controls()
    
    # Load playlist from USB
    if not player.load_playlist():
        print("\nNo music found. Make sure:")
        print("  1. USB drive is connected")
        print("  2. Drive is mounted at /mnt/usbdrive")
        print("  3. MP3 files are present")
        print("\nTo mount manually:")
        print("  sudo mkdir -p /mnt/usbdrive")
        print("  sudo mount /dev/sda1 /mnt/usbdrive")
        return
     
    try:
        if keyboard_mode:
            player.interactive_mode()
        elif GPIO_AVAILABLE:
            print("\nPhysical control mode active")
            print("Use buttons/knobs to control playback")
            print("Press Ctrl+C to exit\n")
            player.play_file(player.playlist[0])
            # Keep running
            while True:
                if not player.is_process_running() and player.state == PlayerState.PLAYING:
                    player.play_next()
                time.sleep(0.5)
        else:
            print("Invalid choice")
    except KeyboardInterrupt:
        pass
    finally:
        player.cleanup()


if __name__ == "__main__":
    main()
