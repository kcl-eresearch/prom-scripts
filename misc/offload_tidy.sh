#!/usr/bin/bash
# Tidy up the offloaded Minknow files.
# Xand Meaden, King's College London, 2025.

source /etc/systemd/ont-platform-data-offload.conf

if [ -z "${ONT_PLATFORM_DATA_OFFLOAD_DIR}" ]; then
    echo "ONT_PLATFORM_DATA_OFFLOAD_DIR is not set. Exiting." 1>&2
    exit 1
fi

/usr/bin/find "${ONT_PLATFORM_DATA_OFFLOAD_DIR}" -type d -mtime +30 | /usr/bin/sort -r | /usr/bin/xargs rmdir -v
