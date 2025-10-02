#!/bin/python3

import datetime
import os
import re
import shutil
import smtplib
import ssl
import subprocess
import sys
import tempfile
import yaml

LOGS_DIR = "/var/log/minknow"
LOG_FILE = "control_server_log-0.txt"
RSYNC = "/usr/bin/rsync"
STATE_FILE = "/var/local/minknow_error_email_state.yaml"
ERROR_TEXT = "stopping_protocol_due_to_device_error"

slots = []
errors = []

try:
    with open("/etc/email_minknow_errors.yaml") as fh:
        config = yaml.safe_load(fh)
except Exception as e:
    sys.exit("Failed to load config: %s" % e)

try:
    with open(STATE_FILE) as fh:
        state = yaml.safe_load(fh)
except:
    state = {}

working_dir = tempfile.mkdtemp(prefix="email_minknow_errors_")

log_list_file = os.path.join(working_dir, "log_list.txt")
with open(log_list_file, "w") as fh:
    for col in config["slots"]["cols"]:
        for row in config["slots"]["rows"]:
            slot = "%d%s" % (col, row)
            slots.append(slot)
            fh.write("%s/%s\n" % (slot, LOG_FILE))

for id, hostname in config["proms"].items():
    prom = "prom%d" % id
    prom_dir = os.path.join(working_dir, prom)
    os.mkdir(prom_dir)

    if prom not in state:
        state[prom] = {
            "last_check": 0,
        }

    subprocess.run([
        RSYNC,
        "-aHSX",
        "--files-from=%s" % log_list_file,
        "%s:%s/" % (prom, LOGS_DIR),
        "%s/" % prom_dir
    ])

    for slot in slots:
        slot_log = os.path.join(prom_dir, slot, LOG_FILE)
        if not os.path.exists(slot_log):
            continue

        if os.stat(slot_log).st_mtime <= state[prom]["last_check"]:
            continue

        with open(slot_log) as fh:
            for line in fh.readlines():
                if ERROR_TEXT in line:
                    try:
                        timestamp_str = re.match(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line).group(1)
                        timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    except:
                        continue

                    if timestamp.timestamp() <= state[prom]["last_check"]:
                        continue

                    error_message = "Error on %s position %s at %s" % (prom, slot, timestamp_str)
                    sys.stderr.write("%s\n" % error_message)
                    errors.append(error_message)

    state[prom]["last_check"] = int(datetime.datetime.now().timestamp())

shutil.rmtree(working_dir)

exit_code = 0

if len(errors) > 0:
    try:
        smtp = smtplib.SMTP(config["mail_host"], config["mail_port"])
        smtp.starttls(context=ssl.create_default_context())
        smtp.login(config["mail_username"], config["mail_password"])
        smtp.sendmail(config["mail_from"], config["mail_to"], "To: %s\nSubject: MinKNOW Device Errors\n\n%s" % (",".join(config["mail_to"]), "\n".join(errors)))
        smtp.quit()
    except Exception as e:
        sys.stderr.write("Failed sending message: %s\n" % e)
        exit_code = 1

if exit_code == 0:
    with open(STATE_FILE, "w") as fh:
        yaml.safe_dump(state, fh)

sys.exit(exit_code)
