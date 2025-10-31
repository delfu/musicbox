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

# GPIO will be imported only if running on Pi
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("Warning: RPi.GPIO not available - physical controls disabled")

class PlayerState(Enum):
    """Player state enumeration"""
    STOPPED = 0
    PLAYING = 1
    PAUSED = 2

class MusicPlayer:
    def __init__(self, music_directory: str = "/mnt/usbdrive"):
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
        self.volume = 80  # Volume percentage (0-100)
        
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
        
        # Set initial volume
        self.set_volume(self.volume)
        
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
        if GPIO_AVAILABLE:
            GPIO.cleanup()
        sys.exit(0)
    
    # ==================== GPIO CONTROL METHODS ====================
    
    def setup_gpio_controls(self, 
                           play_pause_pin: int = 17,
                           next_pin: int = 27,
                           prev_pin: int = 22,
                           encoder_a_pin: int = 5,
                           encoder_b_pin: int = 6,
                           encoder_sw_pin: int = 13,
                           debounce_ms: int = 200):
        """
        Setup GPIO pins for physical controls
        
        Args:
            play_pause_pin: GPIO pin for play/pause button
            next_pin: GPIO pin for next track button  
            prev_pin: GPIO pin for previous track button
            encoder_a_pin: GPIO pin for rotary encoder A signal
            encoder_b_pin: GPIO pin for rotary encoder B signal
            encoder_sw_pin: GPIO pin for rotary encoder push button
            debounce_ms: Debounce time in milliseconds
        """
        if not GPIO_AVAILABLE:
            print("GPIO not available - physical controls disabled")
            return False
        
        print("Setting up GPIO controls...")
        
        # Use BCM pin numbering
        GPIO.setmode(GPIO.BCM)
        
        # Setup button pins with pull-up resistors
        GPIO.setup(play_pause_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(next_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(prev_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Setup rotary encoder pins (Adafruit 377)
        GPIO.setup(encoder_a_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(encoder_b_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(encoder_sw_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Store pins
        self.pins = {
            'play_pause': play_pause_pin,
            'next': next_pin,
            'prev': prev_pin,
            'encoder_a': encoder_a_pin,
            'encoder_b': encoder_b_pin,
            'encoder_sw': encoder_sw_pin
        }
        
        # Setup button callbacks (falling edge = button pressed)
        GPIO.add_event_detect(play_pause_pin, GPIO.FALLING, 
                             callback=self._play_pause_callback, 
                             bouncetime=debounce_ms)
        
        GPIO.add_event_detect(next_pin, GPIO.FALLING,
                             callback=lambda ch: self.play_next(),
                             bouncetime=debounce_ms)
        
        GPIO.add_event_detect(prev_pin, GPIO.FALLING,
                             callback=lambda ch: self.play_previous(),
                             bouncetime=debounce_ms)
        
        # Setup encoder button callback
        GPIO.add_event_detect(encoder_sw_pin, GPIO.FALLING,
                             callback=self._encoder_button_callback,
                             bouncetime=debounce_ms)
        
        # Start volume control thread for rotary encoder
        self.last_a_state = GPIO.input(encoder_a_pin)
        self.control_thread = threading.Thread(target=self._volume_control_thread)
        self.control_thread.daemon = True
        self.control_thread.start()
        
        print("GPIO controls ready!")
        print("  • Encoder A pin connected to GPIO", encoder_a_pin)
        print("  • Encoder B pin connected to GPIO", encoder_b_pin)
        print("  • Encoder button connected to GPIO", encoder_sw_pin)
        return True
    
    def _encoder_button_callback(self, channel):
        """Handle encoder push button press - toggle mute or reset volume"""
        print("Encoder button pressed - resetting volume to 80%")
        self.set_volume(80)
    
    def _play_pause_callback(self, channel):
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
                print("Paused")
            except:
                pass
    
    def resume(self):
        """Resume playback"""
        if self.current_process and self.state == PlayerState.PAUSED:
            try:
                self.current_process.send_signal(signal.SIGCONT)
                self.state = PlayerState.PLAYING
                print("Resumed")
            except:
                pass
    
    def _volume_control_thread(self):
        """Thread to monitor rotary encoder for volume control"""
        if not GPIO_AVAILABLE:
            return
            
        a_pin = self.pins['encoder_a']
        b_pin = self.pins['encoder_b']
        
        while self.running:
            try:
                a_state = GPIO.input(a_pin)
                
                if a_state != self.last_a_state:
                    b_state = GPIO.input(b_pin)
                    
                    # Determine rotation direction based on A and B signals
                    if b_state != a_state:
                        self.volume_up(step=2)
                    else:
                        self.volume_down(step=2)
                    
                    self.last_a_state = a_state
                
                time.sleep(0.001)  # Small delay to prevent CPU hogging
            except:
                pass


def main():
    """Main entry point"""
    print("=================================")
    print("  Raspberry Pi MP3 Player")
    print("  For MAX98357A I2S Amplifiers")
    print("=================================\n")
    
    # Check if running on Raspberry Pi
    is_pi = os.path.exists('/proc/device-tree/model')
    if not is_pi:
        print("Warning: Not running on Raspberry Pi?")
    
    # Create player instance
    player = MusicPlayer()
    
    # Setup GPIO controls if on Pi
    if is_pi and GPIO_AVAILABLE:
        print("\nEnable physical controls? (y/n): ", end="")
        if input().strip().lower() == 'y':
            player.setup_gpio_controls()
            print("\nPhysical controls enabled:")
            print("  • Play/Pause button: GPIO 17")
            print("  • Next button: GPIO 27")
            print("  • Previous button: GPIO 22")
            print("  • Volume encoder A: GPIO 5")
            print("  • Volume encoder B: GPIO 6")
            print("  • Encoder button: GPIO 13")
    
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
    
    # Choose mode
    print("\nSelect mode:")
    print("  1. Play all songs")
    print("  2. Interactive mode (keyboard control)")
    if GPIO_AVAILABLE:
        print("  3. Physical controls only (no keyboard)")
    
    try:
        choice = input("\nEnter choice: ").strip()
        
        if choice == '1':
            player.play_all()
        elif choice == '2':
            player.interactive_mode()
        elif choice == '3' and GPIO_AVAILABLE:
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
