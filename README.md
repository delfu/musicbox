# Raspberry Pi Stereo Music Player

A complete stereo music player for Raspberry Pi using MAX98357A I2S amplifiers with physical controls (buttons and rotary encoder).

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.7+-green.svg)
![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi-red.svg)

## Features

- **True Stereo Output** - Separate left/right channels using two MAX98357A amplifiers
- **Physical Controls** - Buttons for play/pause, next/previous, and rotary encoder for volume
- **USB Music Library** - Plays MP3 files from USB drive
- **Auto-start** - Optional systemd service for headless operation
- **No DAC Required** - Direct I2S digital audio output

## Hardware Requirements

### Essential Components
- 1× Raspberry Pi Zero 2 W (or any Pi with 40-pin header)
- 2× MAX98357A I2S Amplifier Breakout boards
- 2× 4Ω 3W Speakers
- 1× 210kΩ resistor (for right channel selection)
- 1× USB drive with MP3 files
- 5V 2A+ power supply

### Physical Controls (Optional)
- 3× Momentary push buttons (normally open)
- 1× Adafruit Rotary Encoder (Product 377) - 24-pulse with push button
- Jumper wires and breadboard

## Pin Connections

### I2S Audio (Both Amplifiers)
| Pi Pin | Pi GPIO | Connection | Description |
|--------|---------|------------|-------------|
| 12 | GPIO 18 | BCLK | Bit Clock (both amps) |
| 35 | GPIO 19 | LRCLK | Left/Right Clock (both amps) |
| 40 | GPIO 21 | DIN | Data Input (both amps) |
| 2,4 | 5V | VIN | Power (both amps) |
| 6,9,14,20 | GND | GND | Ground (both amps) |

### Channel Selection
- **Left Amp**: SD pin → 3.3V directly
- **Right Amp**: SD pin → 3.3V through 210kΩ resistor

### Physical Controls
| Pi Pin | Pi GPIO | Connection | Function |
|--------|---------|------------|----------|
| 11 | GPIO 17 | Button → GND | Play/Pause |
| 13 | GPIO 27 | Button → GND | Next Track |
| 15 | GPIO 22 | Button → GND | Previous Track |
| 29 | GPIO 5 | Encoder A | Volume Control |
| 31 | GPIO 6 | Encoder B | Volume Control |
| 33 | GPIO 13 | Encoder SW → GND | Reset Volume |

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/pi-music-player.git
cd pi-music-player
```

### 2. Run Setup Script
```bash
chmod +x setup.sh
./setup.sh
```
This will:
- Install all dependencies (mpg123, ALSA, GPIO libraries)
- Configure I2S audio
- Setup USB auto-mount
- Configure GPIO permissions
- Create systemd service
- Generate test scripts

### 3. Reboot
```bash
sudo reboot
```

### 4. Test Hardware
```bash
# Test audio (you should hear tones from both speakers)
./test_audio.sh

# Test buttons and encoder (press each control)
./test_gpio.py
```

### 5. Load Music
- Copy MP3 files to USB drive
- Insert USB drive into Pi
- Mount the drive:
```bash
mount-usb  # Auto-detects USB device
# OR
sudo mount /dev/sda1 /mnt/usbdrive
```

### 6. Run Music Player
```bash
python3 music_player.py
```

## Usage

### Interactive Mode
The player offers three modes:
1. **Play All** - Sequential playback of all songs
2. **Interactive** - Keyboard control with visual feedback
3. **Physical Only** - Use buttons/encoder only (for headless operation)

### Physical Controls
- **Play/Pause Button**: Toggle playback
- **Next Button**: Skip to next track
- **Previous Button**: Go to previous track
- **Rotate Encoder**: Adjust volume (2% per detent)
- **Press Encoder**: Reset volume to 80%

### Keyboard Controls (Interactive Mode)
- `n` - Next song
- `p` - Previous song
- `s` - Stop playback
- `l` - List all songs
- `+` - Volume up
- `-` - Volume down
- `1-9` - Play song by number
- `q` - Quit

## Auto-Start on Boot

Enable the music player to start automatically:
```bash
sudo systemctl enable music-player
sudo systemctl start music-player
```

Check service status:
```bash
sudo systemctl status music-player
journalctl -u music-player -f  # View logs
```

## Wiring Diagram

```
Raspberry Pi GPIO Header

     3.3V ──┐              
