#!/usr/bin/python3

import argparse
import collections
import datetime
import os
import re
import subprocess
import sys
import threading
import time
import yaml

# This was originally written using paramiko but I had trouble with
# getting SSH agent forwarding to work
def ssh_command(host, command):
    try:
        result = subprocess.run(["/usr/bin/ssh", "-A", "-o", "StrictHostKeyChecking=no", "-o", "PasswordAuthentication=no", "-l", args.src_user, host, command], capture_output=True, text=True, check=True)

    except Exception as e:
        sys.exit(f"Failed running SSH command {command} on {host}: {e}")

    return result

def thread_worker(src_host):
    global dd_done
    global results

    filename = f"speedtest_{datetime.datetime.now().timestamp()}_{os.getpid()}_{src_host}"
    src_file = f"{args.src_dir}/{filename}"
    dd_result = ssh_command(src_host, f"/usr/bin/dd if=/dev/urandom of={src_file} bs=1M count={args.file_size}")
    if f"\n{args.file_size * 1024 * 1024} bytes" not in dd_result.stderr:
        sys.exit(f"Unexpected output from dd: {dd_result.stderr}")

    dd_done[src_host] = True

    while len(dd_done) < len(args.src_host):
        time.sleep(0.1)

    start_time = datetime.datetime.now()
    rsync_result = ssh_command(src_host, f"/usr/bin/rsync -a --stats --remove-source-files {src_file} {args.dst_user}@{args.dst_host}:{args.dst_dir}")
    ssh_command(src_host, f"/usr/bin/lftp -e 'rm {args.dst_dir}/{filename}; exit' sftp://{args.dst_user}:NONE@{args.dst_host}")

    speed = None
    for line in rsync_result.stdout.splitlines():
        m = re.search(r" ([0-9,.]+) bytes/sec$", line)
        if m:
            speed = float(m.group(1).replace(",", ""))

    if not speed:
        sys.exit(f"Could not determine speed of rsync for {src_host}")

    result = {
        "duration": (datetime.datetime.now() - start_time).total_seconds(),
        "speed": speed,
    }
    results["stats"]["individual"][src_host] = result

parser = argparse.ArgumentParser()
parser.add_argument("--src_host", action="append", required=True, help="Re-use option for each source prom")
parser.add_argument("--src_user", default="prom", help="Login to prom devices as this user")
parser.add_argument("--src_dir", default="/data", help="Directory used as source for file copy")
parser.add_argument("--dst_host", required=True, help="Destination server address for all file copies")
parser.add_argument("--dst_user", required=True, help="Destination server username")
parser.add_argument("--dst_dir", required=True, help="Destination server directory")
parser.add_argument("--file_size", type=int, default=5120, help="Size of copied file (mebibytes)")
args = parser.parse_args()

src_hosts = collections.deque(args.src_host)

threads = []
dd_done = {}

results = {}
results["start_utc"] = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
results["config"] = {}
results["config"]["destination"] = {"host": args.dst_host, "dir": args.dst_dir}
results["config"]["file_size"] = args.file_size * 1024 * 1024
results["stats"] = {}
results["stats"]["individual"] = {}
results["stats"]["combined"] = {}

while src_hosts:
    src_host = src_hosts.pop()
    t = threading.Thread(target=thread_worker, kwargs={"src_host": src_host})
    threads.append(t)
    t.start()

    while len(threads) >= len(args.src_host):
        threads = [thread for thread in threads if thread.is_alive()]
        time.sleep(1)

for t in threads:
    t.join()

results["stats"]["combined"]["speed_total"] = 0
for dest_addr, dest_stats in results["stats"]["individual"].items():
    results["stats"]["combined"]["speed_total"] += dest_stats["speed"]
results["stats"]["combined"]["speed_average"] = results["stats"]["combined"]["speed_total"] / len(args.src_host)

print(yaml.dump(results, default_flow_style=False))
