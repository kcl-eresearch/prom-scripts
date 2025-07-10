#!/usr/bin/bash
# Tidy up the offloaded Minknow files.
# Xand Meaden, King's College London, 2025.

source /etc/systemd/ont-platform-data-offload.conf

if [ -z "${SOURCE_DIR}" ]; then
    echo "SOURCE_DIR is not set. Exiting." 1>&2
    exit 1
fi

/usr/bin/find "${SOURCE_DIR}" -type d -mtime +30 | /usr/bin/sort -r | /usr/bin/xargs rmdir -v
