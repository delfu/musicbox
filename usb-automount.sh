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
    fi
    ;;

  remove)
    log "unmounting $MOUNT_POINT"
    /bin/umount "$MOUNT_POINT" >> /tmp/usb-automount.log 2>&1
    if [ $? -ne 0 ]; then
      log "failed to unmount $MOUNT_POINT (see /tmp/usb-automount.log)"
    else
      log "unmounted successfully"
    fi
    ;;
esac