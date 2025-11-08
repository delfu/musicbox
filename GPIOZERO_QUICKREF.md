# gpiozero Quick Reference

## Advantages Over RPi.GPIO

1. **Simpler API**: More intuitive, object-oriented design
2. **Automatic Cleanup**: Resources are managed automatically
3. **Built-in Debouncing**: No need for manual debounce logic
4. **Better Abstractions**: Higher-level components like `RotaryEncoder`, `Motor`, etc.
5. **Official Support**: Maintained by the Raspberry Pi Foundation
6. **Better Documentation**: Excellent docs and examples

## Common Patterns

### Button

```python
from gpiozero import Button

# Create button (active-low with pull-up)
button = Button(17, pull_up=True, bounce_time=0.2)

# Callback when pressed
button.when_pressed = lambda: print("Pressed!")

# Callback when released
button.when_released = lambda: print("Released!")

# Check state
if button.is_pressed:
    print("Button is currently pressed")

# Wait for press (blocking)
button.wait_for_press()
```

### Rotary Encoder

```python
from gpiozero import RotaryEncoder

# Create encoder
encoder = RotaryEncoder(5, 6, bounce_time=0.001, max_steps=100)

# Callbacks
encoder.when_rotated_clockwise = lambda: print("CW")
encoder.when_rotated_counter_clockwise = lambda: print("CCW")

# Read steps
print(f"Steps: {encoder.steps}")

# Reset
encoder.steps = 0
```

### LED (Output)

```python
from gpiozero import LED

led = LED(18)
led.on()
led.off()
led.toggle()
led.blink()  # Blink forever
led.blink(on_time=1, off_time=0.5, n=5)  # Blink 5 times
```

### PWM (Dimming/Motor Speed)

```python
from gpiozero import PWMLED, Motor

# Dimmable LED
led = PWMLED(18)
led.value = 0.5  # 50% brightness
led.pulse()  # Fade in/out

# Motor control
motor = Motor(forward=17, backward=18)
motor.forward(speed=0.5)
motor.backward(speed=0.3)
motor.stop()
```

## Pin Numbering

gpiozero uses **BCM numbering by default** (GPIO numbers, not physical pin numbers).

```python
# GPIO 17 (not physical pin 17!)
button = Button(17)
```

To use physical pin numbering:

```python
from gpiozero import Device
from gpiozero.pins.native import NativeFactory

Device.pin_factory = NativeFactory()
```

## Pull-up/Pull-down Resistors

```python
# Pull-up (default for Button)
button = Button(17, pull_up=True)

# Pull-down
button = Button(17, pull_up=False)

# No pull resistor (external resistor required)
button = Button(17, pull_up=None)
```

## Debouncing

All input devices support `bounce_time` parameter (in seconds):

```python
# 200ms debounce
button = Button(17, bounce_time=0.2)

# 1ms debounce (for encoders)
encoder = RotaryEncoder(5, 6, bounce_time=0.001)
```

## Event Callbacks

All callbacks are simple functions with no parameters:

```python
def my_callback():
    print("Event triggered!")

button.when_pressed = my_callback

# Or use lambda
button.when_pressed = lambda: print("Pressed!")
```

## Cleanup

**No explicit cleanup needed!** gpiozero handles it automatically.

However, you can manually close if needed:

```python
button.close()
encoder.close()
```

## Common Gotchas

1. **Callbacks don't receive parameters**: Unlike RPi.GPIO, callbacks don't get a channel argument
   ```python
   # ❌ Wrong (RPi.GPIO style)
   def callback(channel):
       print(f"Pin {channel} triggered")
   
   # ✅ Correct (gpiozero style)
   def callback():
       print("Button pressed")
   ```

2. **Active High vs Active Low**: By default, `Button` expects active-low (pulled to ground when pressed)
   ```python
   # Most buttons: active-low with pull-up
   button = Button(17, pull_up=True)  # Default
   
   # Some sensors: active-high
   sensor = Button(17, pull_up=False, active_state=True)
   ```

3. **Encoder Direction**: If your encoder rotates "backwards", swap A and B pins
   ```python
   # If CW gives CCW events, swap the pins
   encoder = RotaryEncoder(6, 5)  # Swapped from (5, 6)
   ```

## Composite Devices

gpiozero supports composite devices:

```python
from gpiozero import Robot, DistanceSensor

# Robot with two motors
robot = Robot(left=(17, 18), right=(22, 23))
robot.forward()
robot.right()

# Ultrasonic distance sensor
sensor = DistanceSensor(echo=24, trigger=23)
print(f"Distance: {sensor.distance * 100} cm")
```

## Best Practices

1. **Use context managers** for automatic cleanup:
   ```python
   with Button(17) as button:
       button.wait_for_press()
   ```

2. **Use descriptive names**:
   ```python
   play_button = Button(17)
   volume_encoder = RotaryEncoder(5, 6)
   ```

3. **Keep callbacks short**: Long-running callbacks can miss events
   ```python
   # ❌ Bad: blocks other events
   def callback():
       time.sleep(5)
   
   # ✅ Good: quick and non-blocking
   def callback():
       threading.Thread(target=long_task).start()
   ```

4. **Set appropriate bounce times**:
   - Buttons: 0.05-0.2 seconds
   - Encoders: 0.001-0.01 seconds
   - Switches: 0.01-0.05 seconds

## Useful Links

- [Official Documentation](https://gpiozero.readthedocs.io/)
- [Recipe Book](https://gpiozero.readthedocs.io/en/stable/recipes.html)
- [API Reference](https://gpiozero.readthedocs.io/en/stable/api_input.html)
- [Migration Guide](https://gpiozero.readthedocs.io/en/stable/migrating_from_rpigpio.html)