[1]  ●  ●  [2]  5V ──→ Amp Power
[11] ●  ●  [12] ──→ I2S BCLK
     │      
     └──→ Play/Pause
     
[13] ●  ●  [14] GND
     │
     └──→ Next
     
[15] ●  ●  [16]
     │
     └──→ Previous
     
[29] ●  ●  [30] GND
     │
     └──→ Encoder A
     
[31] ●  ●  [32]
     │
     └──→ Encoder B
     
[33] ●  ●  [34] GND
     │
     └──→ Encoder Button
     
[35] ●  ●  [36]
     │
     └──→ I2S LRCLK
     
[39] ●  ●  [40] ──→ I2S DIN
```

## File Structure

```
pi-music-player/
├── music_player.py      # Main application
├── setup.sh             # Installation script
├── test_audio.sh        # Audio test script
├── test_gpio.py         # GPIO test script
├── wiring_guide.md      # Detailed wiring instructions
├── README.md            # This file
└── LICENSE              # MIT License
```

## Troubleshooting

### No Sound
1. Check I2S is enabled: `cat /boot/config.txt | grep i2s`
2. Verify amplifier connections (especially SD pin resistor)
3. Test with: `speaker-test -c2 -t wav`
4. Check volume: `amixer set PCM 80%`

### Only One Channel Working
- Left channel only: Right amp SD pin needs 210kΩ resistor to 3.3V
- Right channel only: Left amp SD pin should connect directly to 3.3V

### Buttons/Encoder Not Working
1. Run `./test_gpio.py` to test each control
2. Check ground connections
3. Verify GPIO pins aren't used by other services
4. Ensure proper GPIO permissions: `groups | grep gpio`

### USB Drive Not Detected
```bash
# Check if drive is detected
lsblk

# Manual mount
sudo mount /dev/sda1 /mnt/usbdrive

# Check mount
df -h | grep usbdrive
```

### Service Won't Start
```bash
# Check service logs
journalctl -u music-player -n 50

# Run manually to see errors
python3 music_player.py
```

## Customization

### Change GPIO Pins
Edit `music_player.py` and modify the `setup_gpio_controls()` call:
```python
player.setup_gpio_controls(
    play_pause_pin=17,
    next_pin=27,
    prev_pin=22,
    encoder_a_pin=5,
    encoder_b_pin=6,
    encoder_sw_pin=13
)
```

### Adjust Volume Steps
In `music_player.py`, change the step parameter:
```python
self.volume_up(step=5)  # Larger steps
self.volume_down(step=1)  # Smaller steps
```

### Change Mount Point
Edit `music_player.py`:
```python
player = MusicPlayer(music_directory="/your/mount/path")
```

## Technical Details

### Why 210kΩ for Right Channel?
The MAX98357A uses SD pin voltage to select channels:
- **High** (>2.8V @ 3.3V logic) = Left channel
- **Medium** (1.4-2.8V @ 3.3V logic) = Right channel
- **Low** (<1.4V) = (Left+Right)/2

Formula: `RSMALL = 94.0 × VDDIO - 100`
- For 3.3V: 94.0 × 3.3 - 100 = 210kΩ

### I2S Configuration
The project uses "HiFiBerry DAC" device tree overlay which provides:
- 44.1kHz/48kHz sample rates
- 16/24/32-bit depth
- Stereo output

### Power Considerations
- Each MAX98357A can draw up to 2.5W
- Pi Zero 2 W draws ~150-300mA
- Recommended: 5V 2A minimum, 3A preferred

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## License

MIT License - See LICENSE file for details

## Acknowledgments

- Adafruit for excellent MAX98357A breakout boards and documentation
- Raspberry Pi Foundation for I2S implementation
- The open-source community for ALSA and GPIO libraries

## Author

Your Name - [@yourusername](https://github.com/yourusername)

## Support

If you like this project, please ⭐ it on GitHub!

For questions and support, open an issue on GitHub.
