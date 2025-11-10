#!/bin/bash
#
# Setup script for Raspberry Pi Stereo Music Player with MAX98357A Amplifiers
# This script installs all dependencies and configures I2S audio
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

REPO_NAME='musicbox'

# Log functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Raspberry Pi
check_raspberry_pi() {
    if [ ! -f /proc/device-tree/model ]; then
        log_error "This doesn't appear to be a Raspberry Pi!"
        read -p "Continue anyway? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        MODEL=$(cat /proc/device-tree/model)
        log_info "Detected: $MODEL"
    fi
}

# Check if running as root
check_root() {
    if [ "$EUID" -eq 0 ]; then
        log_warn "Running as root. It's recommended to run as regular user with sudo."
        read -p "Continue as root? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Update system
update_system() {
    log_info "Updating system packages..."
    sudo apt-get update
    sudo apt-get upgrade -y
}

# Install software dependencies
install_dependencies() {
    log_info "Installing software dependencies..."
    
    # Core audio tools
    sudo apt-get install -y \
        mpg123 \
        alsa-utils \
        alsa-tools
    
    # Python and GPIO libraries
    sudo apt-get install -y \
        python3 \
        python3-pip \
        python3-dev \
        swig \
        python3-setuptools
    
    # Install gpiozero - the official Raspberry Pi GPIO library
    sudo apt-get install -y python3-gpiozero python3-lgpio python3-rpi-lgpio
    # Additional useful tools
    sudo apt-get install -y \
        git \
        vim \
        htop 
    
    # packages for display
    sudo apt-get install python3-pil python3-numpy
    pip3 install --break-system-packages adafruit-circuitpython-rgb-display
    pip3 install --break-system-packages mutagen  # For MP3 metadata

    # TODO: this is only needed if we launch the player as root
    cd $HOME/$REPO_NAME && python3 -m venv venv --system-site-packages
    
    log_info "Dependencies installed successfully!"
}

# Configure I2S audio
configure_firmware() {
    log_info "Configuring I2S audio..."
    
    CONFIG_FILE="/boot/firmware/config.txt"
    BACKUP_FILE="/boot/firmware/config.txt.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Backup current config
    log_info "Backing up current config to $BACKUP_FILE"
    sudo cp $CONFIG_FILE $BACKUP_FILE
    
    # Disable onboard audio
    log_info "Disabling onboard audio..."
    sudo sed -i 's/^dtparam=audio=on/#dtparam=audio=on/g' $CONFIG_FILE
    
    # Remove any existing I2S/SPI configs to avoid duplicates
    sudo sed -i '/^dtoverlay=vc4-kms-v3d/d' $CONFIG_FILE
    sudo sed -i '/^dtparam=i2s=/d' $CONFIG_FILE
    sudo sed -i '/^dtparam=spi=/d' $CONFIG_FILE
    sudo sed -i '/^dtoverlay=max98357a/d' $CONFIG_FILE
    sudo sed -i '/^dtparam=audio/d' $CONFIG_FILE
    
    # Add I2S configuration
    log_info "Adding I2S configuration..."
    echo "" | sudo tee -a $CONFIG_FILE > /dev/null
    echo "# I2S Audio Configuration for MAX98357A" | sudo tee -a $CONFIG_FILE > /dev/null
    echo "dtparam=i2s=on" | sudo tee -a $CONFIG_FILE > /dev/null
    echo "dtparam=audio=off" | sudo tee -a $CONFIG_FILE > /dev/null
    echo "dtoverlay=max98357a" | sudo tee -a $CONFIG_FILE > /dev/null
    echo "dtoverlay=i2s-mmap" | sudo tee -a $CONFIG_FILE > /dev/null

    # Add SPI configuration
    echo "dtparam=spi=on" | sudo tee -a $CONFIG_FILE > /dev/null
    
    log_info "Firmware configuration complete!"
}

# Configure ALSA
configure_alsa() {
    log_info "Configuring ALSA..."
    
    # Create asound.conf for system-wide ALSA config
    sudo tee /etc/asound.conf > /dev/null << 'EOF'
pcm.speakerbonnet {
   type hw card 0 
}

pcm.!default { 
   type plug 
   slave.pcm "dmixer" 
}

pcm.dmixer { 
   type dmix 
   ipc_key 1024
   ipc_perm 0666
   slave { 
     pcm "speakerbonnet" 
     period_time 0
     period_size 1024
     buffer_size 8192
     rate 44100
     channels 2 
   } 
}
ctl.dmixer { 
  type hw card 0 
}
EOF

    # Set initial volume
    log_info "Setting initial volume to 80%..."
    amixer set PCM 80% 2>/dev/null || log_warn "Could not set volume. Will be available after reboot."

    sudo tee $HOME/.asoundrc > /dev/null << 'EOF'
pcm.speakerbonnet {
   type hw card 0
}

pcm.dmixer {
   type dmix
   ipc_key 1024
   ipc_perm 0666
   slave {
     pcm "speakerbonnet"
     period_time 0
     period_size 1024
     buffer_size 8192
     rate 44100
     channels 2
   }
}

ctl.dmixer {
    type hw card 0
}

pcm.softvol {
    type softvol
    slave.pcm "dmixer"
    control.name "PCM"
    control.card 0
}

ctl.softvol {
    type hw card 0
}

pcm.!default {
    type             plug
    slave.pcm       "softvol"
}
EOF

    sudo chattr +i ~/.asoundrc

    #you can set volume with amixer set PCM 80%
}

# Setup USB auto-mount
setup_usb_mount() {
    log_info "Setting up USB auto-mount..."
    
    # Create mount point
    sudo mkdir -p /mnt/usbdrive
    sudo chmod 755 /mnt/usbdrive
    
    # TODO: setup the automount udev rule and script
    sudo tee /etc/udev/rules.d/99-usbhook.rules > /dev/null << 'EOF'
ACTION=="add", SUBSYSTEM=="block", ENV{ID_BUS}=="usb", ENV{ID_FS_TYPE}!="", KERNEL=="sd*[0-9]", RUN+="/usr/bin/systemd-run --no-block /usr/local/bin/usb-automount.sh add %k"
ACTION=="remove", SUBSYSTEM=="block", ENV{ID_BUS}=="usb", ENV{ID_FS_TYPE}!="", KERNEL=="sd*[0-9]", RUN+="/usr/bin/systemd-run --no-block /usr/local/bin/usb-automount.sh remove %k"
EOF

    sudo chmod +x usb-automount.sh

    sudo cp usb-automount.sh /usr/local/bin/usb-automount.sh

    sudo udevadm control --reload-rules
    sudo udevadm trigger
    
    log_info "USB drive automounting configured!"
}

# Setup GPIO permissions
setup_gpio_permissions() {
    log_info "Setting up GPIO permissions..."
    
    # Add current user to gpio group
    sudo usermod -a -G gpio $USER
    
    # Setup udev rules for GPIO access without sudo
    sudo tee /etc/udev/rules.d/99-gpio.rules > /dev/null << 'EOF'
SUBSYSTEM=="bcm2835-gpiomem", KERNEL=="gpiomem", GROUP="gpio", MODE="0660"
SUBSYSTEM=="gpio", KERNEL=="gpiochip*", ACTION=="add", PROGRAM="/bin/sh -c 'chown root:gpio /sys/class/gpio/export /sys/class/gpio/unexport ; chmod 220 /sys/class/gpio/export /sys/class/gpio/unexport'"
SUBSYSTEM=="gpio", KERNEL=="gpio*", ACTION=="add", PROGRAM="/bin/sh -c 'chown root:gpio /sys%p/active_low /sys%p/direction /sys%p/edge /sys%p/value ; chmod 660 /sys%p/active_low /sys%p/direction /sys%p/edge /sys%p/value'"
EOF

    sudo udevadm control --reload-rules
    sudo udevadm trigger
    
    log_info "GPIO permissions configured!"
}

# Create systemd service for auto-start
# TODO: this needs testing so it's disabled from the script
create_systemd_service() {
    log_info "Creating systemd service for auto-start..."
    
    SERVICE_FILE="/etc/systemd/system/music-player.service"
    
    sudo tee $SERVICE_FILE > /dev/null << EOF
[Unit]
Description=Raspberry Pi Music Player
After=multi-user.target sound.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/$REPO_NAME
ExecStart=/usr/bin/python3 $HOME/$REPO_NAME/music_player.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    log_info "Systemd service created!"
    log_info "To enable auto-start on boot, run: sudo systemctl enable music-player"
    log_info "To start the service now, run: sudo systemctl start music-player"
}

# Create test scripts
configure_test_scripts() {
    log_info "Configuring test scripts..."
    
    # GPIO test script
    chmod +x test_gpio.py
    # Audio test script
    chmod +x test_audio.sh
    
    log_info "Test scripts created!"
}

# Print summary
print_summary() {
    echo
    echo "========================================="
    echo "      SETUP COMPLETE!"
    echo "========================================="
    echo
    echo "Next steps:"
    echo "1. Reboot your Raspberry Pi:"
    echo "   sudo reboot"
    echo
    echo "2. After reboot, test the installation:"
    echo "   ./test_audio.sh    # Test stereo audio"
    echo "   ./test_gpio.py     # Test buttons/encoder"
    echo
    echo "3. Copy MP3 files to your USB drive"
    echo
    echo "4. Mount USB drive:"
    echo "   mount-usb          # Auto-detect and mount"
    echo "   mount-usb /dev/sda1 # Specific device"
    echo
    echo "5. Run the music player:"
    echo "   python3 music_player.py"
    echo
    echo "Optional - Enable auto-start on boot:"
    echo "   sudo systemctl enable music-player"
    echo "   sudo systemctl start music-player"
    echo
    echo "GPIO Pin Connections:"
    echo "  I2S Audio:"
    echo "    - GPIO 18 → BCLK (both amps)"
    echo "    - GPIO 19 → LRCLK (both amps)"
    echo "    - GPIO 21 → DIN (both amps)"
    echo "  Controls:"
    echo "    - GPIO 17 → Play/Pause button"
    echo "    - GPIO 27 → Next button"
    echo "    - GPIO 22 → Previous button"
    echo "    - GPIO 5  → Encoder A"
    echo "    - GPIO 6  → Encoder B"
    echo "    - GPIO 13 → Encoder button"
    echo
    echo "========================================="
}

# Main installation flow
main() {
    echo "========================================="
    echo "  Raspberry Pi Music Player Setup"
    echo "  For MAX98357A I2S Amplifiers"
    echo "========================================="
    echo
    
    check_raspberry_pi
    check_root
    
    echo
    read -p "This will install packages and modify system configs. Continue? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    
    update_system
    install_dependencies
    configure_firmware
    configure_alsa 
    setup_usb_mount
    setup_gpio_permissions
    create_systemd_service # this needs more thoughts so it's disabled for now
    configure_test_scripts
    print_summary
    
    echo
    read -p "Reboot now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo reboot
    fi
}

# Run main function
main "$@"
