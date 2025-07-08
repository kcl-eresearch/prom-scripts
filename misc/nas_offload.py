#!/usr/bin/python3
#
# Alternative version of offload script to run on NAS.
#
# WARNING !!!
# WARNING !!!
# WARNING !!!
# This script should not be run directly on a Prom, as it does not check for files being open.
# This is not an issue when files have already been copied using rsync.
# WARNING !!!
# WARNING !!!
# WARNING !!!

import argparse
import collections
import hashlib
import os
import subprocess
import sys
import threading
import yaml

parser = argparse.ArgumentParser()
parser.add_argument("--source_directory", required=True, help="Source directory to copy files from")
parser.add_argument("--destination_directory", required=True, help="Destination directory to copy files to")
parser.add_argument("--logs_directory", default="/data/rsync_logs", help="Directory to store rsync logs")
parser.add_argument("--ssh_user", required=True, help="SSH user for the remote server")
parser.add_argument("--ssh_host", required=True, help="SSH host for the remote server")
parser.add_argument("--ssh_key", required=True, help="Path to the SSH private key for authentication")
parser.add_argument("--file_count", type=int, default=1000, help="Maximum number of files to copy")
parser.add_argument("--batch_size", type=int, default=50, help="Number of files to copy in each batch")
parser.add_argument("--threads", type=int, default=5, help="Number of threads to use for copying files")
parser.add_argument("--min_size", type=int, default=0, help="Minimum file size in MB to consider for copying")
parser.add_argument("--dry_run", action="store_true", help="Perform a dry run without copying files")
args = parser.parse_args()

suffixes = ["fast5", "pod5", "fastq", "fastq.gz", "txt", "html", "pdf", "bam", "bam.bai", "csv", "json", "tsv", "md"]
lock_file = f"/tmp/nas_offload_lock_{hashlib.sha256(args.source_directory.encode()).hexdigest()}.yaml"

def get_files(directory):
    """Get a list of files in the directory with specified suffixes."""
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            if len(files) >= args.file_count:
                return files
            if any(filename.endswith(f".{suffix}") for suffix in suffixes):
                filepath = os.path.join(root, filename)
                if args.min_size:
                    statinfo = os.stat(filepath)
                    if statinfo.st_size < args.min_size * 1000 * 1000:
                        continue
                files.append(os.path.relpath(filepath, directory))
    return collections.deque(files)

def thread_worker():
    global files
    while files:
        to_copy = []
        while len(to_copy) < args.batch_size and files:
            to_copy.append(files.pop())

        to_copy_joined = "\n".join(to_copy)

        job_id = hashlib.sha256(to_copy_joined.encode()).hexdigest()
        job_file = f"/tmp/rsync_{job_id}.txt"

        with open(job_file, "w") as f:
            f.write(to_copy_joined)
            f.write("\n")

        command = ["/usr/bin/rsync"]

        if args.dry_run:
            command.append("-nv")

        command.extend([
            "--perms",
            "--times",
            "--rsh", f"ssh -i {args.ssh_key} -o PasswordAuthentication=no -o ControlMaster=auto -o ControlPersist=yes -o ControlPath=~/.ssh/control_rsync_%C",
            "--log-file", os.path.join(args.logs_directory, f"{job_id}.log"),
            "--files-from", job_file,
            "--remove-source-files",
            args.source_directory,
            f"{args.ssh_user}@{args.ssh_host}:{args.destination_directory}",
        ])

        print(f"Running command: {' '.join(command)}")
        #subprocess.run(command, check=True, text=True)

if os.path.exists(lock_file):
    sys.exit(f"Lock file {lock_file} exists. Another instance may be running.")

with open(lock_file, "w") as f:
    yaml.dump(vars(args), f)

try:
    files = get_files(args.source_directory)
except Exception as e:
    sys.exit(f"Error reading source directory {args.source_directory}: {e}")

threads = []
for _ in range(args.threads):
    thread = threading.Thread(target=thread_worker)
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()

os.unlink(lock_file)
