# GPIO Migration to gpiozero

This document describes the migration from `RPi.GPIO` (via `rpi-lgpio`) to the officially supported `gpiozero` library.

## Summary of Changes

### 1. Setup Script (`setup.sh`)

**Before:**

```bash
sudo apt remove -y python3-rpi.gpio
pip3 install --break-system-packages rpi-lgpio
```

**After:**

```bash
sudo apt-get install -y python3-gpiozero python3-lgpio
```

### 2. Main Music Player (`music_player.py`)

#### Import Changes

**Before:**

```python
import RPi.GPIO as GPIO
```

**After:**

```python
from gpiozero import Button, RotaryEncoder
```

#### GPIO Setup Changes

**Before:**

- Manual `GPIO.setmode(GPIO.BCM)`
- Manual `GPIO.setup()` for each pin
- Manual event detection with `GPIO.add_event_detect()`
- Custom threading for encoder quadrature decoding

**After:**

- Simple object instantiation with built-in pull-ups
- Automatic cleanup (no need for `GPIO.cleanup()`)
- Built-in quadrature decoding in `RotaryEncoder`
- Callback-based event handling

#### Key Benefits

1. **Simpler Code**: Buttons and encoders are now single-line instantiations
2. **Built-in Debouncing**: `bounce_time` parameter handles debouncing automatically
3. **Automatic Cleanup**: No need to call `GPIO.cleanup()` manually
4. **Better Encoder Support**: `RotaryEncoder` class handles quadrature decoding automatically
5. **More Pythonic**: Object-oriented interface with properties and callbacks

### 3. Test Scripts

Both `test_gpio.py` and `test_encoder.py` have been updated to use gpiozero:

- Callback-based architecture instead of polling
- Cleaner, more readable code
- Automatic resource management

## Pin Configuration

All pins remain the same:

- **GPIO 17**: Play/Pause button
- **GPIO 27**: Next button
- **GPIO 22**: Previous button
- **GPIO 5**: Encoder A (CLK)
- **GPIO 6**: Encoder B (DT)
- **GPIO 13**: Encoder button

## Usage Notes

### Button Initialization

```python
button = Button(pin_number, pull_up=True, bounce_time=0.2)
button.when_pressed = callback_function
```

### Rotary Encoder Initialization

```python
encoder = RotaryEncoder(a_pin, b_pin, bounce_time=0.001, max_steps=100)
encoder.when_rotated_clockwise = cw_callback
encoder.when_rotated_counter_clockwise = ccw_callback
```

### Callback Functions

- gpiozero callbacks don't receive a channel parameter
- Simply define: `def callback():` instead of `def callback(channel):`

## Installation on Raspberry Pi

### Option 1: Using setup.sh (Recommended)

After pulling these changes, run:

```bash
./setup.sh
```

This will install `python3-gpiozero` and `python3-lgpio` from the Debian/Raspbian repositories.

### Option 2: Manual Installation

#### If NOT using a virtual environment:

```bash
sudo apt-get install -y python3-gpiozero python3-lgpio
```

#### If using a virtual environment (venv):

```bash
# Activate your venv first
source venv/bin/activate

# Install via pip
pip install gpiozero rpi-lgpio

# Or use requirements.txt
pip install -r requirements.txt
```

**Important:** The `rpi-lgpio` package provides the `lgpio` backend that gpiozero needs to communicate with GPIO pins. Without it, gpiozero will fall back to less reliable backends or fail.

## Backward Compatibility

The migration completely replaces RPi.GPIO usage. If you need to roll back:

1. Install the old dependencies:

   ```bash
   sudo apt remove -y python3-rpi.gpio
   pip3 install --break-system-packages rpi-lgpio
   ```

2. Revert the Python files to use `import RPi.GPIO as GPIO`

## References

- [gpiozero Documentation](https://gpiozero.readthedocs.io/)
- [gpiozero Recipes](https://gpiozero.readthedocs.io/en/stable/recipes.html)
- [RotaryEncoder API](https://gpiozero.readthedocs.io/en/stable/api_input.html#rotaryencoder)
