#!/bin/bash
# Clean up stale LittleFS mount points

MOUNT_BASE="/tmp/littlefs_mounts"

echo "Cleaning up stale LittleFS mounts..."
echo ""

if [ ! -d "$MOUNT_BASE" ]; then
    echo "No mount directory found at $MOUNT_BASE"
    exit 0
fi

cleaned=0
for mount_point in "$MOUNT_BASE"/*; do
    if [ -d "$mount_point" ]; then
        echo "Cleaning: $mount_point"

        # Try to unmount
        fusermount -uz "$mount_point" 2>/dev/null || umount -l "$mount_point" 2>/dev/null || true

        # Remove directory
        rm -rf "$mount_point"

        if [ ! -e "$mount_point" ]; then
            echo "  ✓ Cleaned successfully"
            cleaned=$((cleaned + 1))
        else
            echo "  ✗ Failed to clean (may need sudo)"
        fi
    fi
done

echo ""
echo "Cleaned $cleaned mount point(s)"
