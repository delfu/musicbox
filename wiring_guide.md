# AMP (right)

VIN -> 2 (5V)
GND -> GND
SD -> 220k resistor -> 3.3v
DIN -> 40 (GPIO 21)
BCLK -> 12 (GPIO 18)
LRC -> 35 (GPIO 19)

# AMP (LEFT)

VIN -> 2 (5V)
GND -> GND
SD -> 3.3v
DIN -> 40
BCLK -> 12
LRC -> 35

# Screen

IM1 -> IM2 -> IM3 -> ? 3.3?
RST -> 18
D/C -> 22
CS -> GND
MOSI -> 19
CLK -> 23
VIN -> 2 (5V)
GND -> GND

# BUTTONS

COMMON -> GND
11 (play/pause)
13 (next)
15 (previous)

# Rotary encoder (volume knob)

LEFT PIN -> 31
MIDDLE -> GND
RIGHT PIN -> 29

for clicking: (two pins on the other side)
LEFT_PIN -> 33
RIGHT_PIN -> GND
