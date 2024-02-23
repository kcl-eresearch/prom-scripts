#!/usr/bin/python3
# Copy sequencing reports to rsync destination
# Xand Meaden, King's College London

import datetime
import os
import psutil
import re
import sys
import subprocess
import tempfile
import yaml

RSYNC = "/usr/bin/rsync"

def file_is_open(path):
    for proc in psutil.process_iter():
        try:
            for file in proc.open_files():
                if file.path == path:
                    return True
        except: # We can only read our own processes, but this should be OK
            continue
    return False

try:
    with open("/etc/ont_rsync_reports.yaml") as fh:
        config = yaml.safe_load(fh)
except Exception as e:
    sys.exit("Failed to load config: %s" % e)

to_copy = {}

for item in os.scandir(config["source_dir"]):
    for pattern, destination in config["destination_dirs"].items():
        if destination not in to_copy:
            to_copy[destination] = []

        if re.search(pattern, item.name) and not os.path.exists("%s.copied.yaml" % item.path) and not file_is_open(item.path):
            to_copy[destination].append(item.name)

for destination, files in to_copy.items():
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as fh:
        for file in files:
            fh.write("%s\n" % file)
        copy_list = fh.name

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    result = subprocess.run(
        [
            RSYNC,
            "-a",
            "-e", "ssh -i %s" % config["ssh_private_key"],
            "--chmod=g+w",
            "--files-from=%s" % copy_list,
            "%s/" % config["source_dir"],
            "%s@%s:%s/" % (config["destination_user"], config["destination_host"], destination)
        ],
    )

    if result.returncode == 0:
        for file in files:
            copied_file = "%s/%s.copied.yaml" % (config["source_dir"], file)
            try:
                with open(copied_file, "w") as fh:
                    yaml.dump(
                        {
                            "timestamp": timestamp,
                            "destination_host": config["destination_host"],
                            "destination_path": destination
                        },
                        fh, default_flow_style=False
                    )
            except Exception as e:
                sys.stderr.write("Failed writing %s: %s\n" % (copied_file, e))

    os.unlink(copy_list)
