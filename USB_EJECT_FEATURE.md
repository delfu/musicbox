# USB Eject Feature

## Overview

The rotary encoder button now provides USB eject functionality, allowing you to safely stop playback, unmount the USB drive, and optionally cut power to the USB port.

## How It Works

### When Media is Connected and Playing

**Press the rotary encoder button** to:
1. Stop all playback immediately
2. Sync the filesystem (flush all pending writes)
3. Safely unmount the USB drive from `/mnt/usbdrive`
4. (Optional) Cut power to USB port if `uhubctl` is installed
5. Display "USB EJECTED - Safe to Remove" on screen

After ejection, the USB drive can be safely removed from the device.

### When USB is Ejected

**Press the rotary encoder button again** to:
1. Re-enable USB power (if it was disabled)
2. Allow the system to auto-mount when USB is reconnected
3. Display "Waiting for USB..." on screen
4. Resume automatic playback when media is detected

## Technical Details

### Safe Unmounting Process

1. **Stop Playback**: Terminates the mpg123 process cleanly
2. **Sync Filesystem**: Runs `sync` to ensure all writes are committed
3. **Find Device**: Automatically detects which device is mounted (e.g., `/dev/sda1`)
4. **Unmount**: Uses `sudo umount` to safely unmount the filesystem
5. **Update State**: Sets internal flag to prevent auto-remounting

### USB Power Control (Optional)

USB power control is **optional** and requires the `uhubctl` utility:

```bash
sudo apt-get install uhubctl
```

**Note:** Not all Raspberry Pi models and USB hubs support power control. If `uhubctl` is not available or not supported by your hardware, the system will still safely unmount the USB drive, which is the most important part.

#### Raspberry Pi USB Power Support

- **Raspberry Pi 4/5**: Full USB power control support via `uhubctl`
- **Raspberry Pi 3/Zero**: Limited or no USB power control
- **External USB Hubs**: Some support power control, check `uhubctl` compatibility

### Permissions

The unmount operation requires sudo permissions. Make sure the user running the music player is in the sudoers file with NOPASSWD for umount:

```bash
sudo visudo
```

Add this line (replace `pi` with your username):

```
pi ALL=(ALL) NOPASSWD: /bin/umount, /usr/bin/uhubctl
```

Or use the setup script which configures this automatically.

## User Experience Flow

### Typical Usage Scenario

1. **Playing Music**: USB is mounted, music is playing
2. **User Presses Encoder Button**: 
   - Music stops immediately
   - USB is safely unmounted
   - Display shows "USB EJECTED - Safe to Remove"
   - (Optional) USB power is cut if uhubctl is available
3. **User Removes USB Drive**: Can safely remove the physical device
4. **User Wants to Play Again**:
   - Press encoder button again to re-enable
   - Display shows "Waiting for USB..."
   - Insert USB drive
   - System auto-mounts and starts playing

### State Management

The player maintains two key states:
- `usb_ejected`: Tracks whether USB was manually ejected
- `usb_power_enabled`: Tracks whether USB power is currently on

When `usb_ejected` is `True`, the automatic media detection and playback is suspended, preventing the system from trying to access the unmounted drive.

## Safety Features

1. **Always Stops Playback First**: Ensures no files are open during unmount
2. **Filesystem Sync**: Guarantees all pending writes are completed
3. **Clean Unmount**: Uses proper unmount procedures to prevent corruption
4. **State Tracking**: Prevents race conditions during auto-remount
5. **Display Feedback**: User always knows current state

## Testing

### Manual Testing

Test the eject functionality without GPIO:

```python
from music_player import MusicPlayer
import time

player = MusicPlayer()
player.load_playlist()
player.play_file(player.playlist[0])
time.sleep(3)

# Test ejection
player.eject_usb()

# Test re-enable
time.sleep(2)
player.reenable_usb()
```

### With GPIO

Simply press the rotary encoder button while music is playing.

## Troubleshooting

### "Failed to unmount" Error

**Cause**: Files are still open or device is busy

**Solution**:
1. Stop all playback manually
2. Check for processes using the mount point: `lsof +D /mnt/usbdrive`
3. Kill any remaining processes
4. Try ejecting again

### "uhubctl not available" Message

**Cause**: uhubctl is not installed or your hardware doesn't support it

**Solution**: This is just informational. The USB will still be safely unmounted. If you want USB power control:
1. Install uhubctl: `sudo apt-get install uhubctl`
2. Check compatibility: `sudo uhubctl`
3. If not supported, ignore - unmounting is the critical operation

### USB Doesn't Auto-Mount After Re-enable

**Cause**: The udev rules may not have triggered

**Solution**:
1. Physically disconnect and reconnect the USB drive
2. Check udev rules are active: `sudo udevadm control --reload-rules`
3. Manually trigger: `sudo udevadm trigger`

## Implementation Notes

### Key Methods

- `eject_usb()`: Main ejection logic
- `reenable_usb()`: Re-enable after ejection
- `find_usb_device()`: Automatically finds mounted USB device
- `toggle_usb_power()`: Optional USB power control
- `check_uhubctl_available()`: Checks for uhubctl availability

### Integration Points

- Encoder button callback now handles eject/reenable toggle
- `wait_for_media_and_play()` respects ejection state
- Display updates show ejection status
- All playback stops before unmounting

## Future Enhancements

Possible improvements:
- Long press vs short press for different actions (e.g., long press to eject)
- Eject confirmation on display before unmounting
- LED indicator for ejection state
- Support for multiple USB drives
- Graceful degradation if sudo isn't available

