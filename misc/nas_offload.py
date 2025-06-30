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
import os
import subprocess
import sys
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument("--source_directory", required=True, help="Source directory to copy files from")
parser.add_argument("--destination_directory", required=True, help="Destination directory to copy files to")
parser.add_argument("--logs_directory", default="/data/rsync_logs", help="Directory to store rsync logs")
parser.add_argument("--chunk_size", type=int, default=100, help="Number of files to copy in each chunk")
parser.add_argument("--ssh_user", required=True, help="SSH user for the remote server")
parser.add_argument("--ssh_host", required=True, help="SSH host for the remote server")
parser.add_argument("--ssh_key", required=True, help="Path to the SSH private key for authentication")
args = parser.parse_args()

suffixes = ["fast5", "pod5", "fastq", "fastq.gz", "txt", "html", "pdf", "bam", "bam.bai", "csv", "json", "tsv", "md"]

def get_files(directory):
    """Get a list of files in the directory with specified suffixes."""
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            if len(files) >= args.chunk_size:
                return files
            if any(filename.endswith(f".{suffix}") for suffix in suffixes):
                files.append(os.path.relpath(os.path.join(root, filename), directory))
    return files

try:
    files = get_files(args.source_directory)
except Exception as e:
    sys.exit(f"Error reading source directory {args.source_directory}: {e}")

with tempfile.NamedTemporaryFile(prefix="nas_offload_", mode="w", delete=False) as f:
    for file in files:
        f.write(f"{file}\n")

filename = f.name

command = [
    "/usr/bin/rsync",
    "-v",
    "--perms",
    "--times",
    "--rsh", f"ssh -i {args.ssh_key} -o PasswordAuthentication=no",
    "--stats",
    "--log-file", os.path.join(args.logs_directory, f"{os.path.basename(filename)}.log"),
    "--files-from", filename,
    "--remove-source-files",
    args.source_directory,
    f"{args.ssh_user}@{args.ssh_host}:{args.destination_directory}",
]

subprocess.run(command, check=True)
