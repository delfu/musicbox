#!/bin/bash

MOUNT_POINT="/mnt/usbdrive"
DEVNAME="/dev/$2"
LOGTAG="Automount"

log() {
  /usr/bin/logger "$LOGTAG: $1"
}

case "$1" in
  add)
    log "mounting $DEVNAME to $MOUNT_POINT"
    /bin/mkdir -p "$MOUNT_POINT"

    # wait until the kernel reports the device is ready
    /bin/sleep 2

    # try to mount explicitly specifying the filesystem type (udev lacks env vars)
    /bin/mount -t auto "$DEVNAME" "$MOUNT_POINT" -o uid=pi,gid=pi >> /tmp/usb-automount.log 2>&1

    if [ $? -ne 0 ]; then
      log "failed to mount $DEVNAME (see /tmp/usb-automount.log)"
    else
      log "mounted $DEVNAME successfully"
      # Run as pi user with full environment (HOME, PATH, etc.)
      sudo -u pi -H bash -c 'cd /home/pi/musicbox && source venv/bin/activate && python music_player.py'
      log "started music player as pi user"
    fi
    ;;

  remove)
    log "killing music player"
    pkill -f 'python.*music_player\.py$'

    log "unmounting $MOUNT_POINT"
    /bin/umount "$MOUNT_POINT" >> /tmp/usb-automount.log 2>&1
    if [ $? -ne 0 ]; then
      log "failed to unmount $MOUNT_POINT (see /tmp/usb-automount.log)"
    else
      log "unmounted successfully"
    fi

    ;;
esac